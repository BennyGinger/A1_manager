import pytest
import numpy as np
import logging
from pathlib import Path

# Import the class to be tested from main.py
from a1_manager.main import A1Manager

# BUG: The test file is not importing the A1Manager class correctly. Some problems with resolving the project root path.

# Dummy classes for simulating the hardware components
class DummyCore:
    def __init__(self):
        self.properties = {}
    def set_property(self, device, property_name, value):
        self.properties[(device, property_name)] = value
    def get_property(self, device, property_name):
        # Simulate specific queries:
        if device == 'PFS' and property_name == 'PFS Status':
            return '0000001100001010'
        if device == 'Mosaic3' and property_name == 'TriggerMode':
            return 'InternalExpose'
        if device == 'Core' and property_name == 'Focus':
            return 'ZDrive'
        return self.properties.get((device, property_name), "dummy")
    def snap_image(self):
        # Dummy: do nothing
        pass
    def get_tagged_image(self):
        # Create a dummy image (100x100) as a 1D array and appropriate tags.
        class DummyTaggedImage:
            def __init__(self):
                self.pix = np.zeros(100 * 100, dtype=np.uint16)
                self.tags = {"Height": 100, "Width": 100}
        return DummyTaggedImage()
    def display_slm_image(self, slm_name):
        # Dummy implementation for DMD display
        pass

class DummyNikon:
    def __init__(self, core, objective, focus_device):
        self.core = core
        self.objective = objective
        self.focus_device = focus_device
    def set_light_path(self, state):
        self.core.set_property('LightPath', 'State', state)
    def set_stage_position(self, stage_coord):
        self.core.set_property('Stage', 'Position', stage_coord)
    def get_stage_position(self):
        # Return a dummy stage position as a dictionary
        return {'xy': (100, 200), 'ZDrive': 10, 'PFSOffset': 5}

class DummyCamera:
    def __init__(self, core, binning, exposure_ms):
        self.core = core
        self.binning = binning
        self.exposure_ms = exposure_ms
    def set_camera_binning(self, binning):
        self.binning = binning
    def set_camera_exposure(self, exposure_ms):
        self.exposure_ms = exposure_ms

class DummyLamp:
    def __init__(self, core, lamp_name):
        self.core = core
        self.lamp_name = lamp_name
        self.lapp_main_branch = 0
    def preset_channel(self, oc, intensity):
        # Set dummy settings in Core
        self.core.set_property(self.lamp_name, 'PresetChannel', f"{oc.get('led', '')}:{intensity}")
    def set_LED_shutter(self, state):
        self.core.set_property(self.lamp_name, 'Global State', state)

class DummyDMD:
    def __init__(self, core, dmd_trigger_mode):
        self.core = core
        self.dmd_trigger_mode = dmd_trigger_mode
        # Dummy DMD mask with fixed size (e.g. 50x50)
        self.dmd_mask = type('DummyDMDMask', (), {"dmd_size": (50, 50)})()
    def set_dmd_exposure(self, exposure_sec):
        self.core.set_property('Mosaic3', 'ExposureTime', exposure_sec)
    def activate(self):
        self.core.display_slm_image('Mosaic3')
    def load_dmd_mask(self, input_mask, transform_mask):
        # Return a dummy numpy array
        return np.ones((50, 50), dtype='uint8')

# Dummy functions to replace the original implementations

def dummy_get_lamp(core, lamp_name):
    return DummyLamp(core, lamp_name)

def dummy_DMD(core, dmd_trigger_mode):
    return DummyDMD(core, dmd_trigger_mode)

# Pytest fixture for a dummy core object
@pytest.fixture
def dummy_core():
    return DummyCore()

