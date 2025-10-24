// Type alias test

using Timestamp = uint64
using Temperature = float32
using DeviceId = uint32

struct SensorReading
    Timestamp time
    Temperature value
    DeviceId device
