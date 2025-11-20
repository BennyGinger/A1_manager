from __future__ import annotations # Enable type annotation to be stored as string
import logging
import serial
import time


#from a1_manager.microscope_hardware.nanopick.marZ_api import MarZ
import a1_manager
# from a1_manager.microscope_hardware.nanopick.masterclass import InjecterManager

# Set up logging
logger = logging.getLogger(__name__)

VALVE_2_TIME = 1000 # ms 

class PICController():
    def __init__(self, port: str = "COM10", baudrate: int = 9600, timeout: float = 1.0):
        """
        Initialize the PIC Controller connection.
        :param port: COM port name (e.g., 'COM3')
        :param baudrate: Baud rate (default 9600)
        :param timeout: Read timeout in seconds
        """
        self.ser = serial.Serial(
            port=port, 
            baudrate=baudrate, 
            timeout=timeout,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )
        time.sleep(2)  # wait for the serial connection to initialize
        self._clear_buffers()
        
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

    def test_connection(self):
        """Send the 'a' command to test communication."""
        return self._send_command('a')

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

    def set_switch(self, switch: int, action: str):
        """
        Control switches using 'sXA' command.
        :param switch: switch number (1–7)
        :param action: '+', '-', or '?' for status
        """
        if action not in ['+', '-', '?']:
            raise ValueError("Action must be '+', '-', or '?'")
        return self._send_command(f's{switch}{action}')

    def query_all_outputs(self):
        """Query all output statuses with 'S' command."""
        return self._send_command('S')

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

    def _open_valve(self, valve: int):
        """
        Open valve for the previously specified time.
        Valve 1 → 'I', Valve 2 → 'J'
        """
        if valve == 1:
            cmd = 'I'
        elif valve == 2:
            cmd = 'J'
        else:
            raise ValueError("Valve must be 1 or 2")
        return self._send_command(cmd)

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

    def injecting(self, volume: float, time: int | None = None, mixing_cycles: int | None = None) -> None:
        if time is not None:
            logger.warning("Time injection cannot be specified for PIC controller, it will be ignored.")
        
        if mixing_cycles is not None:
            logger.warning("Mixing cycles cannot be specified for PIC controller, it will be ignored.")
        
       
        valve_time = self._convert_volume_to_time(volume)
        self.set_delay(valve_time)
        self.set_valve_time(1, valve_time)
        
        self.open_valves_sequence('K')
    
    def _convert_volume_to_time(self, volume: float) -> int:
        # logger.warning('Not implemented: volume to time conversion for PIC controller. Using volume as time directly.')
        return int(volume)  # Placeholder implementation

# Example usage
if __name__ == "__main__":
    # Update COM port as needed (e.g., COM3)
    # from pycromanager import Core
    from a1_manager import A1Manager, StageCoord
    # arm = MarZ(core=Core(), dish='96well') # type: ignore
    controller = PICController(port='COM10', timeout=1.0)
    
    a1_manager = A1Manager(objective='10x')
    
    inject_position = StageCoord(xy=(-42667.4, 18511))
    a1_manager.set_stage_position(inject_position)
    
    vol_to_inject = 10
    
    for i in range(100):
        print(f"Instance {i+1}")
        controller.injecting(volume=vol_to_inject)
        time.sleep(2)
    
    fill_position = StageCoord(xy=(-3689.4, 18511))
    
    a1_manager.set_stage_position(fill_position)
    
    # print("Current head position:", arm._get_arm_position)
    # #arm.to_air() # Lift up the head just above the plate
    # arm._set_arm_position(arm._ref_position)
    # print("Current head position after moving to air:", arm._get_arm_position)
    
    
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
    

