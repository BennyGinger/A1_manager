from __future__ import annotations # Enable type annotation to be stored as string
import json
import logging
from a1_manager.microscope_hardware.nanopick.devices.injection_protocol import PickDevice
import serial
import time

# Set up logging
logger = logging.getLogger(__name__)

VALVE_2_TIME = 1000 # ms 
# Mapping of volume (ul) relationship to time (ms) as y = ax + b, with key as "needleSize_pressure" and value as (a, b)
VOL_TIME_MAP = {
    30: {"0.35": (0.0012, 0.0338),},
    50: {"0.10": (0.0027, 0.013), "0.20": (0.0039, 0.3043),"0.30": (0.0057, 0.101),"0.40": (0.0072, 0.1051),},
    70: {"0.20": (0.0144, 1.5931),},
}

class PICController(PickDevice):
    def __init__(self, needle_size: int, pressure: float, test_mode: bool = False, port: str = "COM8"):
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

    def set_led_ring(self, ring: int = 0, brightness: int | None = None) -> None:
        """Toggle LED rings."""
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
    
    def _convert_volume_to_time(self, vol_ul: float) -> int:
        """
        Convert volume in ul to time in ms using linear mapping, where vol = a * time + b.
        :param vol_ul: Volume in microliters
        :return: Time in milliseconds
        """
        a, b = self._converter_params
        vol_time = (vol_ul - b) / a
        return int(vol_time)
    
    def fill(self, fill_vol_nl: float, fill_time_ms: float | None = 100) -> None:
        logger.warning("Filling is not supported for PIC controller, skipping.")

# Example usage
if __name__ == "__main__":
    
        controller = PICController(needle_size=50, pressure=0.2, test_mode=True)
        controller.inject(inject_vol_ul=10, mixing_cycles=3)
        controller._close()
                