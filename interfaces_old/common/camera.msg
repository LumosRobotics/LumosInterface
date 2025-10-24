import /common/geometry.msg

enum CameraMode
    OFF = 0
    MONO = 1
    STEREO = 2

bitfield CameraFlags : uint8
    HDR_ENABLED = 0
    AUTO_EXPOSURE = 1
    STABILIZED = 2

struct CameraInfo
    uint32 width
    uint32 height
    float32 fx @unit("px")
    float32 fy @unit("px")
    float32 cx @unit("px")
    float32 cy @unit("px")
    CameraMode mode
    CameraFlags flags

struct Image
    uint64 timestamp
    array<uint8, 3> data @unit("byte")
    vector<uint8> data @unit("byte")
