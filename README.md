# `xrfdc-mts` Package

This package extends the PYNQ driver for the RFSoC RF Data Converter IP  (https://github.com/Xilinx/PYNQ/tree/master/sdbuild/packages/xrfdc) with MTS functionalities.

## Usage
This package wrapps the `xrfdc`package.
All public objects of the `xrfdc` package are exposed in this package.  
Assuming the proper hex register files for on-board clock-tree is available and the SYSREF capture was correctly designed, the initiation of MTS can be done in the following steps.

1. Configure the clock-tree.
    Configure the on-board clock generators with the proper hex register file. These can be generated using [TICS-PRO](https://www.ti.com/tool/TICSPRO-SW).
    Either the [`xrfclk`](https://github.com/Xilinx/PYNQ/tree/master/sdbuild/packages/xrfclk/package) provided by PYNQ or its wrapper [`xrfclk-readfile`](https://github.com/gaawa/xrfclk-fileread) package needs to be used to load the hex register values to clock the clock chips.
    ```python
    import xrfclk_readfile
    
    xrfclf_readfile.set_ref_clks_fr(lmk_file='LMK_config.txt', lmx_file='LMX_config.txt')
    ```

1. Load the overlay.  
    The RFDC will be bound to the `RFdcMTS` class of `xrfdc-mts` package.
    ```python
    import xrfdc_mts 
    from pynq import Overlay

    ol = Overlay('example_overlay.bit')
    rfdc = ol.usp_rf_data_converter_0  # instance of RFdcMTS class in xrfdc-mts package.
    ```

1. Setup MTS.  
    The `autoRunMTS()` method of `RFdcMTS` object will automatically configure the tiles with the appropriate target delay.
    ```python
    dacTileEnable = 0x3  # enables DAC tile0 and tile1.
    adcTileEnable = 0x0  # disables all ADC tiles.
    rfdc.autoRunMTS(dacTileEnable, adcTileEnable)
    ```
    If desired, the MTS can also be setup manually using `initMTS()` and `syncMTS()` methods. More details in their docstrings.
    

1. Start up synchronized operation.  
    Change the update event type of all converter blocks to SYSREF. Converter configuration are then updated in sync with the SYSREF.
    ```python
    # Set update event to SYSREF
    rfdc.dac_tiles[0].blocks[0].MixerSettings['EventSource'] = xrfdc_mts.EVENT_SRC_SYSREF
    ...
    ```
    In order to reconfigure the converters, first disable RFDC SYSREF receive, arm the converters with the new config and then re-enable SYSREF receive.
    ```
    rfdc.sysrefDisable()

    rfdc.dac_tiles[0].blocks[0].MixerSettings['Freq'] = mixerFreq
    rfdc.dac_tiles[0].blocks[0].ResetNCOPhase()
    ...
    
    rfdc.sysrefEnable()
    ```

## Credits 
https://discuss.pynq.io/t/enabling-mts/4425  
https://github.com/Xilinx/RFSoC-MTS  
https://support.xilinx.com/s/question/0D54U00005eazmiSAA/multitile-synchronization-for-the-adcs-runs-successfully-on-tthe-zcu111-but-the-phase-differences-between-tiles-are-random-with-each-mts-run-and-reboot?language=en_US
