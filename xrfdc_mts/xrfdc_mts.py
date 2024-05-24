import os
import cffi
import time
import xrfdc
from xrfdc import *



# Print colors
_black = "\033[0;30m"
_red = "\033[0;31m"
_green = "\033[0;32m"

# Messages
_INFO = _black + "[" + _green + "INFO" + _black + "]"
_ERROR = _black + "[" + _red + "ERROR" + _black + "]"

# Extend the CFFI with the local C-file 
_THIS_DIR = _THIS_DIR = os.path.dirname(__file__)
with open(os.path.join(_THIS_DIR, 'xrfdc_functions.c'), 'r') as f:
    header_text = f.read()
    
xrfdc._ffi.cdef(header_text)

# remove RFdc driver binding in order to bind RFdcMTS instead
RFdc.bindto = []

class RFdcMTS(RFdc):
    """Class for handling Multi-Tile Synchronization (MTS).
    
    This class is bound to the IP xilinx.com:ip:usp_rf_data_converter:2.6, 
    xilinx.com:ip:usp_rf_data_converter:2.4 or xilinx.com:ip:usp_rf_data_converter:2.3.
    Derived from the RFdc class.

    Members
    -------
    dac_sync_config: XRFdc_MultiConverter_Sync_Config
        Struct containing DAC MTS config.
    adc_sync_config: XRFdc_MultiConverter_Sync_Config
        Struct containing ADC MTS config.
    """

    bindto = ["xilinx.com:ip:usp_rf_data_converter:2.6",
              "xilinx.com:ip:usp_rf_data_converter:2.4", 
              "xilinx.com:ip:usp_rf_data_converter:2.3"]

    def __init__(self, description):
        """Class is constructed by PYNQ.
        
        Creates pointers to sync config structs.
        """
        super().__init__(description)
        self.dac_sync_config = xrfdc._ffi.new("XRFdc_MultiConverter_Sync_Config*")
        self.adc_sync_config = xrfdc._ffi.new("XRFdc_MultiConverter_Sync_Config*")
        
    def autoRunMTS(self, dacTileEnable, adcTileEnable, verbose=False):
        """Let the driver handle the latency synchronization sequence.
        
        First measures the latency with input argument of -1.
        Then, it uses the results to calculate and apply the appropriate
        latency margin.
        Calls MTS synchronisation for the second time with the measured latancy+margin.
        
        Parameters
        ----------
        dacTileEnable: int
            0: disable all DAC tiles
            bit 1: enable tile0
            bit 2: enable tile1
            etc...
        adcTileEnable: int
            0: disable all ADC tiles
            bit 1: enable tile0
            bit 2: enable tile1
            etc...
        """
        self.initMTS(-1, dacTileEnable, -1, adcTileEnable, verbose=verbose)
        
        # fixted margin of 16 samples for DACs
        dacTargetLatency = 0
        if dacTileEnable:
            dacLatency = max(self.dac_sync_config.Latency)
            dacMargin = 16
            dacTargetLatency = dacLatency + dacMargin
            
        
        # margin for ADCs must be nr. of samples er cycle * decimation facotr
        # Config is read from the tile 0 block 0 as this is the required ADC for MTS.
        adcTargetLatency = 0
        if adcTileEnable:
            adcLatency = max(self.adc_sync_config.Latency)
            adcSampPerCycle = self.adc_tiles[0].blocks[0].FabRdVldWords
            adcDecimationFactor = self.adc_tiles[0].blocks[0].DecimationFactor
            margin = adcSampPerCycle * adcDecimationFactor
            adcTargetLatency = adcLatency + margin
            
        self.syncMTS(dacTargetLatency, dacTileEnable, adcTargetLatency, adcTileEnable, verbose=verbose)
        
    def initMTS(self, dacTargetLatency, dacTileEnable, adcTargetLatency, adcTileEnable, verbose=False):
        """Initialize MTS.
        
        Initializes the sync config struct using XRFdc_MultiConverter_Init and then
        configures with the given target latency with XRFdc_MultiConverter_Sync.
        The resulting latency can be read from dac_sync_config.Latency or adc_sync_config.Latency.
        When the target latency is set to -1, the base latency can be measured.
        
        Parameters
        ----------
        dacTargetLatency: int
            Target latency for DAC
        dacTileEnable: int
            0: disable all DAC tiles
            bit 1: enable tile0
            bit 2: enable tile1
            etc...
        adcTargetLatency: int
            Target latency for ADC
        adcTileEnable: int
            0: disable all ADC tiles
            bit 1: enable tile0
            bit 2: enable tile1
            etc...
            
        """
        dacLatency = None
        adcLatency = None 

        ConfigPtrDAC = xrfdc._ffi.new("int*")
        PLL_CodesPtrDAC = xrfdc._ffi.new("int*")
        ConfigPtrADC = xrfdc._ffi.new("int*")
        PLL_CodesPtrADC = xrfdc._ffi.new("int*")

        # initialize config structs for DAC and ADC
        xrfdc._lib.XRFdc_MultiConverter_Init(self.dac_sync_config, ConfigPtrDAC, PLL_CodesPtrDAC, 0)
        xrfdc._lib.XRFdc_MultiConverter_Init(self.adc_sync_config, ConfigPtrADC, PLL_CodesPtrADC, 0)
        
        # synchronize the MTS with the provided target latency
        self.syncMTS(dacTargetLatency, dacTileEnable, adcTargetLatency, adcTileEnable, verbose=verbose)
        
    def syncMTS(self, dacTargetLatency, dacTileEnable, adcTargetLatency, adcTileEnable, verbose=False):
        """
        Calls converter MTS sync function.

        Calls XRFdc_MultiConverter_Sync for the chosen converters with the given target latencies.
        
        Parameters
        ----------
        dacTargetLatency: int
            Target latency for DAC
        dacTileEnable: int
            0: disable all DAC tiles
            bit 1: enable tile0
            bit 2: enable tile1
            etc...
        adcTargetLatency: int
            Target latency for ADC
        adcTileEnable: int
            0: disable all ADC tiles
            bit 1: enable tile0
            bit 2: enable tile1
            etc...
        """
        # Synchronize DAC
        self.dac_sync_config.RefTile = 0x0
        self.dac_sync_config.Tiles = dacTileEnable
        self.dac_sync_config.SysRef_Enable = 1
        self.dac_sync_config.Target_Latency = dacTargetLatency 
        if dacTileEnable:
            status = xrfdc._lib.XRFdc_MultiConverter_Sync(self._instance, 
                                                           xrfdc._lib.XRFDC_DAC_TILE,
                                                           self.dac_sync_config) 
            self._syncReportDac(status, verbose=verbose)

        # Synchronize ADC
        self.adc_sync_config.RefTile = 0x0
        self.adc_sync_config.Tiles = adcTileEnable
        self.adc_sync_config.SysRef_Enable = 1
        self.adc_sync_config.Target_Latency = adcTargetLatency
        if adcTileEnable:
            status = xrfdc._lib.XRFdc_MultiConverter_Sync(self._instance, 
                                                          xrfdc._lib.XRFDC_ADC_TILE,
                                                          self.adc_sync_config)
            self._syncReportAdc(status, verbose=verbose)

    def sysrefDisable(self):
        """Disable RFDC SYSREF receive."""
        status = xrfdc._lib.XRFdc_MTS_Sysref_Config(self._instance, self.dac_sync_config, self.adc_sync_config, 0)
        print('disable sysref func status: ', status)
        return status

    def sysrefEnable(self):
        """Enable RFDC SYSREF receive"""
        status = xrfdc._lib.XRFdc_MTS_Sysref_Config(self._instance, self.dac_sync_config, self.adc_sync_config, 1)
        print('enable sysref func status: ', status)
        return status

    def _syncReportAdc(self, status, verbose):
        """Prints MTS report for ADC.
        
        It checks for errors using the status return of XRFdc_MultiConverter_Sync function
        and reports the contents of ADC sync config struct.
    
        Parameters
        ----------
        status: int
            Status return of XRFdc_MultiConverter_Sync function called for ADC
        """
        factor = xrfdc._ffi.new("unsigned int*")

        if status != xrfdc._lib.XRFDC_MTS_OK:
            self._MTS_Sync_Status_Msg(status)
        else:
            self._MTS_Sync_Status_Msg(status)
            
            if verbose:
                print("========== ADC Multi-Tile Sync Report ==========")
                for i in range(0,4):
                    if (1<<i) & self.adc_sync_config.Tiles:
                        xrfdc._lib.XRFdc_GetDecimationFactor(self._instance, i, 0, factor)
                        print("ADC{}: Latency(T1) = {}, Adjusted Delay Offset({}) = {}, Marker Delay = {}".format(i,
                                                                                                                  self.adc_sync_config.Latency[i],
                                                                                                                  factor[0],
                                                                                                                  self.adc_sync_config.Offset[i],
                                                                                                                  self.adc_sync_config.Marker_Delay))
                        print("=== MTS ADC Tile{} PLL Report ===".format(i))
                        print("    ADC{}: PLL DTC Code ={} ".format(i, self.adc_sync_config.DTC_Set_PLL.DTC_Code[i]))
                        print("    ADC{}: PLL Num Windows ={} ".format(i, self.adc_sync_config.DTC_Set_PLL.Num_Windows[i]))
                        print("    ADC{}: PLL Max Gap ={} ".format(i, self.adc_sync_config.DTC_Set_PLL.Max_Gap[i]))
                        print("    ADC{}: PLL Min Gap ={} ".format(i, self.adc_sync_config.DTC_Set_PLL.Min_Gap[i]))
                        print("    ADC{}: PLL Max Overlap ={} ".format(i, self.adc_sync_config.DTC_Set_PLL.Max_Overlap[i]))
                        print("=== MTS ADC Tile{} T1 Report ===".format(i))
                        print("    ADC{}: T1 DTC Code ={} ".format(i, self.adc_sync_config.DTC_Set_T1.DTC_Code[i]))
                        print("    ADC{}: T1 Num Windows ={} ".format(i, self.adc_sync_config.DTC_Set_T1.Num_Windows[i]))
                        print("    ADC{}: T1 Max Gap ={} ".format(i, self.adc_sync_config.DTC_Set_T1.Max_Gap[i]))
                        print("    ADC{}: T1 Min Gap ={} ".format(i, self.adc_sync_config.DTC_Set_T1.Min_Gap[i]))
                        print("    ADC{}: T1 Max Overlap ={}".format(i, self.adc_sync_config.DTC_Set_T1.Max_Overlap[i]))

                print("ADC Multi-Tile Synchronization is complete.")
                print("###############################################")
            
            
    def _syncReportDac(self, status, verbose):
        """Prints MTS report for DAC.
        
        It checks for errors using the status return of XRFdc_MultiConverter_Sync function
        and reports the contents of DAC sync config struct.
    
        Parameters
        ----------
        status: int
            Status return of XRFdc_MultiConverter_Sync function called for DAC
        """
        factor = xrfdc._ffi.new("unsigned int*")
        if status != xrfdc._lib.XRFDC_MTS_OK:
            self._MTS_Sync_Status_Msg(status)
        else:
            self._MTS_Sync_Status_Msg(status)

            if verbose:
                print("========== DAC Multi-Tile Sync Report ==========")
                for i in range(0,4):
                    if (1<<i) & self.dac_sync_config.Tiles:
                        xrfdc._lib.XRFdc_GetInterpolationFactor(self._instance, i, 0, factor)
                        print("DAC{}: Latency(T1) = {}, Adjusted Delay Offset({}) = {}, Marker Delay = {}".format(i,
                                                                                                              self.dac_sync_config.Latency[i],
                                                                                                              factor[0],
                                                                                                              self.dac_sync_config.Offset[i],
                                                                                                              self.dac_sync_config.Marker_Delay))
                        print("=== MTS DAC Tile{} PLL Report ===".format(i))
                        print("    DAC{}: PLL DTC Code ={} ".format(i, self.dac_sync_config.DTC_Set_PLL.DTC_Code[i]))
                        print("    DAC{}: PLL Num Windows ={} ".format(i, self.dac_sync_config.DTC_Set_PLL.Num_Windows[i]))
                        print("    DAC{}: PLL Max Gap ={} ".format(i, self.dac_sync_config.DTC_Set_PLL.Max_Gap[i]))
                        print("    DAC{}: PLL Min Gap ={} ".format(i, self.dac_sync_config.DTC_Set_PLL.Min_Gap[i]))
                        print("    DAC{}: PLL Max Overlap ={} ".format(i, self.dac_sync_config.DTC_Set_PLL.Max_Overlap[i]))
                        print("=== MTS DAC Tile{} T1 Report ===".format(i))
                        print("    DAC{}: T1 DTC Code ={} ".format(i, self.dac_sync_config.DTC_Set_T1.DTC_Code[i]))
                        print("    DAC{}: T1 Num Windows ={} ".format(i, self.dac_sync_config.DTC_Set_T1.Num_Windows[i]))
                        print("    DAC{}: T1 Max Gap ={} ".format(i, self.dac_sync_config.DTC_Set_T1.Max_Gap[i]))
                        print("    DAC{}: T1 Min Gap ={} ".format(i, self.dac_sync_config.DTC_Set_T1.Min_Gap[i]))
                        print("    DAC{}: T1 Max Overlap ={}".format(i, self.dac_sync_config.DTC_Set_T1.Max_Overlap[i]))

                print("DAC Multi-Tile Synchronization is complete.")
                print("###############################################")
        
    def printLatency(self):
        """Print latency and offset."""
        print('*** printing latency ***')
        for i in range(4):
            print("ADC Latency: "+str(self.adc_sync_config.Latency[i]))
            print("ADC offset: "+str(self.adc_sync_config.Offset[i]))
        print("*****")

    def _MTS_Sync_Status_Msg(self, status):
        """Checks for MTS error.
        
        Uses the status return of XRFdc_MultiConverter_Sync function to determine possible errors.
        Throws RuntimeError in case an error is found.
        
        Parameters
        ----------
        status: int
            Status return of XRFdc_MultiConverter_Sync function 
        """
        
        if status == xrfdc._lib.XRFDC_MTS_OK:
            print(_INFO  + " : Multi-Tile-Sync completed successfully.")

        else:
            if status & xrfdc._lib.XRFDC_MTS_TIMEOUT == xrfdc._lib.XRFDC_MTS_TIMEOUT:
                raise MtsTimeoutException
            if status & xrfdc._lib.XRFDC_MTS_NOT_SUPPORTED == xrfdc._lib.XRFDC_MTS_NOT_SUPPORTED:
                raise MtsNotSupportedException    
            if status & xrfdc._lib.XRFDC_MTS_DTC_INVALID == xrfdc._lib.XRFDC_MTS_DTC_INVALID:
                raise MtsDtcInvalidException    
            if status & xrfdc._lib.XRFDC_MTS_NOT_ENABLED == xrfdc._lib.XRFDC_MTS_NOT_ENABLED:
                raise MtsNotEnabledException    
            if status & xrfdc._lib.XRFDC_MTS_SYSREF_GATE_ERROR == xrfdc._lib.XRFDC_MTS_SYSREF_GATE_ERROR:
                raise MtsSysrefGateError    
            if status & xrfdc._lib.XRFDC_MTS_SYSREF_FREQ_NDONE == xrfdc._lib.XRFDC_MTS_SYSREF_FREQ_NDONE:
                raise MtsSysrefFreqNdoneException    
            if status & xrfdc._lib.XRFDC_MTS_BAD_REF_TILE == xrfdc._lib.XRFDC_MTS_BAD_REF_TILE:
                raise MtsBadRefTileException
        

# custom exceptions
class MtsTimeoutException(RuntimeError):
    def __init__(self):
        self.msg = "Multi-Tile-Sync did not complete successfully, due to a timeout."
        super().__init__(self.msg)

class MtsNotSupportedException(RuntimeError):
    def __init__(self):
        self.msg = "Multi-Tile-Sync not supported."
        super().__init__(self.msg)

class MtsDtcInvalidException(RuntimeError):
    def __init__(self):
        self.msg = "DTC invalid."
        super().__init__(self.msg)

class MtsNotEnabledException(RuntimeError):
    def __init__(self):
        self.msg = "Multi-Tile-Sync is not enabled."
        super().__init__(self.msg)

class MtsSysrefGateError(RuntimeError):
    def __init__(self):
        self.msg = "Sysref gate error."
        super().__init__(self.msg)

class MtsSysrefFreqNdoneException(RuntimeError):
    def __init__(self):
        self.msg = "Sysref frequency error."
        super().__init__(self.msg)

class MtsBadRefTileException(RuntimeError):
    def __init__(self):
        self.msg = "Bad reference tile."
        super().__init__(self.msg)