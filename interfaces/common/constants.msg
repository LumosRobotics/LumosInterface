const uint8 MAX_SATELLITES = 12
const float32 EARTH_RADIUS_M = 6371000.0

enum GpsFixStatus
    NO_FIX = 0
    FIX = 1
    DGPS = 2
    RTK = 3
