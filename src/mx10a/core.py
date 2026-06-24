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

    def _instruments_query(self, query:str):
        pass

    def _instrument_write(self, command:str):
        pass

# RF Amplifier commands
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




