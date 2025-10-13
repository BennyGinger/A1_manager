from __future__ import annotations # Enable type annotation to be stored as string
from pathlib import Path
from datetime import datetime
from typing import TypeVar
from itertools import combinations
import logging

from numpy.typing import NDArray
import numpy as np
import tifffile as tiff
from skimage.draw import disk
import cv2
from skimage.measure import regionprops


T = TypeVar('T', bound=np.generic)

# Setup logging
logger = logging.getLogger(__name__)


def save_tif(img: NDArray[T], savedir: Path, img_name: str) -> Path:
    """
    Save a numpy array as a tiff file. The savedir is the folder where the file will be saved.
    """
    img_path = savedir.joinpath(f"{img_name}.tif")
    tiff.imwrite(img_path, data=img.astype('uint16'))
    return img_path

def create_date_savedir(parent_path: Path, folder_name: str | None = None)-> Path:
    """
    Create a folder with the actual date in the parent_path. If a folder_name is given, it will be added to the date.
    """
    # Create folder with actual date
    now = datetime.now()
    folder_name = f'_{folder_name}' if folder_name else ''
    new_folder_name = f'{now.year}{now.month:02d}{now.day:02d}{folder_name}'
    savedir = parent_path.joinpath(new_folder_name)
    savedir.mkdir(exist_ok=True)
    return savedir

def bounding_box_nDim(mask: NDArray[T]) -> tuple[NDArray[T], tuple[slice]]:
    """This function take a np.array (any dimension) and create a bounding box around the nonzero shape.
    Also return a slice object to be able to reconstruct to the originnal shape"""
    
    # Determine the number of dimensions
    N = mask.ndim
    
    # Go trhough all the axes to get min and max coord val
    slice_list = []
    for ax in combinations(reversed(range(N)), N - 1):
        nonzero = np.any(mask, axis=ax)
        vmin, vmax = np.where(nonzero)[0][[0, -1]]
        # Store these coord as slice obj
        slice_list.append(slice(vmin,vmax+1))
    
    s = tuple(slice_list)
    
    return (mask[s], s)

def draw_square_from_circle(point: tuple, radius: int, mask_size: tuple)-> tuple:
    """Draw a square around a circle with a given radius and center point."""
    
    mask = np.zeros(shape=mask_size)
    rr,cc = disk(point,radius=radius,shape=mask_size)
    mask[rr,cc] = 1
    return bounding_box_nDim(mask)

def get_centroid(image: NDArray[T]) -> list:
    """Get the centroid of a binary image."""
    
    properties = regionprops(image)
    centroids = [prop.centroid for prop in properties]
    return centroids

def threshold_img(img: NDArray[T]) -> NDArray[T]:
    """Threshold an image using Otsu's method."""

    img_uint8 = img.astype(np.uint8)
    _, mask = cv2.threshold(img_uint8, 0, img_uint8.max(), cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return mask.astype(bool)

def image_to_rgb(img0: NDArray[np.generic], channels: list[int] = [0, 0]) -> NDArray[np.uint8]:
    """
    Copied from cellpose. image is 2 x Ly x Lx or Ly x Lx x 2 - change to RGB Ly x Lx x 3
    Pylance warning suppression: add type hints, runtime checks, and comments.
    """
    img = img0.copy().astype(np.float32)
    # Ensure 3D array
    if img.ndim < 3:
        img = img[:, :, np.newaxis]
    # If first dim is likely channel, transpose to (Ly, Lx, n_channels)
    if img.shape[0] < 5:
        img = np.transpose(img, (1, 2, 0))
    # If channels[0] is 0, average across last axis
    if channels[0] == 0:
        img = img.mean(axis=-1)[:, :, np.newaxis]
    # Normalize each channel
    for i in range(img.shape[-1]):
        if np.ptp(img[:, :, i]) > 0:
            normed = _normalize99(img[:, :, i])
            img[:, :, i] = np.clip(normed, 0, 1)
            img[:, :, i] = np.clip(img[:, :, i], 0, 1)
    img *= 255
    img = np.uint8(img)  # type: ignore
    # Prepare output array
    assert img.ndim == 3, f"img should be 3D, got shape {img.shape}"
    h, w, c = img.shape  # type: ignore
    rgb_img: NDArray[np.uint8] = np.zeros((h, w, 3), np.uint8)
    if c == 1:
        # Single channel, tile to RGB and cast to uint8
        rgb_img = np.tile(img, (1, 1, 3)).astype(np.uint8)  # type: ignore
    else:
        # Defensive: ensure channel indices are valid
        if 0 <= channels[0] - 1 < c:
            rgb_img[:, :, channels[0] - 1] = img[:, :, 0]  # type: ignore
        if channels[1] > 0 and 0 <= channels[1] - 1 < c:
            rgb_img[:, :, channels[1] - 1] = img[:, :, 1]  # type: ignore
    return rgb_img

def _normalize99(raw_img: np.ndarray, lower: int=1, upper: int=99)-> np.ndarray:
    """ Copied from cellpose. normalize image so 0.0 is 1st percentile and 1.0 is 99th percentile """
    
    norm_img = raw_img.copy()
    x01 = np.percentile(norm_img, lower)
    x99 = np.percentile(norm_img, upper)
    norm_img = (norm_img - x01) / (x99 - x01)
    return norm_img