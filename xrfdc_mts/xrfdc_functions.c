/******************************************************************************
* C-Code API extension for MTS operation.
* Taken from: https://discuss.pynq.io/t/enabling-mts/4425/6
******************************************************************************/



// MTS related data structures
/**
 * MTS DTC Settings.
 */
typedef struct {
	u32 RefTile;
	u32 IsPLL;
	int Target[4];
	int Scan_Mode;
	int DTC_Code[4];
	int Num_Windows[4];
	int Max_Gap[4];
	int Min_Gap[4];
	int Max_Overlap[4];
} XRFdc_MTS_DTC_Settings;

/**
 * MTS Sync Settings.
 */
typedef struct {
	u32 RefTile;
	u32 Tiles;
	int Target_Latency;
	int Offset[4];
	int Latency[4];
	int Marker_Delay;
	int SysRef_Enable;
	XRFdc_MTS_DTC_Settings DTC_Set_PLL;
	XRFdc_MTS_DTC_Settings DTC_Set_T1;
} XRFdc_MultiConverter_Sync_Config;

/**
 * MTS Marker Struct.
 */
typedef struct {
	u32 Count[4];
	u32 Loc[4];
} XRFdc_MTS_Marker;


// MTS related macros
#define XRFDC_MTS_SYSREF_DISABLE 0U
#define XRFDC_MTS_SYSREF_ENABLE 1U
#define XRFDC_MTS_SCAN_INIT 0U
#define XRFDC_MTS_SCAN_RELOAD 1U

/* MTS Error Codes */
#define XRFDC_MTS_OK 0U
#define XRFDC_MTS_NOT_SUPPORTED 1U
#define XRFDC_MTS_TIMEOUT 2U
#define XRFDC_MTS_MARKER_RUN 4U
#define XRFDC_MTS_MARKER_MISM 8U
#define XRFDC_MTS_DELAY_OVER 16U
#define XRFDC_MTS_TARGET_LOW 32U
#define XRFDC_MTS_IP_NOT_READY 64U
#define XRFDC_MTS_DTC_INVALID 128U
#define XRFDC_MTS_NOT_ENABLED 512U
#define XRFDC_MTS_SYSREF_GATE_ERROR 2048U
#define XRFDC_MTS_SYSREF_FREQ_NDONE 4096U
#define XRFDC_MTS_BAD_REF_TILE 8192U


// MTS related function prototypes
u32 XRFdc_MTS_Sysref_Config(XRFdc *InstancePtr, XRFdc_MultiConverter_Sync_Config *DACSyncConfigPtr, XRFdc_MultiConverter_Sync_Config *ADCSyncConfigPtr, u32 SysRefEnable);
u32 XRFdc_MultiConverter_Init(XRFdc_MultiConverter_Sync_Config *ConfigPtr, int *PLL_CodesPtr, int *T1_CodesPtr, u32 RefTile);
u32 XRFdc_MultiConverter_Sync(XRFdc *InstancePtr, u32 Type, XRFdc_MultiConverter_Sync_Config *ConfigPtr);
u32 XRFdc_GetMTSEnable(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, u32 *EnablePtr);
u32 XRFdc_GetMasterTile(XRFdc *InstancePtr, u32 Type);
u32 XRFdc_GetSysRefSource(XRFdc *InstancePtr, u32 Type);
u32 XRFdc_MTS_Dtc_Scan(XRFdc *InstancePtr, u32 Type, u32 Tile_Id, XRFdc_MTS_DTC_Settings *SettingsPtr);