# Pytest fixture for an A1Manager where the hardware components were replaced by dummy classes.
@pytest.fixture
def dummy_a1_manager(monkeypatch, dummy_core):
    # Replace in the dependencies of A1Manager:
    from a1_manager.microscope_hardware import nikon, cameras, dmd_manager, lamps_factory
    monkeypatch.setattr(nikon, "NikonTi2", DummyNikon)
    monkeypatch.setattr(cameras, "AndorCamera", DummyCamera)
    monkeypatch.setattr(lamps_factory, "get_lamp", dummy_get_lamp)
    monkeypatch.setattr(dmd_manager, "DMD", dummy_DMD)
    
    # Override the load_config_file function in utils so that it returns a dummy configuration dict.
    from a1_manager.utils import utils
    monkeypatch.setattr(utils, "load_config_file", lambda key: {"exposure_ms": 150, "led": "dummy_led"})
    
    # Create the A1Manager
    manager = A1Manager(objective="10x", exposure_ms=150, binning=2, lamp_name="pE-800",
                        focus_device="ZDrive", dmd_trigger_mode="InternalExpose")
    # Overwrite the core attribute with our dummy core
    manager.core = dummy_core
    return manager

def test_a1manager_initialization(dummy_a1_manager):
    manager = dummy_a1_manager
    # Test whether the Nikon lens has been initialized correctly
    assert manager.nikon.objective == "10x"
    # Prüfe, ob die Kamera den korrekten Expositionswert besitzt
    assert manager.camera.exposure_ms == 150
    # Check if the camera has the correct exposure value
    manager.lamp.preset_channel({"led": "dummy_led"}, 50)
    preset = manager.core.properties.get((manager.lamp.lamp_name, 'PresetChannel'))
    assert preset == "dummy_led:50"
    # Check if the DMD attribute is set if DMD is connected
    if manager.is_dmd_attached:
        assert manager.dmd is not None

def test_oc_settings(dummy_a1_manager):
    manager = dummy_a1_manager
    # Call oc_settings
    manager.oc_settings(optical_configuration="test", intensity=75)
    # Check if the lamp command (preset_channel) has been set
    preset = manager.core.properties.get((manager.lamp.lamp_name, 'PresetChannel'))
    assert preset is not None
    # Check if the camera exposure has been updated; see our dummy function in load_config_file returns exposure_ms 150.
    assert manager.camera.exposure_ms == 150

def test_snap_image(dummy_a1_manager):
    manager = dummy_a1_manager
    img = manager.snap_image(dmd_exposure_sec=5)
    # Verify that a NumPy array is returned
    assert isinstance(img, np.ndarray)
    # Test the data type
    assert img.dtype == np.uint16
    # Test the image size; according to DummyTaggedImage it should be 100x100.
    assert img.shape == (100, 100)

def test_window_size(dummy_a1_manager):
    manager = dummy_a1_manager
    # Test the window_size() method for the case "dmd_window_only" True
    size_true = manager.window_size(dmd_window_only=True)
    # Since DummyDMD.dmd_mask.dmd_size = (50, 50), and size_pixel2micron multiplied by (2) from DummyCalib:
    # We expect: size_true = (manager.size_pixel2micron(50), manager.size_pixel2micron(50))
    expected_value = manager.size_pixel2micron(50)
    assert size_true == (expected_value, expected_value)
    # Test the case when dmd_window_only is False.
    size_false = manager.window_size(dmd_window_only=False)
    # size_false is calculated from manager.image_size (which is calculated by DummyCamera) and size_pixel2micron.
    expected_value_image = manager.size_pixel2micron(manager.image_size[0])
    assert size_false == (expected_value_image, expected_value_image)

def test_light_stimulate(dummy_a1_manager, monkeypatch):
    manager = dummy_a1_manager
    # Capture LED shutter calls by replacing the set_LED_shutter method
    shutter_calls = []
    def dummy_set_LED_shutter(state):
        shutter_calls.append(state)
        manager.core.set_property(manager.lamp.lamp_name, 'Global State', state)
    monkeypatch.setattr(manager.lamp, "set_LED_shutter", dummy_set_LED_shutter)
    # Test light_stimulate with short duration (1 second)
    manager.light_stimulate(duration_sec=1)
    # Check that the shutter is first set to 1 and then to 0
    assert shutter_calls == [1, 0]
