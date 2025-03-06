
# TODO: incorporate this into the dish_grid class
def size_pixel2micron(self, size_in_pixel: int=None)-> tuple:
    pixel_calibration = {'10x':0.6461,'20x':0.3258}
    objective = self.nikon.objective
    binning = self.camera.binning
    pixel_in_um = pixel_calibration[objective]
    if size_in_pixel:
        return size_in_pixel*pixel_in_um*binning
    image_size = self.camera.image_size
    return image_size[0]*pixel_in_um*binning