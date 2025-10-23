"""
Common geometry definitions
"""

struct Vector3
    float32 x @unit("m")
    float32 y @unit("m")
    float32 z @unit("m")

struct Quaternion
    float32 w
    float32 x
    float32 y
    float32 z
