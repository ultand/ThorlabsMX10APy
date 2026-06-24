
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
            self.inst.query("*OPC?")
            self.check_errors()
            return True

        except VisaIOError as e:
            self.logger.error(f"Hardware Communication Error during command {command}: {e}")
            return False

# RF Amplifier commands
    @property
    def amplifier_gain_mode(self)->str:
        mode = self._instrument_query("AMP:MODE?")
        return 'Analog' if mode is '0' else 'Digital'
    
    @amplifier_gain_mode.setter
    def amplifier_gain_mode(self, value: str):
        if value.lower() not in ["digital", "analog"]:
            pass # should throw an error
        
        # there are less verbose ways to type this
        if value.lower() == "digital":
            pass
        elif value.lower() == "analog":
            pass

    @property
    def amplifier_is_enabled(self)->bool:
        res = self._instrument_query("AMP:POW?")
        return res in ['1', 'ON']


# MZI COMMANDS
    @property
    def is_mzm_calibrating(self)->bool:
        state = self._instrument_query("MZM:CAL?")
        return state == '0'
   
    @property
    def mzm_dither_amplitude(self)->float:
        amplitude = self._instrument_query("MZM:Dither:AMP?")
        return float(amplitude)

    @property
    def mzm_dither_frequency(self)->float:
        frequency = self._instrument_query("MZM:Dither:FREQ?")
        return float(frequency)

    @property
    def mzm_hold_ratio(self)->float:
        pass

    @property
    def mzm_bias_mode(self)->str:
        mode = self._instrument_query("MZM:MODE?")
        match mode:
            case "0":
                return "Off"
            case "1":
                return "Auto Peak"
            case "2":
                return "Auto Null"
            case "3":
                return "Auto Quad Pos"
            case "4":
                return "Auto Quad Neg"
            case "5":
                return "Hold Quad Pos"
            case "6":
                return "Hold Quad Neg"
            case "7":
                return "Manual Voltage"
            case "8":
                return "Auto Power Ratio Pos"
            case "9":
                return "Auto Power Ratio Neg"
    
    @property
    def is_mzm_at_setpoint(self)->bool:
        state = self._instrument_query("MZM:SET?")
        return state == '1'

    @property
    def post_mzm_power_mw(self)->float:
        pass

    @property
    def post_mzm_power_dbm(self)->float:
        pass

# VOA Commands
    @property
    def voa_is_enabled(self)->bool:
        pass
    @property
    def voa_attenuation(self)->float:
        pass

# System Commands

    def check_errors(self):
        pass
    
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
