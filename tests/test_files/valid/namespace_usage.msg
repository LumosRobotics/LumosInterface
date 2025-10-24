// Valid - namespace features demonstration

import common/geometry

// Import all types from common::geometry namespace
using namespace common::geometry

// Create short alias for common::geometry
namespace cg = common::geometry

struct Transform
    // Simple type name (available via 'using namespace')
    Vector3 position

    // Aliased namespace
    cg::Vector3 velocity

    // Fully qualified type name
    common::geometry::Quaternion orientation

    // Primitive types still work
    float64 timestamp
