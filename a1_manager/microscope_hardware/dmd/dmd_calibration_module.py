from __future__ import annotations # Enable type annotation to be stored as string
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
# Remove the java warnings
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import matplotlib.pyplot as plt
from cv2 import getAffineTransform
from skimage.draw import disk

from main import A1Manager
from utils.utils import image_to_rgb, save_img, load_config_file, draw_square_from_circle, bounding_box_nDim, get_centroid, threshold_img


@dataclass
class CalibrateFTurret:
    """
    Class to calibrate the fTurret by capturing images, processing masks, and computing
    transformation matrices between the DMD and camera coordinate systems.
    """
    savedir: Path
    fTurret: str # '5-Duo' or '4-Quad'
    img_savedir: Path = field(init=False)
    fTurret_profile: dict[str, Any] = field(init=False)
    dmd_points_list: list['DMD_Point'] = field(init=False)
    
    def __post_init__(self)-> None:
        turret_name = self.fTurret.split('-')[-1]
        self.img_savedir = self.savedir.joinpath(turret_name)
        self.img_savedir.mkdir(exist_ok=True)

        # Load existing DMD profile if available
        dmd_profile = load_config_file('dmd_profile')
        if dmd_profile is not None:
            self.fTurret_profile = dmd_profile[self.fTurret]
        
    def get_fTurret_profile(self, a1_manager: A1Manager)-> dict[str, Any]:
        # Take a snap image of the full dmd
        a1_manager.load_dmd_mask('fullON', transform_mask=False)
        dmd_fullON_img = a1_manager.snap_image()
        save_img(dmd_fullON_img, self.img_savedir, 'dmd_fullON_img')
        
        # Threshold the image
        mask = threshold_img(dmd_fullON_img)
        save_img(mask, self.img_savedir, 'dmd_fullON_mask')
        
        # Get boxed mask and its position. The slice corrdinate is (sliceY(start,end),sliceX(start,end))
        boxed_mask, box_coord = bounding_box_nDim(mask) 
        
        # Determine the correction to apply to the center of dmd window to match the center of the full camera image
        height_dmd, width_dmd = boxed_mask.shape[0]//2, boxed_mask.shape[1]//2
        center_offset = 2048 // 2
        y_corr = center_offset - height_dmd * a1_manager.camera.binning
        x_corr = center_offset - width_dmd * a1_manager.camera.binning
        
        # Create dmd_position dict
        self.fTurret_profile = {
            'window_size': boxed_mask.shape,
            'y_slice':[int(box_coord[0].start), int(box_coord[0].stop)],
            'x_slice':[int(box_coord[1].start), int(box_coord[1].stop)],
            'center_xy_corr_pix':[x_corr, y_corr] # save as x,y coord for nikon
            }
        return self.fTurret_profile
    
    def create_dmd_point_list(self, a1_manager: A1Manager, numb_points: int)-> None:
        """
        Generates a list of random DMD points within the specified window
        and creates corresponding DMDPoint instances.
        """
        window_size = self.fTurret_profile['window_size']
        window_start = (self.fTurret_profile['x_slice'][0], self.fTurret_profile['y_slice'][0])
        input_centroids = self.generate_random_points(window_size, window_start, numb_points)
        self.dmd_points_list = [
            DMD_Point(point, idx, a1_manager.image_size, self.img_savedir) 
            for idx, point in enumerate(input_centroids)
            ]
        
    def get_transformation_matrix(self, a1_manager: A1Manager)-> np.ndarray:
        """
        Computes an averaged affine transformation matrix using sets of three points.
        Each transform is computed using cv2.getAffineTransform between corresponding
        input centroids and mask centroids.
        """
        input_centroids = [dmd_point.point_centroid for dmd_point in self.dmd_points_list]
        mask_centroids = self.get_mask_centroids(a1_manager)
        # Convert y,x coord (numpy) to x,y coord (cv2)
        src_points = [(x, y) for [(y, x)] in mask_centroids]
        dst_points = [(x, y) for y, x in input_centroids]
        
        num_transforms = len(src_points) // 3
        avg_transform = np.zeros(shape=(2,3), dtype=np.float32)
        for i in range(num_transforms):
            # Get 3 points
            src_pts = np.float32(src_points[3*i:3*i+3])
            dst_pts = np.float32(dst_points[3*i:3*i+3])
            # Get transformation matrix
            avg_transform += getAffineTransform(src_pts,dst_pts)
        avg_transform /= num_transforms
        return avg_transform
    
    def test_transformation_matrix(self, a1_manager: A1Manager, transfo_matrix: dict=None)-> None:
        """
        Applies the transformation matrix to a generated full input mask, captures the transformed image, and displays the original vs. transformed mask side-by-side.
        """
        points_list = [dmd_point.point_centroid for dmd_point in self.dmd_points_list]
        full_mask = self.create_full_input_mask(a1_manager, points_list)
        save_img(full_mask, self.img_savedir, 'full_mask.tif')
        
        # Affine transform the mask
        transformed_mask = a1_manager.dmd.dmd_mask.apply_affine_transform(full_mask, transfo_matrix)
        save_img(transformed_mask, self.img_savedir, 'full_mask_transformed.tif')
        
        # Project mask on the dmd with transformation matrix
        a1_manager.load_dmd_mask(transformed_mask, transform_mask=False)
        transformed_mask_img = a1_manager.snap_image()
        save_img(transformed_mask_img, self.img_savedir, 'full_mask_img')

        # Display the original and transformed masks
        stack = np.stack([full_mask, transformed_mask_img]).astype('uint16')
        stack_rgb = image_to_rgb(stack, channels=[1,2])
        plt.imshow(stack_rgb)
        plt.show()
        
    @staticmethod
    def generate_random_points(window_size: tuple[int, int], window_start: tuple[int, int], numb_points: int)-> list[tuple[int, int]]:
        """
        Generates random (y, x) points within a specified rectangular area.
        Requires numb_points to be a multiple of 3.
        """
        if numb_points%3!=0:
            raise ValueError(f"numb_points must be a multiple of 3, currently {numb_points}")
        
        # Define boundaries
        dmd_height, dmd_width = window_size
        minX, maxX = 40, dmd_width - 39
        minY, maxY = 40, dmd_height - 39
        
        # Coordinate correction, to rezise to original image
        start_x, start_y = window_start
        
        # Generate points
        count = 0
        x_points = []; y_points = []
        while count < numb_points:
            x = start_x + np.random.randint(minX, maxX)
            y = start_y + np.random.randint(minY, maxY)
            if x not in x_points and y not in y_points:
                x_points.append(x); y_points.append(y)
                count+=1
        return [(y,x) for y, x in zip(y_points, x_points)]

    @staticmethod
    def create_full_input_mask(a1_manager: A1Manager, points_list: list[tuple[int, int]])-> np.ndarray:
        """
        Creates a full input mask by drawing squares (of random sizes)
        centered at each point from the list.
        """
        mask = np.zeros(shape=a1_manager.image_size, dtype=np.uint16)
        for point in points_list:
            radius = np.random.randint(15, 38)
            _,box_coord = draw_square_from_circle(point, radius, a1_manager.image_size)
            mask[box_coord] = 1
        return mask
    
    def get_mask_centroids(self, a1_manager: A1Manager)-> list[tuple[int, int]]:
        """
        Processes each DMDPoint to obtain the corresponding mask centroid.
        """
        centroid_list = []
        for dmd_point in self.dmd_points_list:
            # Create mask
            dmd_point.create_mask_from_coordinate()
            # Get image of mask trhough DMD without transformation
            mask_img = dmd_point.get_img_of_mask(a1_manager)
            # Get segmentation of mask img
            thresholded_mask = dmd_point.threshold_img_point(mask_img).astype('int')
            centroid_list.append(dmd_point.get_centroid_point(thresholded_mask))
        return centroid_list

