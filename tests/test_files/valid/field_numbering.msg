// Valid - field numbering demonstration

// Numbered struct (backwards compatible)
struct Position
    float64 lat : 0
        description: "Latitude in degrees"
        unit: "deg"
    float64 lon : 1
        description: """Longitude in degrees
        This description is multiline."""
        unit: "deg"
    optional float64 altitude : 2
        unit: "meters"

// Sparse numbering (with gaps for future/deleted fields)
struct SensorData
    uint32 id : 0
    // Field 1-4 reserved for future use
    array<uint8, 100> raw_data : 5
    // Field 6 was deleted, don't reuse
    float64 timestamp : 7
    optional string metadata : 10

// Unordered numbering (any order allowed)
struct Config
    string name : 100
    uint32 version : 1
    bool enabled : 50
    array<string, max=10> tags : 25

// Unnumbered struct (no backwards compatibility)
struct SimpleData
    uint32 id
    float64 value
    string name

// Mixed features with numbering
struct ComplexData
    optional uint32 id : 0 @primary(true)
    Vector3 position : 1
    common::geometry::Quaternion rotation : 2
    array<float32, 3> velocity : 3 @unit("m/s")
    matrix<float32, 4, 4> transform : 4
        description: "Transformation matrix"
    tensor<float32, 10, 10, 10> grid : 5
