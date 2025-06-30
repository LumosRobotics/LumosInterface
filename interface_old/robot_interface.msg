import /sensor/camera.msg
import /sensor/gps.msg

interface /camera/left/image
    Image img

interface /camera/left/info
    CameraInfo intrinsics

interface /gps/fix
    GpsFix fix
