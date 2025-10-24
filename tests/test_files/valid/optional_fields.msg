// Valid - optional field modifier demonstration

struct Position
    [attributes]
        attribute0: true
        attribute2: "hello"

    // Required field
    uint32 id

    // Optional primitive field
    optional float64 latitude

    // Optional with inline attributes
    optional float64 longitude @unit("degrees"), @range(-180)

    // Optional with indented attributes
    optional float32 altitude
        unit: "meters"
        description: "Altitude above sea level"

    // Optional user-defined type
    optional Vector3 velocity

    // Optional qualified type with both attribute types
    optional common::geometry::Quaternion orientation @default("identity")
        description: "Optional orientation"