@dataclass
class DMD_Point:
    """
    Represents a point on the DMD with methods to generate its corresponding
    mask, capture the mask image through the DMD, and compute the centroid.
    """
    point_centroid: tuple[int, int] # (y,x) numpy
    instance: int
    image_size: tuple[int, int]
    savedir: Path
    mask_path: Path = field(init=False)
    mask_img_path: Path = field(init=False)
    mask_img_mask_path: Path = field(init=False)
    mask_centroid: tuple[int, int] = field(init=False)
    
    def create_mask_from_coordinate(self)-> None:
        """
        Creates a binary mask with a disk (radius=10) drawn at the point centroid
        and saves the mask image.
        """
        mask = np.zeros(shape=self.image_size, dtype=np.uint8)
        rr, cc = disk(self.point_centroid, radius=10, shape=self.image_size)
        mask[rr, cc] = 1
        self.mask_path = self.save_point_image(mask, "mask")
    
    def save_point_image(self, img: np.ndarray, img_name: str)-> Path:
        """Saves the provided image to disk and returns the file path."""
        return save_img(img,self.savedir, f'{img_name}_{self.instance}')
    
    def get_img_of_mask(self, a1_manager: A1Manager)-> np.ndarray:
        """
        Loads the point mask onto the DMD, captures the resulting image,
        saves it, and returns the image.
        """
        a1_manager.load_dmd_mask(self.mask_path, transform_mask=False)
        mask_img = a1_manager.snap_image()
        self.mask_img_path = self.save_point_image(mask_img,'mask_img')
        return mask_img
    
    def threshold_img_point(self, img: np.ndarray)-> np.ndarray:
        """Thresholds the given image, saves the thresholded image, and returns it."""
        mask = threshold_img(img)
        self.mask_img_mask_path = self.save_point_image(mask,'mask_img_mask')
        return mask
    
    def get_centroid_point(self, mask: np.ndarray)-> tuple[int, int]:
        """Calculates the centroid of the provided mask, stores it, and returns the value."""
        self.mask_centroid = get_centroid(mask)
        return self.mask_centroid
