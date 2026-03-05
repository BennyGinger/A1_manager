from __future__ import annotations # Enable type annotation to be stored as string
from abc import ABC, abstractmethod
import logging
import serial
import time
from dataclasses import dataclass
import logging

import requests

# Set up logging
logger = logging.getLogger(__name__)

class InjectionDevice(ABC):
    """ Abstract base class for injection devices. """
    
    def __init__(self) -> None:
        pass

    @abstractmethod
    def inject(self, inject_vol_ul: float, inject_time_ms: int | None = None, mixing_cycles: int = 1) -> None:
        """ Inject a specified volume using the device.
        
        Args:
            inject_vol_ul (float): Volume to inject in microliters.
            inject_time_ms (int | None): Time to inject in milliseconds. If None, volume-based injection is used.
            mixing_cycles (int): Number of mixing cycles during injection.
        """
        pass
    
    @abstractmethod
    def fill(self, fill_vol_nl: float, fill_time_ms: int | None = 100) -> None:
        """ Fill the device with a specified volume.
        
        Args:
            fill_vol_nl (float): Volume to fill in nanoliters.
            fill_time_ms (int | None): Time to fill in milliseconds. If None, volume-based filling is used.
        """
        pass
    
    @abstractmethod
    def set_led_ring(self, ring: int = 0, brightness: int | None = None) -> None:
        """ Set the LED ring state.
        
        Args:
            ring (int): Ring number (0 for off, 1 for inner, 2 for outer).
            brightness (int | None): Brightness level (if applicable).
        """
        pass
    
    @property
    @abstractmethod
    def injection_altitude(self) -> str:
        """Gives the altitude at which the injection happens, among 'air', 'dip' or 'deep'."""
        pass


#### Valve Class ####


VALVE_2_TIME = 1000 # ms 
# Mapping of volume (ul) relationship to time (ms) as y = ax + b, with key as "needleSize_pressure" and value as (a, b)
VOL_TIME_MAP = {
    30: {"0.35": (0.0012, 0.0338),},
    50: {"0.20": (0.0039, 0.3043),"0.30": (0.0057, 0.101),"0.40": (0.0072, 0.1051),},
    70: {"0.20": (0.0144, 1.5931),},
}

