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
_INFO = "[" + _green + "INFO" + _black + "]"
_ERROR = "[" + _red + "ERROR" + _black + "]"

# Extend the CFFI with the local C-file 
_THIS_DIR = _THIS_DIR = os.path.dirname(__file__)
with open(os.path.join(_THIS_DIR, 'xrfdc_functions.c'), 'r') as f:
    header_text = f.read()
    
xrfdc._ffi.cdef(header_text)

# remove RFdc driver binding in order to bind RFdcMTS instead
RFdc.bindto = []

class RFdcMTS(RFdc):

    bindto = ["xilinx.com:ip:usp_rf_data_converter:2.6",
              "xilinx.com:ip:usp_rf_data_converter:2.4", 
              "xilinx.com:ip:usp_rf_data_converter:2.3"]

    def __init__(self, description):
        super().__init__(description)
        self.dac_sync_config = xrfdc._ffi.new("XRFdc_MultiConverter_Sync_Config*")
        self.adc_sync_config = xrfdc._ffi.new("XRFdc_MultiConverter_Sync_Config*")
        
    def autoRunMTS(self, dacTileEnable, adcTileEnable):
        """Let the driver handle the latency synchronization sequence."""
        if adcTileEnable:
            raise RuntimeError("Auto MTS sequencing for ADC tiles are not yet implemented!")
        
        self.initMTS(-1, dacTileEnable, -1, adcTileEnable)
        dacLatency = max(self.dac_sync_config.Latency)
        dacMargin = 16
        
        self.syncMTS(dacLatency+dacMargin, dacTileEnable, 0, adcTileEnable)
        
    def initMTS(self, dacTargetLatency, dacTileEnable, adcTargetLatency, adcTileEnable):
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
        self.syncMTS(dacTargetLatency, dacTileEnable, adcTargetLatency, adcTileEnable)
        
    def syncMTS(self, dacTargetLatency, dacTileEnable, adcTargetLatency, adcTileEnable):
        # Synchronize DAC
        self.dac_sync_config.RefTile = 0x0
        self.dac_sync_config.Tiles = dacTileEnable
        self.dac_sync_config.SysRef_Enable = 1
        self.dac_sync_config.Target_Latency = dacTargetLatency 
        if dacTileEnable:
            status = xrfdc._lib.XRFdc_MultiConverter_Sync(self._instance, 
                                                           xrfdc._lib.XRFDC_DAC_TILE,
                                                           self.dac_sync_config) 
            self._syncReportDac(status)

        # Synchronize ADC
        self.adc_sync_config.RefTile = 0x0
        self.adc_sync_config.Tiles = adcTileEnable
        self.adc_sync_config.SysRef_Enable = 1
        self.adc_sync_config.Target_Latency = adcTargetLatency
        if adcTileEnable:
            status = xrfdc._lib.XRFdc_MultiConverter_Sync(self._instance, 
                                                          xrfdc._lib.XRFDC_ADC_TILE,
                                                          self.adc_sync_config)
            self._syncReportAdc(status)

    def sysrefDisable(self):
        self.status3 = xrfdc._lib.XRFdc_MTS_Sysref_Config(self._instance, self._DAC_Sync_Config, self._ADC_Sync_Config, 0)
        print(self.status3)

    def sysrefEnable(self):
        self.status3 = xrfdc._lib.XRFdc_MTS_Sysref_Config(self._instance, self._DAC_Sync_Config, self._ADC_Sync_Config, 1)
        print(self.status3)

    def _syncReportAdc(self, status):
        factor = xrfdc._ffi.new("unsigned int*")

        if status != xrfdc._lib.XRFDC_MTS_OK:
            self._MTS_Sync_Status_Msg(status)
        else:
            self._MTS_Sync_Status_Msg(status)

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
            
            
    def _syncReportDac(self, status):
        factor = xrfdc._ffi.new("unsigned int*")
        if status != xrfdc._lib.XRFDC_MTS_OK:
            self._MTS_Sync_Status_Msg(status)
        else:
            self._MTS_Sync_Status_Msg(status)

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
        print('*** printing latency ***')
        for i in range(4):
            print("ADC Latency: "+str(self.adc_sync_config.Latency[i]))
            print("ADC offset: "+str(self.adc_sync_config.Offset[i]))
        print("*****")

    def _MTS_Sync_Status_Msg(self, status):
        
        if status == xrfdc._lib.XRFDC_MTS_OK:
            print(_INFO  + " : ADC Multi-Tile-Sync completed successfully.")
        elif status == xrfdc._lib.XRFDC_MTS_TIMEOUT:
            print(_ERROR + " : ADC Multi-Tile-Sync did not complete successfully, due to a timeout.")
        elif status == xrfdc._lib.XRFDC_MTS_NOT_SUPPORTED:
            print(_ERROR + " : ADC Multi-Tile-Sync not supported.")
        elif status == xrfdc._lib.XRFDC_MTS_DTC_INVALID:
            print(_ERROR + " : DTC invalid.")
        elif status == xrfdc._lib.XRFDC_MTS_NOT_ENABLED:
            print(_ERROR + " : ADC Multi-Tile-Sync is not enabled.")
        elif status == xrfdc._lib.XRFDC_MTS_SYSREF_GATE_ERROR:
            print(_ERROR + " : Sysref gate error.")
        elif status == xrfdc._lib.XRFDC_MTS_SYSREF_FREQ_NDONE:
            print(_ERROR + " : Sysref frequency error.")
        elif status == xrfdc._lib.XRFDC_MTS_BAD_REF_TILE:
            print(_ERROR + " : Bad reference tile.")
        else:
            print(_ERROR + " : ADC Multi-Tile-Sync did not complete successfully.")