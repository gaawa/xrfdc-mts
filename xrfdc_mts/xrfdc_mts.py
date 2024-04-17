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
        
    def RunMTS(self, Target_Latency_DAC, Enable_Tile_DAC, Target_Latency_ADC, Enable_Tile_ADC):

        self._DAC_Sync_Config = xrfdc._ffi.new("XRFdc_MultiConverter_Sync_Config*")
        self._ADC_Sync_Config = xrfdc._ffi.new("XRFdc_MultiConverter_Sync_Config*")

        ConfigPtr = xrfdc._ffi.new("int*")
        PLL_CodesPtr = xrfdc._ffi.new("int*")
        RefTile = xrfdc._ffi.new("u32*")
        
        # Run MTS on DACs
        xrfdc._lib.XRFdc_MultiConverter_Init(self._DAC_Sync_Config, ConfigPtr, PLL_CodesPtr, 0)
        
        self._DAC_Sync_Config.RefTile = 0x0
        self._DAC_Sync_Config.Tiles = Enable_Tile_DAC
        self._DAC_Sync_Config.SysRef_Enable = 1
        self._DAC_Sync_Config.Target_Latency = Target_Latency_DAC 
        
        if Enable_Tile_DAC:
            print(self._DAC_Sync_Config.Target_Latency)
            self.status1 = xrfdc._lib.XRFdc_MultiConverter_Sync(self._instance, xrfdc._lib.XRFDC_DAC_TILE,self._DAC_Sync_Config) 
            self._SyncReport("DAC", self.status1)
            

        self.printLatency()

        time.sleep(0.5)
        
        # Run MTS on ADCs
        xrfdc._lib.XRFdc_MultiConverter_Init(self._ADC_Sync_Config, ConfigPtr, PLL_CodesPtr, 0)
        
        self._ADC_Sync_Config.RefTile = 0x0
        self._ADC_Sync_Config.Tiles = Enable_Tile_ADC
        self._ADC_Sync_Config.SysRef_Enable = 1
        self._ADC_Sync_Config.Target_Latency = Target_Latency_ADC
        
        if Enable_Tile_ADC:
            print(self._ADC_Sync_Config.Target_Latency)
            self.status1 = xrfdc._lib.XRFdc_MultiConverter_Sync(self._instance, xrfdc._lib.XRFDC_ADC_TILE,self._ADC_Sync_Config)
            self._SyncReport("ADC", self.status1)


    def _SyncReport(self, converter, status):

        if isinstance(converter,str):
            pass
        else:
            print(_ERROR + " : Argument converter must be a string!")
            return

        factor = xrfdc._ffi.new("unsigned int*")

        if "ADC" == converter:
            if status != xrfdc._lib.XRFDC_MTS_OK:
                self._MTS_Sync_Status_Msg(status)
            else:
                self._MTS_Sync_Status_Msg(status)

                print("========== ADC Multi-Tile Sync Report ==========")
                for i in range(0,4):
                    if (1<<i) & self._ADC_Sync_Config.Tiles:
                        xrfdc._lib.XRFdc_GetDecimationFactor(self._instance, i, 0, factor)
                        print("ADC{}: Latency(T1) = {}, Adjusted Delay Offset({}) = {}, Marker Delay = {}".format(i, \
                                                                                                                  self._ADC_Sync_Config.Latency[i], \
                                                                                                                  factor[0], \
                                                                                                                  self._ADC_Sync_Config.Offset[i], \
                                                                                                                  self._ADC_Sync_Config.Marker_Delay))
                        print("=== MTS ADC Tile{} PLL Report ===".format(i))
                        print("    ADC{}: PLL DTC Code ={} ".format(i, self._ADC_Sync_Config.DTC_Set_PLL.DTC_Code[i]))
                        print("    ADC{}: PLL Num Windows ={} ".format(i, self._ADC_Sync_Config.DTC_Set_PLL.Num_Windows[i]))
                        print("    ADC{}: PLL Max Gap ={} ".format(i, self._ADC_Sync_Config.DTC_Set_PLL.Max_Gap[i]))
                        print("    ADC{}: PLL Min Gap ={} ".format(i, self._ADC_Sync_Config.DTC_Set_PLL.Min_Gap[i]))
                        print("    ADC{}: PLL Max Overlap ={} ".format(i, self._ADC_Sync_Config.DTC_Set_PLL.Max_Overlap[i]))
                        print("=== MTS ADC Tile{} T1 Report ===".format(i))
                        print("    ADC{}: T1 DTC Code ={} ".format(i, self._ADC_Sync_Config.DTC_Set_T1.DTC_Code[i]))
                        print("    ADC{}: T1 Num Windows ={} ".format(i, self._ADC_Sync_Config.DTC_Set_T1.Num_Windows[i]))
                        print("    ADC{}: T1 Max Gap ={} ".format(i, self._ADC_Sync_Config.DTC_Set_T1.Max_Gap[i]))
                        print("    ADC{}: T1 Min Gap ={} ".format(i, self._ADC_Sync_Config.DTC_Set_T1.Min_Gap[i]))
                        print("    ADC{}: T1 Max Overlap ={}".format(i, self._ADC_Sync_Config.DTC_Set_T1.Max_Overlap[i]))

                print("ADC Multi-Tile Synchronization is complete.")
                print("###############################################")
            
            ADC_Latencies = []
            for i in range(2):
                ADC_Latencies.append(self._ADC_Sync_Config.Latency[i])

            return ADC_Latencies
        
        elif "DAC" == converter:

            if status != xrfdc._lib.XRFDC_MTS_OK:
                self._MTS_Sync_Status_Msg(status)
            else:
                self._MTS_Sync_Status_Msg(status)

                print("========== DAC Multi-Tile Sync Report ==========")
                for i in range(0,4):
                    if (1<<i) & self._DAC_Sync_Config.Tiles:
                        xrfdc._lib.XRFdc_GetDecimationFactor(self._instance, i, 0, factor)
                        print("DAC{}: Latency(T1) = {}, Adjusted Delay Offset({}) = {}, Marker Delay = {}".format(i, \
                                                                                                                  self._DAC_Sync_Config.Latency[i], \
                                                                                                                  factor[0], \
                                                                                                                  self._DAC_Sync_Config.Offset[i], \
                                                                                                                  self._DAC_Sync_Config.Marker_Delay))
                        print("=== MTS DAC Tile{} PLL Report ===".format(i))
                        print("    DAC{}: PLL DTC Code ={} ".format(i, self._DAC_Sync_Config.DTC_Set_PLL.DTC_Code[i]))
                        print("    DAC{}: PLL Num Windows ={} ".format(i, self._DAC_Sync_Config.DTC_Set_PLL.Num_Windows[i]))
                        print("    DAC{}: PLL Max Gap ={} ".format(i, self._DAC_Sync_Config.DTC_Set_PLL.Max_Gap[i]))
                        print("    DAC{}: PLL Min Gap ={} ".format(i, self._DAC_Sync_Config.DTC_Set_PLL.Min_Gap[i]))
                        print("    DAC{}: PLL Max Overlap ={} ".format(i, self._DAC_Sync_Config.DTC_Set_PLL.Max_Overlap[i]))
                        print("=== MTS DAC Tile{} T1 Report ===".format(i))
                        print("    DAC{}: T1 DTC Code ={} ".format(i, self._DAC_Sync_Config.DTC_Set_T1.DTC_Code[i]))
                        print("    DAC{}: T1 Num Windows ={} ".format(i, self._DAC_Sync_Config.DTC_Set_T1.Num_Windows[i]))
                        print("    DAC{}: T1 Max Gap ={} ".format(i, self._DAC_Sync_Config.DTC_Set_T1.Max_Gap[i]))
                        print("    DAC{}: T1 Min Gap ={} ".format(i, self._DAC_Sync_Config.DTC_Set_T1.Min_Gap[i]))
                        print("    DAC{}: T1 Max Overlap ={}".format(i, self._DAC_Sync_Config.DTC_Set_T1.Max_Overlap[i]))

                print("DAC Multi-Tile Synchronization is complete.")
                print("###############################################")
            
            DAC_Latencies = []
            for i in range(2):
                DAC_Latencies.append(self._DAC_Sync_Config.Latency[i])

            return DAC_Latencies

        else:
            print(_ERROR + " : " + converter + " is not a valid converter argument!")

    def printLatency(self):
        for i in range(4):
            print("ADC Latency: "+str(self._ADC_Sync_Config.Latency[i]))
            print("ADC offset: "+str(self._ADC_Sync_Config.Offset[i]))
        print("*****")

    def _MTS_Sync_Status_Msg(self, status):
        
        if status == xrfdc._lib.XRFDC_MTS_OK:
            print(_INFO + " : ADC Multi-Tile-Sync completed successfully.")
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