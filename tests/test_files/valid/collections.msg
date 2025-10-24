// Valid - collection types demonstration (array, matrix, tensor)

struct SensorData
    // Fixed size arrays
    array<uint8, 12> satellite_ids
    array<float32, 3> position_xyz

    // Dynamic 1D size (unbounded)
    array<uint8> data_payload
    array<string> error_messages

    // Static size arrays
    array<uint8, 100> other_data
    array<string, 50> log_entries

    // Matrix with static size
    matrix<uint8, 640, 480> camera_matrix

    // Dynamic with max constraint
    array<uint8, max=100> sensor_readings
    array<string, max=50> log_entries_max

    // Size arguments with ? means dynamic in that dimension
    matrix<uint8, ?, 480> camera_image
    tensor<float32, 100, ?, 3> voxel_grid
    tensor<float32, 10, 10, 10, 4> tensor_4d

    // Optional collections
    optional array<Vector3, 10> waypoints

    // Collections with inline attributes
    array<float32, 3> acceleration @unit("m/s^2"), @range(-10)

    // Collections with indented attributes
    matrix<float32, 4, 4> transform_matrix
        description: "Transformation matrix"
        coordinate_system: "world"

    // User-defined and qualified element types
    array<Position> path_history
    array<common::geometry::Vector3, 100> trajectory
