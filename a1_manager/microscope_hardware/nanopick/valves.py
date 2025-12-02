from __future__ import annotations # Enable type annotation to be stored as string
import logging
import serial
import time


#from a1_manager.microscope_hardware.nanopick.marZ_api import MarZ
import a1_manager
from a1_manager.microscope_hardware.nanopick.masterclass import InjectionManager

# Set up logging
logger = logging.getLogger(__name__)

VALVE_2_TIME = 1000 # ms 
# Mapping of volume (ul) relationship to time (ms) as y = ax + b, with key as "needleSize_pressure" and value as (a, b)
VOL_TIME_MAP = {"30_0.35": (0.0012, 0.0338)}

class PICController(InjectionManager):
    def __init__(self, needle_size: int, pressure: float, port: str = "COM10"):
        """
        Initialize the PIC Controller connection.
        :param needle_size: Needle size in microns (e.g., 30)
        :param pressure: Pressure in bar (e.g., 0.35)
        :param port: COM port name (e.g., 'COM3')
        """
        self.ser = serial.Serial(
            port=port, 
            baudrate=9600, 
            timeout=1.0,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )
        time.sleep(2)  # wait for the serial connection to initialize
        self._clear_buffers()
        
        self._map_converter = f"{needle_size}_{pressure}"
        
        # initialize valve 2 time
        self.set_valve_time(2, VALVE_2_TIME)

    def _clear_buffers(self):
        """Clear input and output buffers."""
        self.ser.reset_input_buffer()
        time.sleep(0.1)
    
    def _send_command(self, command: str, inter_char_delay: float = 0.001, wait_for_reply: bool = True) -> str:
        """
        Send a command string with optional inter-character delay.
        :param command: Command string (without CR)
        :param inter_char_delay: Delay between characters in seconds
        :return: Response from the controller
        """
        self._clear_buffers()
        
        # Send command character by character for multi-character commands
        if len(command) > 1:
            logger.debug(f"Sending multi-char command '{command}' with delay {inter_char_delay}s")
            for char in command:
                self.ser.write(char.encode('ascii'))
                self.ser.flush()
                time.sleep(inter_char_delay)
            # Send terminator
            self.ser.write(b'\r')
            self.ser.flush()
        else:
            # Single character commands - send normally
            full_cmd = (command + '\r').encode('ascii')
            logger.debug(f"Sending single-char command: {full_cmd}")
            self.ser.write(full_cmd)
            self.ser.flush()
        
        # Return early if no reply expected
        if not wait_for_reply:
            logger.debug("Command sent (no reply expected)")
            return ""
        
        # Wait for response
        time.sleep(0.05)  # Small delay to let the PIC process
        
        # Read response
        response = ""
        start_time = time.time()
        timeout = self.ser.timeout if self.ser.timeout is not None else 1.0
        while time.time() - start_time < timeout:
            if self.ser.in_waiting > 0:
                char = self.ser.read(1)
                if char:
                    try:
                        decoded_char = char.decode('ascii')
                        if decoded_char in ['\r', '\n']:
                            break
                        response += decoded_char
                    except UnicodeDecodeError:
                        logger.error(f"Decode error for byte: {char.hex()}")
                        break
            else:
                time.sleep(0.001)  # Small delay to prevent busy waiting

        logger.debug(f"Response: '{response}'")
        return response

    def set_led_ring(self, ring: int = 0, brightness: int | None = None):
        """Toggle LED rings."""
        if ring == 0:
            self._send_command('s1-', wait_for_reply=False)
            return self._send_command('s5-', wait_for_reply=False)
        if ring == 1:
            self._send_command('s1-', wait_for_reply=False)
            return self._send_command('s5+', wait_for_reply=False)
        if ring == 2:
            self._send_command('s1+', wait_for_reply=False)
            return self._send_command('s5+', wait_for_reply=False)

    def set_valve_time(self, valve: int, duration: int):
        """
        Set the valve open duration.
        Valve 1 → 'i', Valve 2 → 'j'
        :param valve: Valve number (1 or 2)
        :param duration: Duration in milliseconds
        :param wait_for_reply: Whether to wait for a response
        """
        if valve == 1:
            cmd = f'i{duration}'
        elif valve == 2:
            cmd = f'j{duration}'
        else:
            raise ValueError("Valve must be 1 or 2")
        return self._send_command(cmd)

    def set_delay(self, delay: int):
        """Set delay between valve openings with 'k' command."""
        return self._send_command(f'k{delay}')

    def open_valves_sequence(self, mode: str):
        """
        Open valves in sequence with delay.
        'K' = Valve1 then Valve2
        'L' = Valve2 then Valve1
        """
        if mode not in ['K', 'L']:
            raise ValueError("Mode must be 'K' or 'L'")
        return self._send_command(mode)

    def close(self):
        """Close the serial port."""
        self.ser.close()

    def injecting(self, inject_vol_ul: float, inject_time_ms: int | None = None, mixing_cycles: int = 1) -> None:
        if inject_time_ms is not None:
            logger.warning("Time injection cannot be specified for PIC controller, it will be ignored.")
        
        # Calculate valve open time per cycle
        valve_time = round(self._convert_volume_to_time(inject_vol_ul) / mixing_cycles)
        
        # Inject
        for _ in range(mixing_cycles):
            self.set_delay(valve_time)
            self.set_valve_time(1, valve_time)
            self.open_valves_sequence('K')
            time.sleep((valve_time + VALVE_2_TIME)/1000)  # Wait for both valves to finish, in seconds
    
    def _convert_volume_to_time(self, vol_ul: float) -> int:
        """
        Convert volume in ul to time in ms using linear mapping, where vol = a * time + b.
        :param vol_ul: Volume in microliters
        :return: Time in milliseconds
        """
        a, b = VOL_TIME_MAP[self._map_converter]
        vol_time = (vol_ul - b) / a
        return int(vol_time)  

