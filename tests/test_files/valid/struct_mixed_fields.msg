// Struct with mixed field types and attributes

struct SensorData
    uint64 timestamp
    float32 temperature
        unit: "celsius"
        range: "-40.0 to 85.0"
    float32 pressure
        unit: "hPa"
    bool is_valid
