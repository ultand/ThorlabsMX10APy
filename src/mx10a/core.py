
# imports
import logging
import pyvisa
import time
import atexit
from pyvisa import VisaIOError
from src.mx10a.constants import *

class MX10A:
    def __init__(self, instrument, override_safety = False):
        self.logger = logging.getLogger(__name__)

        self.inst = instrument
        self.inst.write_termination = '\n'
        self.inst.read_termination = '\n'

        atexit.register(self.close)
        
        # set initial states

        # start the VOA in constant attenuation state
        self._instrument_write("VOA:MODE: 0")
        # start with active VOA - safety mechanism
        self.voa_attenuation = MAX_VOA_ATTENUATION
        self.voa_is_enabled = True
    
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
    # bizarre that gain_mode appears to have opposite write and read commands?
    @property
    def amplifier_gain_mode(self)->str:
        mode = self._instrument_query("AMP:MODE?")
        return 'Analog' if mode is '0' else 'Digital'

    @amplifier_gain_mode.setter
    def amplifier_gain_mode(self, value: str):
        if value.lower() not in ["digital", "analog"]:
            # this may not be the best way to handle this issue. 
            e_string = "Error: provided amplifier gain mode is neither 'digital' nor 'analog'. Value has not been updated. Please check provided value."
            self.logger.error(e_string))
            raise ValueError(e_string)
        
        if value.lower() == "digital":
            command = "0"
        elif value.lower() == "analog":
            command = "1"
        self._instrument_write(f"AMP:MODE: {command}")

    @property
    def is_amplifier_enabled(self)->bool:
        res = self._instrument_query("AMP:POW?")
        return res in ['1', 'ON']
    
    @is_amplifier_enabled.setter
    def is_amplifier_enabled(self, value:bool):
        command = "1" if value else "0"
        self._instrument_write(f"AMP:POW: {command}")

    @property
    def amplifier_gain(self)->float:
        value = self._instrument_query("AMP:GAIN?")
        return float(value)

    @amplifier_gain.setter
    def amplifier_gain(self, value:float):
        if value < AMPLIFIER_GAIN_MINIMUM | value > AMPLIFIER_GAIN_MAXIMUM: 
            self.logger.error(f"Error: Provided amplifier gain {value} is outside of software defined range {AMPLIFIER_GAIN_MINIMUM} -- {AMPLIFIER_GAIN_MAXIMUM}. Value not updated.")
            return
        self._instrument_write(f"AMP:GAIN {value}")

    # set the amplifier swing