class PICController(InjectionDevice):
    def __init__(self, needle_size: int, pressure: float, test_mode: bool = False, port: str = "COM8") -> None:
        """
        Initialize the PIC Controller connection.
        :param needle_size: Needle size in microns (e.g., 30)
        :param pressure: Pressure in bar (e.g., 0.35)
        :param port: COM port name (e.g., 'COM3')
        :param test_mode: If True, then the volume to time conversion is skipped for testing purposes, and only the volume value is used as time.
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
        
        if needle_size not in VOL_TIME_MAP:
            raise ValueError(f"Needle size {needle_size} not supported. Only {list(VOL_TIME_MAP.keys())} are supported.")
        
        neddle_map = VOL_TIME_MAP[needle_size]
        if f"{pressure:.2f}" not in neddle_map:
            raise ValueError(f"Pressure {pressure} not supported for needle size {needle_size}. Only {list(neddle_map.keys())} are supported.")
        
        self._converter_params = neddle_map[f"{pressure:.2f}"]
        
        # initialize valve 2 time
        self._set_valve_time(2, VALVE_2_TIME)
        self.test_mode = test_mode

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

    def _set_valve_time(self, valve: int, duration: int):
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

    def _set_delay(self, delay: int):
        """Set delay between valve openings with 'k' command."""
        return self._send_command(f'k{delay}')

    def _open_valves_sequence(self, mode: str):
        """
        Open valves in sequence with delay.
        'K' = Valve1 then Valve2
        'L' = Valve2 then Valve1
        """
        if mode not in ['K', 'L']:
            raise ValueError("Mode must be 'K' or 'L'")
        return self._send_command(mode)

    def _close(self):
        """Close the serial port."""
        self.ser.close()

    def _convert_volume_to_time(self, vol_ul: float) -> int:
        """
        Convert volume in ul to time in ms using linear mapping, where vol = a * time + b.
        :param vol_ul: Volume in microliters
        :return: Time in milliseconds
        """
        a, b = self._converter_params
        vol_time = (vol_ul - b) / a
        return int(vol_time)
    
    def inject(self, inject_vol_ul: float, inject_time_ms: float | None = None, mixing_cycles: int = 1) -> None:
        """
        Function controlling injection. Sets the volume according to number of mixing cycles. 
        It sets the opening time of the first valve and the delay to the desired time by converting the desired volume to time.
        Args:
            inject_vol_ul(float): injection volume in microliters
            inject_time_ms(float | None): injection time in milliseconds, will be None in case of valves
            mixing_cycles(int): number of mixing cycles (default: 1 - meaning there is no mixing)
        """
        if inject_time_ms is not None:
            logger.warning("Time injection cannot be specified for PIC controller, it will be ignored.")
        
        
        # Calculate valve open time per cycle
        if self.test_mode:
            valve_time = round(inject_vol_ul)
        else:
            valve_time = round(self._convert_volume_to_time(inject_vol_ul) / mixing_cycles)
              
        # Inject
        for _ in range(mixing_cycles):
            self._set_delay(valve_time)
            self._set_valve_time(1, valve_time)
            self._open_valves_sequence('K')
            time.sleep((valve_time + VALVE_2_TIME)/1000)  # Wait for both valves to finish, in seconds
    
    def set_led_ring(self, ring: int = 0, brightness: int | None = None) -> None:
        """Toggle LED rings."""
        
        if brightness is not None:
            logger.warning("Brightness setting is not supported for PIC controller, it will be ignored.")
        
        if ring == 0:
            self._send_command('s1-', wait_for_reply=False)
            self._send_command('s5-', wait_for_reply=False)
            return 
        if ring == 1:
            self._send_command('s1-', wait_for_reply=False)
            self._send_command('s5+', wait_for_reply=False)
            return 
        if ring == 2:
            self._send_command('s1+', wait_for_reply=False)
            self._send_command('s5+', wait_for_reply=False)
            return
    
    def fill(self, fill_vol_nl: float, fill_time_ms: int | None = 100) -> None:
        logger.warning("Filling method is not implemented for PIC controller.")

    @property
    def injection_altitude(self) -> str:
        """Gives the altitude at which the injection happens, among 'air', 'dip' or 'deep'."""
        return "air"


#### Head Class ####


BASE_URL = "http://localhost:5000/api"  # Base URL for the API

# Volumes
MAX_VOLUME = 500 # in nanoliters
MIN_VOLUME = 10  # in nanoliters


@dataclass(slots=True)
class Head(InjectionDevice):
    """
    Class that controls the API head.
    """

    _track_volume: float = MAX_VOLUME  # in nanoliters

    def __post_init__(self):
        self.switch_LED_off()
    
    @property
    def get_track_volume(self) -> float:
        return self._track_volume
    
    def _set_volume(self, volume_nl: float, time_ms: float | None = None) -> None:
        """
        A volume-time pair is sent to the controller. The piezo unit will start immediately to withdraw or inject the specified volume under the specified time. 
        The volume values are absolute values. If the volume is less than the previously sent item, then fluid is withdrawn 
        through the pipette. 
        If the volume is greater than the previously sent one, fluid will be injected back.
        
        Args:
            volume_nl (float): Volume in nanoliters 
            time_ms (float): Time in milliseconds (default: 100 ms)
        """

        # Endpoint and parameters
        endpoint = f"{BASE_URL}/setVolume?volume={volume_nl}&time={time_ms}"
        try:
            response = requests.put(endpoint)
            if response.status_code == 200:
                logger.debug(f"Success: {response.text}")
            else:
                logger.error(f"Error {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
    
    def switch_LED_on(self) -> None:
        """
        Switch on the LED light
        """
        self.set_led_ring(1, 100) 
        self.set_led_ring(2, 100) 
        
    def switch_LED_off(self) -> None:
        """
        Switch off the LED light
        """
        self.set_led_ring(1, 0) 
        self.set_led_ring(2, 0) 
            
    def set_led_ring(self, ring: int = 0, brightness: int | None = None) -> None:
        """
        Set brightness level of LED 
        
        Args:
            ring (int): LED ID (1-2)
            brightness (int): Brightness level (0-100)
        """
        if brightness == None:
            logger.error("You forgot to add a value for brightness between 0 and 100.")
        else:
            # Endpoint and parameters
            endpoint = f"{BASE_URL}/setLED/{ring}?brightness={brightness}"
            try:
                response = requests.put(endpoint)
                if response.status_code == 200:
                    logger.debug(f"Success: {response.text}")
                else:
                    logger.error(f"Error {response.status_code}: {response.text}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")

    def fill(self, fill_vol_nl: float, fill_time_ms : float | None = 100) -> None:
        
        fill_vol_nl = abs(fill_vol_nl)  # Ensure volume is positive
        max_filling_volume = MAX_VOLUME - self.get_track_volume
        
        if fill_vol_nl > max_filling_volume:
            vol_to_fill = max_filling_volume
            logger.warning(f"The volume to fill exceeds the maximum volume of the pipette! It will be set to {vol_to_fill} nanoliters.")
        else:
            vol_to_fill = fill_vol_nl

        # Draw the liquid into the pipette
        self._set_volume(self.get_track_volume - vol_to_fill, fill_time_ms)
        self._track_volume += vol_to_fill

    def inject(self, inject_vol_ul: float, inject_time_ms: float | None = None, mixing_cycles: int = 1) -> None:
                
        inject_vol_nl = abs(inject_vol_ul)  # Ensure volume is positive. 
        max_injection_volume = self.get_track_volume - MIN_VOLUME
        
        if inject_vol_nl > max_injection_volume:
            vol_to_inject = max_injection_volume
            logger.warning(f"The volume to inject exceeds the current volume in the pipette! It will be set to {max_injection_volume} nanoliters (i.e. current volume - minimum volume).")
        else:
            vol_to_inject = inject_vol_nl
            
        # Draw the liquid into the pipette
        self._set_volume(self.get_track_volume + vol_to_inject, inject_time_ms)
        self._mixing(mixing_cycles, vol_to_inject)
        self._track_volume -= vol_to_inject

    @property
    def injection_altitude(self) -> str:
        """Gives the altitude at which the injection happens, among 'air', 'dip' or 'deep'."""
        return "deep"

    def _mixing(self, mixing_cycles: int = 1, vol_to_mix: float = 0, mixing_time_ms: float = 20) -> None:
        """
        Mix the liquid in the pipette by sucking it up and letting it out multiple times.
        Args:
            mixing_cycles(int): number of mixing cycles (default: 1 - meaning there is no mixing)
            mixing_time_ms(float): time for each mixing cycle in milliseconds (default: 20 ms)
            vol_to_mix(float): volume to inject in nanoliters
        """
        
        if mixing_cycles > 1:
            for _ in range(mixing_cycles):
                self._set_volume(self.get_track_volume - vol_to_mix, mixing_time_ms)  # suck it up
                self._set_volume(self.get_track_volume + vol_to_mix, mixing_time_ms)  # let it out
        else:
            pass