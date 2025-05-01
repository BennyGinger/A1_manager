from __future__ import annotations # Enable type annotation to be stored as string

from pycromanager import Core

from a1_manager.utils.utility_classes import StageCoord


class NikonTi2:
    """Class to control the A1_dmd through pycromanager."""
    __slots__ = 'core','objective','focus_device'
    
    def __init__(self, core: Core, objective: str, focus_device: str='ZDrive') -> None:
        self.core = core
        self._select_objective(objective)
        self.focus_device = focus_device
        # Set focus device
        self.select_focus_device(focus_device)
        
    def select_focus_device(self, focus_device: str='ZDrive')-> None: # ZDrive, PFSOffset, MarZ
        """
        Select the focus device to use.
        Possible options:
        - ZDrive
        - PFSOffset
        - MarZ
        
        Default is ZDrive.
        """
        self.core.set_property('Core','Focus',focus_device)
        if focus_device == 'PFSOffset':
            self.core.set_property('PFS','FocusMaintenance','On')
        else:
            self.core.set_property('PFS','FocusMaintenance','Off')
    
    def get_stage_position(self)-> StageCoord:
        """Get the current stage position in XY coordinates and the focus device position."""
        return StageCoord(
            xy=(self.core.get_x_position(),self.core.get_y_position()),
            ZDrive=self.core.get_position('ZDrive'),
            PFSOffset=self.core.get_position('PFSOffset')
        )
    
    def set_stage_position(self, stage_position: StageCoord)-> None:
        """Set the stage position in XY coordinates and the focus device position."""
        self.core.set_xy_position(*stage_position.xy)
        if stage_position[self.focus_device] is not None:
            self.core.set_position(self.focus_device, stage_position[self.focus_device])
    
    def _select_objective(self, objective: str)-> None:
        """Select the objective to use. Expected objective string: '[number]x' e.g. 10x, 20x."""
        Objectifdefault = {'10x':1, '20x':2}
        self.objective = objective
        if not isinstance(self.objective, str):
            raise TypeError("Objective must be a string: 10x, 20x...")
        if objective not in Objectifdefault.keys():
            raise ValueError(f"{self.objective} is not yet calibrated. Please use 10x or 20x")
        self.core.set_property('Nosepiece', 'State', Objectifdefault[self.objective])

    def set_light_path(self, light_path: int)-> None:
        """Change Light path: 0=EYE, 1=R, 2=AUX and 3=L"""
        self.core.set_property('LightPath','State',light_path)
