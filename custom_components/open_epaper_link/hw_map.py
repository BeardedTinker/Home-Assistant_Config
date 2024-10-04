from typing import Dict, Tuple

HW_MAP: Dict[int, Tuple[str, int, int]] = {
    0: ["M2 1.54\"", 152, 152],
    1: ["M2 2.9\"",  296, 128],
    2: ["M2 4.2\"",  400, 300],
    5: ["M2 7.4\"",  640, 384],
    17: ["M2 2.9\" (NFC)", 296, 128],
    18: ["M2 4.2\" (NFC)",  400, 300],
    26: ["M2 7.4\" (outdated)",  640, 384],
    33: ["M2 2.9\"", 296, 128],
    38: ["M2 7.4 BW\"",  640, 384],
    39: ["M2 2.9 BW\"", 296, 128],
    45: ["M3 12.2\"",  960, 768],
    46: ["M3 9.7\"",  960, 672],
    47: ["M3 4.3\"",  522, 152],
    48: ["M3 1.6\"",  200, 200],
    49: ["M3 2.2\"",  296, 160],
    50: ["M3 2.6\"",  360, 184],
    51: ["M3 2.9\"",  384, 168],
    52: ["M3 4.2\"",  400, 300],
    53: ["M3 6.0\"",  600, 448],
    54: ["M3 7.5\"",  800, 480],
    67: ["M3 1.3\" Peghook",  144, 200],
    69: ["M3 2.2\" Lite",  250, 128],
    70: ["M3 2.2\" BW",  296, 160],
    84: ["HS BW 2.13\"",  256, 128],
    85: ["HS BWR 2.13\"",  256, 128],
    86: ["HS BWR 2.66\"",  296, 152],
    96: ["HS BWY 3.5\"",  384, 184],
    97: ["HS BWR 3.5\"",  384, 184],
    98: ["HS BW 3.5\"",  384, 184],
    102: ["HS BWY 7.5\"",  800, 480],
    103: ["HS BWY 2.0\"",  152, 200],
    128: ["Chroma 7.4\"", 640, 384],
    130: ["Chroma29 2.9\"", 296, 128],
    131: ["Chroma42 4\"", 400, 300],
    176: ["Gicisky BLE EPD BW 2.1\"",  212, 104],
    177: ["Gicisky BLE EPD BWR 2.13\"",  250, 128],
    178: ["Gicisky BLE EPD BW 2.9\"",  296, 128],
    179: ["Gicisky BLE EPD BWR 2.9\"",  296, 128],
    181: ["Gicisky BLE EPD BWR 4.2\"",  400, 300],
    186: ["Gicisky BLE TFT 2.13\"",  250, 132],
    191: ["Gicisky BLE Unknown",  0, 0],
    190: ["ATC MiThermometer BLE",  6, 8],
    224: ["AP display",  320, 170],
    225: ["AP display",  160, 80],
    226: ["LILYGO TPANEL",  480, 480],    
    240: ["Segmented",  0, 0]
}
def is_in_hw_map(hw_type: int) -> bool:
    return hw_type in HW_MAP

def get_hw_string(hw_type: int) -> str:
    return HW_MAP.get(hw_type, "NOT_IN_HW_MAP")[0]

def get_hw_dimensions(hw_type: int) -> Tuple[int, int]:
    return HW_MAP.get(hw_type)[1:]
