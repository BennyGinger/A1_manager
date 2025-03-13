# from concurrent.futures import ThreadPoolExecutor
# from functools import partial, wraps
from pathlib import Path
# from time import time
# from typing import Callable, Iterable
# import os
# from os.path import join
# from os import listdir, getcwd, remove
from datetime import datetime, timedelta
import json

import numpy as np
import tifffile as tiff
# from tifffile import imwrite
# TODO: Remove bg_sub
# from smo import SMO
from skimage.draw import disk
# from skimage.transform import resize
from itertools import combinations
import cv2
from skimage.measure import regionprops


# def is_run_from_ipython()-> bool:
#     """Check if the pipeline is run in a notebook or not"""
#     from IPython import get_ipython
#     return get_ipython() is not None

# if is_run_from_ipython():
#     from tqdm.notebook import tqdm
# else:
#     from tqdm import tqdm


# def progress_bar(*args,**kwargs)-> Callable:
#     """Progress bar function from the tqdm library. Either the notebook or the terminal version is used. See tqdm documentation for more information.
    
#     Main Args:
#         iterable: iterable object
#         desc: str, description of the progress bar
#         colour: str, colour of the progress bar
#         total: int, total number of iterations, used in multiprocessing"""
#     return tqdm(*args,**kwargs)


def save_img(img: np.ndarray, savedir: Path, img_name: str)-> Path:
    img_path = savedir.joinpath(f"{img_name}.tif")
    tiff.imwrite(img_path, data=img.astype('uint16'))
    return img_path

# def create_savedir(parent_path: str, folder_name: str)-> Path:
#     """Create a folder in the parent_path with the folder_name. If the folder already exists, it will be emptied."""
#     parent_path: Path = Path(parent_path)
#     dir_path = parent_path.joinpath(folder_name)
#     dir_path.mkdir(exist_ok=True)
#     # If not empty remove all files in folder
#     if any(dir_path.iterdir()): 
#         rm_all_files_from_dir(dir_path)
#     return dir_path

def create_date_savedir(parent_path: Path, folder_name: str=None)-> Path:
    """Create a folder with the actual date in the parent_path. If a folder_name is given, it will be added to the date."""
    # Create folder with actual date
    now = datetime.now()
    folder_name = f'_{folder_name}' if folder_name else ''
    new_folder_name = f'{now.year}{now.month:02d}{now.day:02d}{folder_name}'
    savedir = parent_path.joinpath(new_folder_name)
    savedir.mkdir(exist_ok=True)
    return savedir

def find_project_root(current_path: Path) -> Path:
    """
    Recursively search for the project root directory by looking for the .git directory.
    """
    for parent in current_path.parents:
        if parent.joinpath(".git").exists():
            return parent
    raise FileNotFoundError("Project root with .git directory not found.")

def load_config_file(file_name_key: str)-> dict | None:
    project_path = find_project_root(Path(__file__).resolve())
    config_path = project_path.joinpath('config')
    found_file = None
    for file in config_path.iterdir():
        if file.match(f"*{file_name_key}*"):
            found_file = file
    
    if found_file is None:
        print(f"No {file_name_key} found.")
        return None
    
    return load_file(found_file)

def load_file(file_path: Path)-> dict | None:
    if not file_path.exists():
        print(f"No file found at {file_path}")
        return None
    
    with open(file_path) as json_file:
        loaded_file: dict = json.load(json_file)
    return loaded_file

def save_file(file_name_key: str, data: dict)-> None:
    parent_path = Path(__file__).resolve().parent.parent
    config_path = parent_path.joinpath('config')
    save_name = f"{file_name_key}.json"
    save_path = config_path.joinpath(save_name)
    with open(save_path, "w") as outfile:
        json.dump(data, outfile)

# def check_file_date(file_name: str)-> None:
#     if file_name.endswith('.npy'):
#         log_message = "WARNING: The transformation matrix is older than 6 months. Please recalibrate the DMD."
#         numb_days = 183
#     elif file_name.endswith('.json'):
#         log_message = "WARNING: The dish calibration is older than a month. Please recalibrate the dish."
#         numb_days = 30
    
#     try:
#         file_date = datetime.strptime(file_name.split('_')[0],'%Y%m%d')
#     except ValueError:
#         return None
#     threshold_date = datetime.now() - timedelta(days=numb_days)
#     if file_date < threshold_date:
#         print(log_message)

# def rm_specific_file(file_type: str, key_file_name: str='')-> None:
#     parent_path = getcwd()
#     pattern = f"{key_file_name}{file_type}"
#     for file in listdir(parent_path):
#         if file.__contains__(pattern):
#             remove(join(parent_path,file))
#             print(f"Removed old {key_file_name} {file}")

# def rm_all_files_from_dir(path: Path)-> None:
#     for file in path.iterdir():
#         os.remove(file)

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
    mask = np.zeros(shape=mask_size)
    rr,cc = disk(point,radius=radius,shape=mask_size)
    mask[rr,cc] = 1
    return bounding_box_nDim(mask)

def get_centroid(image: np.ndarray) -> list:
    properties = regionprops(image)
    centroids = [prop.centroid for prop in properties]
    return centroids

# def apply_background_correction(img: np.ndarray)-> np.ndarray:
#     # Initialise SMO
#     smo = SMO(shape=img.shape,sigma=0,size=7)
#     # Do background correction
#     bgimg = smo.bg_corrected(img)
#     bgimg[bgimg<0] = 0
#     return bgimg

def threshold_img(img: np.ndarray)-> np.ndarray:
    _, mask = cv2.threshold(img,0,img.max(), cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return mask.astype(bool)

# def correct_z_outliers(z_data: list)-> float:
#     # Compute IQR
#     q3,q1 = np.percentile(z_data,[75,25])
#     iqr = q3-q1
#     # Compute upper and lower bound
#     upper_bound = q3 + 1.5*iqr
#     lower_bound = q1 - 1.5*iqr
#     # Remove outliers
#     z_data_clean = [z for z in z_data if between(z,lower_bound,upper_bound)]
#     # Compute mean
#     return np.mean(z_data_clean)
    
# def timer(func):
#     """Decorator to measure the execution time of a function."""
#     @wraps(func)
#     def wrapper_timer(*args, **kwargs):
#         start_time = time()  # Start time
#         value = func(*args, **kwargs)  # Call the decorated function
#         end_time = time()  # End time
#         run_time = end_time - start_time  # Calculate execution time
#         print(f"Finished {func.__name__!r} in {run_time:.4f} secs")
#         return value
#     return wrapper_timer

# def run_multithread(method_name: str, input_data: Iterable, desc: str="", **kwargs)-> list:
#     """Run a function in multi-threading. It uses a lock to limit access of some functions to the different threads."""
#     # Run callable in threads
#     outputs = []
#     with ThreadPoolExecutor() as executor:
#         with progress_bar(total=len(input_data),
#                           desc=desc) as pbar:
#             # Run function
#             futures = [executor.submit(partial(getattr(obj, method_name), **kwargs)) for obj in input_data]
#             # Update the pbar and get outputs
#             for future in futures:
#                 pbar.update()
#                 outputs.append(future.result())
#     return outputs  

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