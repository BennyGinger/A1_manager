from __future__ import annotations # Enable type annotation to be stored as string
from pathlib import Path
from datetime import datetime
import json
from itertools import combinations
import logging

import numpy as np
import tifffile as tiff
from skimage.draw import disk
import cv2
from skimage.measure import regionprops

from a1_manager import CONFIG_DIR
from .json_utils import decode_dataclass, encode_dataclass


def save_tif(img: np.ndarray, savedir: Path, img_name: str)-> Path:
    """
    Save a numpy array as a tiff file. The savedir is the folder where the file will be saved.
    """
    img_path = savedir.joinpath(f"{img_name}.tif")
    tiff.imwrite(img_path, data=img.astype('uint16'))
    return img_path

def create_date_savedir(parent_path: Path, folder_name: str=None)-> Path:
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

def load_config_file(file_name_key: str)-> dict | None:
    """
    Load a json file from the config folder. Use the decode_dataclass function to decode the dataclass if needed.
    """
    
    config_path = CONFIG_DIR
    found_file = None
    for file in config_path.iterdir():
        if file.match(f"*{file_name_key}*"):
            found_file = file
    
    if found_file is None:
        logging.warning(f"No {file_name_key} found.")
        return None
    
    return load_json(found_file)

def load_json(file_path: Path)-> dict | None:
    """
    Load a json file. Use the decode_dataclass function to decode the dataclass if needed.
    """
    
    if not file_path.exists():
        logging.error(f"No file found at {file_path}")
        return None
    
    with open(file_path) as json_file:
        loaded_file: dict = json.load(json_file, object_hook=decode_dataclass)
    return loaded_file

def save_config_file(file_name_key: str, data: dict)-> None:
    """Save a dictionary to a json file in the config folder."""
    
    config_path = CONFIG_DIR
    save_name = f"{file_name_key}.json"
    save_path = config_path.joinpath(save_name)
    save_json(save_path, data)

def save_json(file_path: Path, data: dict)-> None:
    """
    Save a dictionary to a json file.
    """
    with open(file_path, "w") as outfile:
        json.dump(data, outfile, default=encode_dataclass, indent=4)

def bounding_box_nDim(mask: np.ndarray)-> tuple[np.ndarray, tuple[slice]]:
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

def get_centroid(image: np.ndarray) -> list:
    """Get the centroid of a binary image."""
    
    properties = regionprops(image)
    centroids = [prop.centroid for prop in properties]
    return centroids

def threshold_img(img: np.ndarray)-> np.ndarray:
    """Threshold an image using Otsu's method."""
    
    _, mask = cv2.threshold(img,0,img.max(), cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return mask.astype(bool)

def image_to_rgb(img0: np.ndarray, channels: list[int]=[0,0])-> np.ndarray:
    """ Copied from cellpose. image is 2 x Ly x Lx or Ly x Lx x 2 - change to RGB Ly x Lx x 3 """
    
    img = img0.copy()
    img = img.astype(np.float32)
    if img.ndim<3:
        img = img[:,:,np.newaxis]
    if img.shape[0]<5:
        img = np.transpose(img, (1,2,0))
    if channels[0]==0:
        img = img.mean(axis=-1)[:,:,np.newaxis]
    for i in range(img.shape[-1]):
        if np.ptp(img[:,:,i])>0:
            img[:,:,i] = np.clip(_normalize99(img[:,:,i]), 0, 1)
            img[:,:,i] = np.clip(img[:,:,i], 0, 1)
    img *= 255
    img = np.uint8(img)
    rgb_img = np.zeros((img.shape[0], img.shape[1], 3), np.uint8)
    if img.shape[-1]==1:
        rgb_img = np.tile(img,(1,1,3))
    else:
        rgb_img[:,:,channels[0]-1] = img[:,:,0]
        if channels[1] > 0:
            rgb_img[:,:,channels[1]-1] = img[:,:,1]
    return rgb_img

def _normalize99(raw_img: np.ndarray, lower: int=1, upper: int=99)-> np.ndarray:
    """ Copied from cellpose. normalize image so 0.0 is 1st percentile and 1.0 is 99th percentile """
    
    norm_img = raw_img.copy()
    x01 = np.percentile(norm_img, lower)
    x99 = np.percentile(norm_img, upper)
    norm_img = (norm_img - x01) / (x99 - x01)
    return norm_img