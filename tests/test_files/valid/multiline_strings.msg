// Valid - multiline strings in field and struct attributes

struct Documentation
    [attributes]
        description: """This struct demonstrates
        the use of multiline strings
        in attribute blocks"""
        version: "1.0"
    uint32 id
    string name
        description: """The name field
        can contain any string value"""
        maxLength: 256

struct SensorData
    float32 temperature
        unit: "celsius"
        description: """Temperature measurement
        Range: -40 to 85°C
        Accuracy: ±0.5°C"""
    float32 humidity
        unit: "%"
        range: "0-100"
        note: """Relative humidity
        Calibration required"""
