// Valid - inline attributes demonstration

struct GpsData
    // Inline attributes only
    GpsFixStatus status @description("GPS fix status"), @size(3), @encoding("utf-8")

    // Mix of inline and indented attributes
    float64 latitude @unit("degrees"), @range(-90)
        description: "Latitude coordinate"
        precision: 6

    float64 longitude @unit("degrees"), @range(-180)
        description: "Longitude coordinate"
        precision: 6

    // Indented only (backwards compatible)
    float32 altitude
        unit: "meters"
        description: "Altitude above sea level"

    // No attributes at all
    uint64 timestamp
