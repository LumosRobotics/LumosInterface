// Interface definition test

struct Position
    float64 x
    float64 y

interface RobotStatus
    Position pos
    uint8 battery_level
    bool is_moving
