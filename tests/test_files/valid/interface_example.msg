// Valid - interface type demonstration

// Interface is identical to struct, just different keyword
interface Position
    [attributes]
        version: "1.0"
        coordinate_system: "WGS84"

    float64 lat : 0
        description: "Latitude in degrees"
        unit: "deg"
    float64 lon : 1
        description: """Longitude in degrees
        This description is multiline."""
        unit: "deg"
    optional float64 altitude : 2
        unit: "meters"

// Interface with all features
interface SensorData
    uint32 id : 0 @primary(true)
    optional float64 temperature : 1
    array<uint8, 100> raw_data : 2
    Vector3 velocity : 3
    common::geometry::Quaternion orientation : 4

// Can mix struct and interface in same file
struct Config
    string name
    uint32 version

interface Message
    uint32 id
    string payload