# MZI COMMANDS
    @property
    def is_mzm_calibrating(self)->bool:
        state = self._instrument_query("MZM:CAL?")
        return state == '0'
   
    @property
    def mzm_dither_amplitude(self)->float:
        amplitude = self._instrument_query("MZM:Dither:AMP?")
        return float(amplitude)

    @mzm_dither_amplitude.setter
    def mzm_dither_amplitude(self, value:float):
        # check that value is acceptable
        if value < MZM_DITHER_AMPLITUDE_MINIMUM | value > MZM_DITHER_AMPLITUDE_MAXIMUM:
            self.logger.error(f"Error: Provided dither amplitude {value} is outside of software defined range {MZM_DITHER_AMPLITUDE_MINIMUM} -- {MZM_DITHER_AMPLITUDE_MAXIMUM}}. Value not updated.")
        else:
            self._instrument_write(f"MZM:Dither:AMP {value}")

    @property
    def mzm_dither_frequency(self)->float:
        frequency = self._instrument_query("MZM:Dither:FREQ?")
        return float(frequency)
    
    @mzm_dither_frequency.setter
    def mzm_dither_frequency(self, value: float):
        if value < MZM_DITHER_FREQUENCY_MINIMUM:
            pass
        elif value > MZM_DITHER_FREQUENCY_MAXIMUM:
            pass
        else:
            self._instrument_write(f"MZM:Dither:FREQ {value}")

    @property
    def mzm_hold_ratio(self)->float:
        # check that state is auto power ratio
        current_state = self.mzm_bias_mode
        if "auto power" not in current_state.lower():
            self.logger.warning(f"ERROR: Current MZM state is {current_state}. MZM hold ratio only has an effect in auto power modes. Update MZM mode accordingly.")
        value = self._instrument_query("MZM:HOLD:Ratio?")
        return float(value)

    @mzm_hold_ratio.setter
    def mzm_hold_ratio(self, value:float):
        
        # check that value is in allowed range
        if value < MZM_HOLD_RATIO_MINIMUM | value > MZM_HOLD_RATIO_MAXIMUM:
            self.logger.error(f"ERROR: Provided hold ratio {value} is outside of software defined range {MZM_HOLD_RATIO_MINIMUM} - {MZM_HOLD_RATIO_MAXIMUM}. Value not updated.")
            return

        # check that the state is in an auto power mode
        current_state = self.mzm_bias_mode
        if "auto power" not in current_state.lower():
            self.logger.warning(f"ERROR: Current MZM state is {current_state}. MZM hold ratio only has an effect in auto power modes. Update MZM mode accordingly.")

        self._instrument_write(f"MZM:HOLD:Ratio {value}")
        
    @property
    def mzm_hold_voltage(self)->float:
        # check that state is manual voltage
        current_state = self.mzm_bias_mode
        if current_state.lower() is not "manual voltage":
            self.logger.warning("WARNING: MZM mode is not Manual Voltage. Hold voltage is not currently being used.")
        
        value = self._instrument_query("MZM:HOLD:V?")
        return float(value)

    @mzm_hold_voltage.setter
    def mzm_hold_voltage(self, value:float):
        if value < MZM_MANUAL_VOLTAGE_MIN | value > MZM_MANUAL_VOLTAGE_MAX:
            self.logger.error(f"ERROR: Provided manual voltage {value} is outside software defined range {MZM_MANUAL_VOLTAGE_MIN} - {MZM_MANUAL_VOLTAGE_MAX}. Value has not been updated.")
            return
        
        current_state = self.mzm_bias_mode
        if current_state.lower() is not "manual voltage":
            self.logger.warning("WARNING: MZM mode is not Manual Voltage. Hold voltage is not currently being used.")

        self._instrument_write(f"MZM:HOLD:V {value}")

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

    @mzm_bias_mode.setter
    def mzm_bias_mode(self, value:str):
        match value.lower():
            case "0" | "off":
                command = "0"
            case "1" | "auto peak":
                command  = "1"
            case "2" | "auto null":
                command = "2"
            case "3" | "auto quad pos":
                command = "3"
            case "4" | "auto quad neg":
                command = "4"
            case "5" | "hold quad pos":
                command = "5"
            case "6" | "hold quad neg":
                command = "6"
            case "7" | "manual voltage":
                command = "7"
            case "8" |  "auto power ratio pos":
                command = "8"
            case "9" | "auto power ratio neg":
                command = "9"
            case _:
                pass
        self._instrument_write(f"MZM:MODE: {command}")

    @property
    def is_mzm_at_setpoint(self)->bool:
        state = self._instrument_query("MZM:SET?")
        return state == '1'

    @property
    def post_mzm_power_mw(self)->float:
        power = self._instrument_query("MZM:TAP:MW?")
        return float(power)

    @property
    def post_mzm_power_dbm(self)->float:
        power = self._instrument_query("MZM:TAP:DBM?")
        return float(power)

    @property
    def mzm_bias_voltage(self)->float:
        bias_voltage = self._instrument_query("MZM:V?")
        return float(bias_voltage)

    # reseting the mzm should probably not be a property
    @property
    def _reset_mzm(self):
        self._instrument_write("MZM:RESET")

# VOA Commands
    @property
    def voa_is_enabled(self)->bool:
        state = self._instrument_query("VOA:POW?")
        return bool(state)

    @voa_is_enabled.setter
    def voa_is_enabled(self, value: bool):
        state = '1' if value else '0'
        self._instrument_write(f"VOA:POW: {state}")

    @property
    def voa_set_attenuation(self)->float:
        value = self._instrument_query("VOA:ATT?")
        return float(value)
    
    @voa_set_attentuation.setter
    def voa_set_attenuation(self, value:float)
        # check if value is a valid value
        if value < MIN_VOA_ATTENUATION | value > MAX_VOA_ATTENUATION:
            self.logger.error(f"ERROR: Provided VOA attenuation {value} is outside of software defined range {MIN_VOA_ATTENUATION} - {MAX_VOA_ATTENUATION}. Value not updated.")
            return
        self._instrument_write(f"VOA:ATT {value}")

    @property
    def voa_measured_attenuation(self)->float:
        value = self._instrument_query("VOA:MEAS?")
        return float(value)

    @property
    def voa_measured_optical_output_power_dbm(self)->float:
        value = self._instrument_query("VOA:TAP:DBM?")
        return float(value)

    @property
    def voa_measured_optical_output_power_mw(self)->float:
        value = self._instrument_query("VOA:TAP:MW?")
        return float(value)


# System Commands
    def check_errors(self):
        try:
            for _ in range(ERROR_QUEUE_LIMIT):
                error_string = self.inst.query("SYST:ERRor?").strip()
                if not error_string or error_string.startswith('0') or "No error":
                    break

                self.logger.error(f"MX10A Hardware Error: {error_string}")
            except Exception as e:
                self.logger.debug(f"Could not read error queue: {e}")
    
    def system_serial_number(self):
        return self._instrument_query("SYS:SER?")
    
    def system_bootloader(self):
        return self._instrument_query("SYS:BOOT?")

    def system_firmware(self):
        return self._instrument_query("SYS:FIRM?")

    def system_hardware(self):
        return self._instrument_query("SYS:HARD?")

    def system_restart(self):
        self._instrument_write("SYS:RESTART")

    def system_sleep(self):
        self._instrument_write("SYS:SLEEP")

    def system_wake(self):
        self._instrument_query("SYS:WAKE")

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
                
