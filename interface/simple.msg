import /common/geometry.msg

# Constants
const uint8 MAX_SATELLITES = 12
const float32 EARTH_RADIUS_M = 6371000.0
const uint8 VERSION = 1

enum GpsFixStatus
    NO_FIX = 0
    FIX = 1
    DGPS = 2
    RTK = 3

"""
This is a multiline comment
describing the GPS enum.
It can span multiple lines.
"""

# Struct
struct Position
    float64 lat
    float64 lon
    GpsFixStatus gps_fix_status
    Vectord3 direction

# Interface
interface GpsInfo
    Position pos
    uint8 satellite_count
    GpsFixStatus gps_fix_status2
