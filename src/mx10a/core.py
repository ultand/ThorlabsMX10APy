
# imports
import logging
import pyvisa
import time
import atexit
from pyvisa import VisaIOError

class MX10A:
    def __init__(self, instrument, override_safety = False):
        self.logger = logging.getLogger(__name__)

        self.inst = instrument
        self.inst.write_termination = '\n'
        self.inst.read_termination = '\n'

        atexit.register(self.close)

        # LOAD CONSTANTS
        # set initial states

    def _instrument_query(self, query:str):
        try:
            self.logger.info(f"Sending command: {query}")
            response = self.inst.query(query)
            self.check_errors()
            return response.strip()
        
        except VisaIOError as e:
            self.logger.error(f"Hardware Communication Error during {query}: {e}")
            return None

    def _instrument_write(self, command:str):
        try:
            self.logger.info(f"Sending command: {command}")
            # check for operation complete
            self.inst.write(command)
            self.logger.info(f"Sending command: *OPC?")
            self.inst.query ("*OPC?")
            self.check_errors()
            return True

        except VisaIOError as e:
            self.logger.error(f"Hardware Communication Error during command {command}: {e}")
            return False

# RF Amplifier commands
    @property
    def gain_mode(self)->str:



# MZI COMMANDS
# VOA Commands
# System Commands

    def close(self):
        if hasattr(self, 'inst'):
            try:
                pass
            except VisaIOError:
                self.logger.error("Could not cleanly reset settings during close. Connection may be dead.")
            finally:
                try:
                    self.inst.close()
                except Exception:
                    pass
                del self.inst




