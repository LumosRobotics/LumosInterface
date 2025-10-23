import common/geometry // Only way to import, always import by path, and never by overridden namespace
import common/constants

using namespace common::geometry // Removes the need to prefix with 'common::geometry::'
namespace cg = common::geometry // Creates an alias for the namespace

// Constants
const uint8 MAX_SATELLITES = 12
const float32 EARTH_RADIUS_M = 6371000.0
const uint8 VERSION = 1

using GPSCoordinate = float64
using Timestamp = uint64
using DeviceId = uint32

common::constants::MAX_SATELLITES // Can be used to access constants from imported namespaces

// Comments should be with // and /* */

// Enum values can be assigned or omitted
enum GpsFixStatus
    NO_FIX = 0
    FIX = 1
    DGPS = 2
    RTK = 3

/*
This is a multiline comment
describing the GPS enum.
It can span multiple lines.
*/

struct BaseStruct
    float some_value = 1
    string some_string = 2

// Struct
@attribute0, @attribute2("hello")
struct Position : BaseStruct // Inheritance
    float64 lat
        // Brackets for field attributes are optional, can be done with 
        description: "Longitude in degrees"
        unit: "deg"
    float64 lon
        description: """Latitude in degrees
        This description is multiline."""
        unit: "deg"
    GpsFixStatus gps_fix_status @description("Status of the GPS fix") @size(3) @encoding("utf-8")
    GpsFixStatus gps_fix_status2
    {
        description: "Status of the GPS fix"
        size: 3
        encoding: "utf-8"
    } 
    common::geometry::Vector3 position
    // Fixed size
    array<uint8, 12> satellite_ids
    array<float32, 3> position_xyz

    // Dynamic
    array<uint8> data_payload
    array<string> error_messages

    // Dynamic with max
    array<uint8, max=100> sensor_readings
    array<string, max=50> log_entries

    matrix<uint8, ?, 480> camera_image
    tensor<float32, 100, 100, 3> voxel_grid
    optional tensor<float32, 10, 10, 10, 4> tensor_4d

// Interface
interface GpsInfo
    Position pos
    uint8 satellite_count
    GpsFixStatus gps_fix_status2
