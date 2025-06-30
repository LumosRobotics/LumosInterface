import /common/constants.msg
import /common/geometry.msg

struct GpsFix @rate_hz(10)
    float64 latitude     @unit("deg") @min(-90) @max(90)
    float64 longitude    @unit("deg") @min(-180) @max(180)
    float32 altitude     @unit("m") @optional
    uint8 satellites     @max(MAX_SATELLITES)
    GpsFixStatus status