# Example usage
if __name__ == "__main__":
    import json
    from pathlib import Path
    from time import sleep
    from typing import Any
    from pycromanager import Core

    from a1_manager import A1Manager, StageCoord
    from a1_manager.microscope_hardware.nanopick.marZ_api import MarZ
    arm = MarZ(core=Core(), dish='96well') # type: ignore
    controller = PICController(needle_size=30, pressure=0.35, port='COM10')

    a1_manager = A1Manager(
        objective='20x',
        nanopick_dish = '96well')
   
    dish_calib_path = Path(r"C:\repos\A1_manager\config\calib_96well.json")
    with open(dish_calib_path, 'r') as f:
        dish_calib: dict[str, dict[str, Any]]= json.load(f)
    keys = list(dish_calib.keys())
    print("Wells in calibration:", keys)
   
    for well in list(keys):
        print(well)
       
        arm.to_home() # Lift up the head above the plate
        mt = dish_calib.get(well, {})
        position = StageCoord(xy=mt['center'])
        a1_manager.set_stage_position(position)
        sleep(0.5)
       
       
        # Injection of ligands
        arm.to_liquid()
        controller.injecting(inject_vol_ul=10)
        arm.to_home()
        sleep(0.5)
   
 
    controller.close()
    
"""     from a1_manager import A1Manager, StageCoord
    # arm = MarZ(core=Core(), dish='96well') # type: ignore
    controller = PICController(needle_size=30, pressure=0.35, port='COM10')
    
    # a1_manager = A1Manager(objective='10x')
    
    # inject_position = StageCoord(xy=(-42667.4, 18511))
    # a1_manager.set_stage_position(inject_position)
    
    vol_to_inject = 8305
    
    for i in range(10):
        print(f"Instance {i+1}")
        controller.injecting(inject_vol_ul=5, mixing_cycles=1) """
        
    


    
    
    
    
    # Update COM port as needed (e.g., COM3)
    # from pycromanager import Core
"""     from a1_manager import A1Manager, StageCoord
    # arm = MarZ(core=Core(), dish='96well') # type: ignore
    controller = PICController(needle_size=30, pressure=0.35, port='COM10')
    
    # a1_manager = A1Manager(objective='10x')
    
    # inject_position = StageCoord(xy=(-42667.4, 18511))
    # a1_manager.set_stage_position(inject_position)
    
    vol_to_inject = 8305
    
    for i in range(5):
        print(f"Instance {i+1}")
        controller.injecting(inject_vol_ul=10, mixing_cycles=1) """
    
    # fill_position = StageCoord(xy=(-3689.4, 18511))
    
    # a1_manager.set_stage_position(fill_position)
    
    # print("Current head position:", arm._get_arm_position)
    # #arm.to_air() # Lift up the head just above the plate
    # arm._set_arm_position(arm._ref_position)
    # print("Current head position after moving to air:", arm._get_arm_position)
    
    # controller.set_led_ring(2)
    # controller.close()

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
""" 
    print("Testing connection:", controller.test_connection())
    #print("Toggle LED2:", controller.toggle_led2())
    #print("Set switch 1 ON:", controller.set_switch(1, '+'))
    #print("Query all outputs:", controller.query_all_outputs())
    # print("Set Valve1 time 100 ms:", controller.set_valve_time(1, 100))
    # print("Set delay 200 ms:", controller.set_delay(200))

    print("Set ring 1:", controller.set_led_ring(1))
    time.sleep(1)
    print("Set ring 2:", controller.set_led_ring(2))
    time.sleep(1)
    print("Turn off rings:", controller.set_led_ring(0))
    controller.set_valve_time(1, 100)
    controller.set_valve_time(2, 100) 
    controller.set_delay(10)
    print("Open both valves (1 then 2):", controller.open_valves_sequence('K'))
    # # print("Open Valve1:", controller.open_valve(1))
    # # print("Open Valve2:", controller.open_valve(2))
    #for i in range(3):
        #print("Open both valves (1 then 2):", controller.open_valves_sequence('K'))
        #print("Set ring 2:", controller.set_led_ring(2))
        #time.sleep(1)
        #print("Turn off rings:", controller.set_led_ring(0))
        #time.sleep(0.5)
    # time.sleep(1)  # Wait a bit before the next command
    # time.sleep(1)
    # print("Open both valves (2 then 1):", controller.open_valves_sequence('L'))
    # print("Testing connection:", controller.test_connection()) """
    

