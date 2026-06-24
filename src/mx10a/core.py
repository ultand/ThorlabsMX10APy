# imports
import logging
import pyvisa
import time
import atexit

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



