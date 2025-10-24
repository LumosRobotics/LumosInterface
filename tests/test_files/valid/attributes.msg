// Attributes test

@deprecated
@version("1.0")
struct AttributedStruct
    float64 lat
        description: "Latitude in degrees"
        unit: "deg"
    float64 lon
    {
        description: "Longitude in degrees"
        unit: "deg"
    }
