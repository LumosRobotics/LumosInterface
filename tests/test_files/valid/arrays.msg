// Array types test

struct ArrayTypes
    // Fixed size arrays
    array<uint8, 12> fixed_array
    array<float32, 3> coordinates

    // Dynamic arrays
    array<uint8> dynamic_data
    array<string> messages

    // Dynamic with max
    array<uint8, max=100> limited_data
