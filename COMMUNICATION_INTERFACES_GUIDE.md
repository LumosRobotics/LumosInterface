# Communication Interfaces: Encoding/Decoding Requirements

## Overview

This document analyzes common communication interfaces used in embedded systems, robotics, and industrial applications. For each interface, we detail the relevant attributes needed for proper message encoding, decoding, and validation.

---

## Table of Contents

1. [CAN (Controller Area Network)](#can-controller-area-network)
2. [Ethernet](#ethernet)
3. [TCP/IP](#tcpip)
4. [UDP/IP](#udpip)
5. [UART (Serial)](#uart-serial)
6. [RS-485](#rs-485)
7. [SPI (Serial Peripheral Interface)](#spi-serial-peripheral-interface)
8. [I2C](#i2c)
9. [USB](#usb)
10. [Modbus](#modbus)
11. [MQTT](#mqtt)
12. [DDS (Data Distribution Service)](#dds-data-distribution-service)
13. [WebSocket](#websocket)
14. [Comparison Matrix](#comparison-matrix)

---

## CAN (Controller Area Network)

### Overview
CAN is a multi-master serial bus standard for connecting electronic control units (ECUs). Widely used in automotive, industrial automation, and medical equipment.

### Physical Characteristics
- **Speed**: 10 Kbps - 1 Mbps (CAN 2.0), up to 5 Mbps (CAN-FD)
- **Max Distance**: 40m @ 1Mbps, 1000m @ 50Kbps
- **Topology**: Bus with twisted pair
- **Max Payload**: 8 bytes (CAN 2.0), 64 bytes (CAN-FD)

### Required Message-Level Attributes

```yaml
can_message:
  id:                    # Message identifier
    type: integer
    required: true
    range: [0, 0x7FF]    # Standard 11-bit (0x1FFFFFFF for extended 29-bit)
    description: "CAN arbitration ID"

  extended:              # Use extended 29-bit ID
    type: boolean
    default: false

  cycle_time:            # Periodic transmission interval
    type: integer
    unit: milliseconds
    description: "Message transmission period (0 = event-driven)"

  dlc:                   # Data Length Code
    type: integer
    range: [0, 8]        # [0, 64] for CAN-FD
    default: 8

  can_fd:                # Enable CAN-FD mode
    type: boolean
    default: false
```

### Required Field-Level Attributes

```yaml
can_signal:
  start_bit:             # Starting bit position in message
    type: integer
    required: true
    range: [0, 63]       # [0, 511] for CAN-FD

  length:                # Signal length in bits
    type: integer
    required: true
    range: [1, 64]

  byte_order:            # Endianness
    type: enum
    values: [little_endian, big_endian, motorola, intel]
    default: little_endian

  value_type:            # How to interpret raw bits
    type: enum
    values: [unsigned, signed, ieee_float, ieee_double]
    default: unsigned

  scale:                 # Physical = (Raw * scale) + offset
    type: float
    required: true
    description: "Scaling factor for physical value"

  offset:                # Physical value offset
    type: float
    default: 0.0

  min:                   # Minimum physical value
    type: float
    required: true

  max:                   # Maximum physical value
    type: float
    required: true

  unit:                  # Physical unit
    type: string
    examples: ["km/h", "rpm", "degC", "bar"]

  initial_value:         # Default/initial value
    type: float
    description: "Value to use before first valid message"
```

### Rationale

- **ID + Extended**: Required for message arbitration and priority
- **Start Bit + Length**: CAN signals can be bit-packed at arbitrary positions
- **Byte Order**: Different ECUs may use different endianness (Intel vs Motorola)
- **Scale/Offset**: CAN signals are typically integers representing physical values
- **Min/Max**: Required for validation and for determining raw integer range
- **Cycle Time**: Important for bandwidth analysis and timing validation

### Example

```
struct VehicleSpeed
    [attributes]
        can_message:
            id: 0x123
            cycle_time: 100
            extended: false

    float32 speed
        can_signal:
            start_bit: 0
            length: 16
            byte_order: little_endian
            scale: 0.01
            offset: 0.0
            min: 0.0
            max: 250.0
            unit: "km/h"
```

---

## Ethernet

### Overview
Physical and data link layer protocol for local area networks. Forms the foundation for higher-level protocols like TCP/IP.

### Physical Characteristics
- **Speed**: 10 Mbps - 400 Gbps
- **Max Distance**: 100m (twisted pair), 40km+ (fiber)
- **Topology**: Star (switched)
- **Frame Size**: 64 - 1518 bytes (standard), up to 9000 bytes (jumbo frames)

### Required Message-Level Attributes

```yaml
ethernet_frame:
  ethertype:             # Protocol identifier
    type: integer
    required: true
    range: [0x0600, 0xFFFF]
    examples:
      - 0x0800: "IPv4"
      - 0x86DD: "IPv6"
      - 0x8100: "VLAN"

  vlan_id:               # Virtual LAN identifier
    type: integer
    range: [0, 4095]
    description: "802.1Q VLAN tag"

  priority:              # 802.1p priority
    type: integer
    range: [0, 7]
    description: "Quality of Service priority"

  destination_mac:       # Destination MAC address
    type: string
    pattern: "^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"
    description: "FF:FF:FF:FF:FF:FF for broadcast"

  multicast:             # Enable multicast
    type: boolean
    default: false
```

### Required Field-Level Attributes

```yaml
ethernet_field:
  offset:                # Byte offset in payload
    type: integer
    required: true

  byte_order:            # Endianness (network byte order = big endian)
    type: enum
    values: [network, host]
    default: network
    description: "network = big endian"
```

### Rationale

- **EtherType**: Identifies higher-level protocol for proper demultiplexing
- **VLAN ID**: Essential for network segmentation and isolation
- **Priority**: QoS for time-sensitive data (e.g., real-time control)
- **Byte Order**: Network protocols typically use big-endian

### Example

```
struct RobotState
    [attributes]
        ethernet_frame:
            ethertype: 0x88B5  # IEEE 1588 PTP
            vlan_id: 100
            priority: 6  # High priority for control data

    uint64 timestamp
        ethernet_field:
            offset: 0
            byte_order: network
```

---

## TCP/IP

### Overview
Reliable, ordered, connection-oriented transport protocol over IP networks. Guarantees delivery and correct ordering.

### Physical Characteristics
- **Speed**: Depends on underlying network
- **Max Distance**: Global (internet-scale)
- **Reliability**: Guaranteed delivery with retransmission
- **Overhead**: 20-60 bytes per packet (IP + TCP headers)

### Required Message-Level Attributes

```yaml
tcp_connection:
  port:                  # TCP port number
    type: integer
    required: true
    range: [1, 65535]
    description: "Well-known ports: 1-1023, registered: 1024-49151"

  keepalive:             # Enable TCP keepalive
    type: boolean
    default: true

  keepalive_interval:    # Keepalive probe interval
    type: integer
    unit: seconds
    default: 60

  timeout:               # Connection timeout
    type: integer
    unit: seconds
    default: 30

  nodelay:               # Disable Nagle's algorithm
    type: boolean
    default: false
    description: "Set to true for low-latency applications"

  buffer_size:           # Socket buffer size
    type: integer
    unit: bytes
    default: 65536
```

### Required Field-Level Attributes

```yaml
tcp_field:
  encoding:              # Wire encoding format
    type: enum
    values: [binary, json, protobuf, msgpack, cbor]
    default: binary

  byte_order:            # For binary encoding
    type: enum
    values: [big_endian, little_endian]
    default: big_endian

  compression:           # Compression algorithm
    type: enum
    values: [none, gzip, lz4, zstd]
    default: none
```

### Rationale

- **Port**: Required for establishing connections
- **Keepalive**: Detects broken connections in long-lived sessions
- **NoDelay**: Critical for real-time applications (disables packet coalescing)
- **Buffer Size**: Affects throughput and memory usage
- **Encoding**: Different applications have different serialization needs

### Example

```
struct TelemetryStream
    [attributes]
        tcp_connection:
            port: 5000
            nodelay: true  # Low latency for real-time data
            keepalive: true
            keepalive_interval: 30

    uint64 timestamp
    float32 temperature
    float32 pressure
        tcp_field:
            encoding: msgpack  # Efficient binary encoding
            compression: lz4   # Fast compression
```

---

## UDP/IP

### Overview
Connectionless, unreliable transport protocol. Lower overhead than TCP, suitable for real-time streaming where occasional packet loss is acceptable.

### Physical Characteristics
- **Speed**: Depends on underlying network
- **Max Distance**: Global (internet-scale)
- **Reliability**: No delivery guarantee
- **Overhead**: 8 bytes (UDP header) + 20 bytes (IP header)

### Required Message-Level Attributes

```yaml
udp_message:
  port:                  # UDP port number
    type: integer
    required: true
    range: [1, 65535]

  multicast_group:       # Multicast IP address
    type: string
    pattern: "^(22[4-9]|23[0-9])\\.(\\d{1,3}\\.){2}\\d{1,3}$"
    description: "224.0.0.0 - 239.255.255.255"

  ttl:                   # Time-to-live / hop limit
    type: integer
    range: [1, 255]
    default: 64

  broadcast:             # Enable broadcast
    type: boolean
    default: false

  max_packet_size:       # Maximum datagram size
    type: integer
    unit: bytes
    range: [1, 65507]    # 65535 - 20 (IP) - 8 (UDP)
    default: 1472        # Typical MTU-safe size

  rate_limit:            # Maximum messages per second
    type: integer
    description: "For bandwidth control"
```

### Required Field-Level Attributes

```yaml
udp_field:
  sequence_number:       # For detecting packet loss
    type: boolean
    default: true
    description: "Automatically add sequence counter"

  timestamp:             # For latency measurement
    type: boolean
    default: true

  checksum:              # Additional integrity check
    type: enum
    values: [none, crc16, crc32, md5]
    default: crc32

  encoding:              # Wire format
    type: enum
    values: [binary, json, msgpack]
    default: binary
```

### Rationale

- **Port**: Required for addressing
- **Multicast**: Efficient one-to-many communication
- **Max Packet Size**: Avoid IP fragmentation for reliability
- **Sequence Number**: Detect packet loss and reordering
- **Rate Limit**: Prevent network congestion
- **Checksum**: Additional error detection beyond UDP's basic checksum

### Example

```
struct SensorData
    [attributes]
        udp_message:
            port: 6000
            multicast_group: "239.255.0.1"
            max_packet_size: 1400
            rate_limit: 100  # 100 Hz

    uint32 sequence
        udp_field:
            sequence_number: true

    uint64 timestamp
        udp_field:
            timestamp: true

    float32 value
```

---

## UART (Serial)

### Overview
Universal Asynchronous Receiver-Transmitter. Simple point-to-point serial communication, widely used in embedded systems.

### Physical Characteristics
- **Speed**: 300 bps - 921,600 bps (higher with custom crystals)
- **Max Distance**: 15m (standard), 300m+ (with RS-232 drivers)
- **Topology**: Point-to-point
- **Voltage**: TTL (0-5V), RS-232 (±12V)

### Required Message-Level Attributes

```yaml
uart_config:
  baud_rate:             # Communication speed
    type: integer
    required: true
    values: [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]

  data_bits:             # Bits per character
    type: integer
    values: [5, 6, 7, 8]
    default: 8

  parity:                # Error detection
    type: enum
    values: [none, even, odd, mark, space]
    default: none

  stop_bits:             # Stop bit count
    type: enum
    values: [1, 1.5, 2]
    default: 1

  flow_control:          # Hardware/software flow control
    type: enum
    values: [none, hardware, software, both]
    default: none
    description: "hardware = RTS/CTS, software = XON/XOFF"
```

### Required Field-Level Attributes

```yaml
uart_field:
  framing:               # Message framing protocol
    type: enum
    values: [fixed_length, delimited, length_prefixed, cobs, slip]
    required: true
    description: |
      fixed_length: Fixed message size
      delimited: Use start/end markers
      length_prefixed: First byte(s) = message length
      cobs: Consistent Overhead Byte Stuffing
      slip: Serial Line Internet Protocol

  delimiter:             # For delimited framing
    type: string
    description: "Start/end markers, e.g., '\\n' or '\\r\\n'"

  escape_character:      # For byte stuffing
    type: string

  byte_order:            # Endianness
    type: enum
    values: [big_endian, little_endian]
    default: little_endian

  checksum:              # Error detection
    type: enum
    values: [none, xor, crc8, crc16, crc32]
    default: crc16
    description: "Append checksum to each message"
```

### Rationale

- **Baud Rate**: Must match on both ends (no auto-negotiation)
- **Data Bits/Parity/Stop**: Must match for proper framing
- **Flow Control**: Prevents buffer overflow on slow receivers
- **Framing**: Critical for message boundaries in byte stream
- **Checksum**: UART has no built-in error detection beyond parity

### Example

```
struct SensorReading
    [attributes]
        uart_config:
            baud_rate: 115200
            data_bits: 8
            parity: none
            stop_bits: 1

    uint8 sensor_id
    float32 temperature
    float32 humidity
        uart_field:
            framing: length_prefixed
            byte_order: little_endian
            checksum: crc16
```

---

## RS-485

### Overview
Differential serial interface supporting multi-drop configurations. Industrial standard for robust long-distance communication.

### Physical Characteristics
- **Speed**: Up to 10 Mbps
- **Max Distance**: 1200m @ 100 Kbps
- **Topology**: Multi-drop bus (up to 32 nodes)
- **Voltage**: Differential ±7V

### Required Message-Level Attributes

```yaml
rs485_config:
  baud_rate:             # Communication speed
    type: integer
    required: true
    values: [9600, 19200, 38400, 57600, 115200]

  data_bits:
    type: integer
    values: [8, 9]
    default: 8

  parity:
    type: enum
    values: [none, even, odd]
    default: even         # Recommended for RS-485

  stop_bits:
    type: enum
    values: [1, 2]
    default: 1

  addressing_mode:       # How to address nodes
    type: enum
    values: [master_slave, peer_to_peer, token_passing]
    required: true
```

### Required Field-Level Attributes

```yaml
rs485_field:
  node_address:          # Device address on bus
    type: integer
    required: true
    range: [1, 247]      # 0 = broadcast, 248-255 reserved

  broadcast_address:     # Address for broadcast messages
    type: integer
    default: 0

  turnaround_time:       # RX/TX switching time
    type: integer
    unit: microseconds
    default: 100
    description: "Delay for transceiver direction change"

  collision_detection:   # Detect bus collisions
    type: boolean
    default: true

  retry_count:           # Retransmission attempts
    type: integer
    default: 3

  timeout:               # Response timeout
    type: integer
    unit: milliseconds
    default: 100
```

### Rationale

- **Addressing**: Required for multi-drop bus communication
- **Turnaround Time**: RS-485 transceivers need time to switch direction
- **Collision Detection**: Multiple transmitters can cause collisions
- **Retry Logic**: Half-duplex nature requires robust error handling
- **Even Parity**: Industry standard for RS-485

### Example

```
struct MotorCommand
    [attributes]
        rs485_config:
            baud_rate: 115200
            parity: even
            addressing_mode: master_slave

    uint8 node_address
        rs485_field:
            node_address: 1

    uint8 command
    int32 position
    uint16 velocity
        rs485_field:
            turnaround_time: 200
            timeout: 50
            retry_count: 3
```

---

## SPI (Serial Peripheral Interface)

### Overview
Synchronous serial protocol for short-distance communication. Master-slave architecture with separate clock line.

### Physical Characteristics
- **Speed**: Up to 100 Mbps
- **Max Distance**: ~3m (PCB traces)
- **Topology**: Master with multiple slaves
- **Lines**: SCLK, MOSI, MISO, SS (per slave)

### Required Message-Level Attributes

```yaml
spi_config:
  clock_speed:           # SPI clock frequency
    type: integer
    unit: hertz
    required: true
    range: [1000, 100000000]

  clock_polarity:        # Clock idle state (CPOL)
    type: enum
    values: [low, high]
    default: low
    description: "low = idle at 0V, high = idle at VDD"

  clock_phase:           # Clock edge for sampling (CPHA)
    type: enum
    values: [first_edge, second_edge]
    default: first_edge

  bit_order:             # Transmission order
    type: enum
    values: [msb_first, lsb_first]
    default: msb_first

  chip_select_polarity:  # CS active level
    type: enum
    values: [active_low, active_high]
    default: active_low

  chip_select_hold:      # CS hold time after transaction
    type: integer
    unit: nanoseconds
    default: 0
```

### Required Field-Level Attributes

```yaml
spi_field:
  register_address:      # For register-based devices
    type: integer
    description: "First byte often contains register address"

  read_write_bit:        # R/W flag in address byte
    type: boolean
    description: "Bit 7 of address byte for R/W indication"

  dummy_bytes:           # Dummy clocks for response
    type: integer
    default: 0
    description: "Number of dummy bytes before reading response"

  byte_order:            # Multi-byte field ordering
    type: enum
    values: [big_endian, little_endian]
    default: big_endian
```

### Rationale

- **Clock Polarity/Phase**: Must match device datasheet (4 SPI modes)
- **Bit Order**: Device-specific, often MSB-first
- **Chip Select**: Typically active-low, but device-dependent
- **Register Address**: Common pattern for peripheral access
- **Dummy Bytes**: Some devices need clock cycles before responding

### Example

```
struct AccelerometerData
    [attributes]
        spi_config:
            clock_speed: 10000000  # 10 MHz
            clock_polarity: high
            clock_phase: second_edge
            bit_order: msb_first

    uint8 register_address
        spi_field:
            register_address: 0x28  # ACCEL_XOUT_H
            read_write_bit: true

    int16 accel_x
    int16 accel_y
    int16 accel_z
        spi_field:
            dummy_bytes: 1
            byte_order: big_endian
```

---

## I2C

### Overview
Two-wire serial protocol for short-distance communication. Multi-master capable with addressing.

### Physical Characteristics
- **Speed**: 100 kbps (standard), 400 kbps (fast), 1 Mbps (fast+), 3.4 Mbps (high-speed)
- **Max Distance**: ~1m on PCB
- **Topology**: Multi-master bus
- **Lines**: SDA (data), SCL (clock)
- **Max Devices**: 127 (7-bit addressing)

### Required Message-Level Attributes

```yaml
i2c_config:
  device_address:        # I2C slave address
    type: integer
    required: true
    range: [0x00, 0x7F]  # 7-bit address
    description: "Some addresses reserved (0x00-0x07, 0x78-0x7F)"

  addressing_mode:       # Address bit width
    type: enum
    values: [7bit, 10bit]
    default: 7bit

  clock_speed:           # SCL frequency
    type: integer
    unit: hertz
    values: [100000, 400000, 1000000, 3400000]
    default: 100000

  clock_stretching:      # Allow slave to hold SCL low
    type: boolean
    default: true
    description: "Slave can pause transaction"
```

### Required Field-Level Attributes

```yaml
i2c_field:
  register_address:      # Internal register address
    type: integer
    required: true
    range: [0x00, 0xFF]

  register_width:        # Register address size
    type: enum
    values: [8bit, 16bit]
    default: 8bit

  auto_increment:        # Auto-increment register address
    type: boolean
    default: false
    description: "Read multiple sequential registers"

  byte_order:            # For multi-byte registers
    type: enum
    values: [big_endian, little_endian]
    default: big_endian
```

### Rationale

- **Device Address**: Required for bus arbitration
- **Clock Speed**: Must be supported by all devices on bus
- **Clock Stretching**: Allows slower devices to keep up
- **Register Address**: Common pattern for I2C peripherals
- **Auto-increment**: Efficient for reading multiple registers

### Example

```
struct IMUData
    [attributes]
        i2c_config:
            device_address: 0x68  # MPU-6050
            clock_speed: 400000   # Fast mode
            clock_stretching: true

    uint8 register_address
        i2c_field:
            register_address: 0x3B  # ACCEL_XOUT_H
            auto_increment: true

    int16 accel_x
    int16 accel_y
    int16 accel_z
    int16 temp
    int16 gyro_x
    int16 gyro_y
    int16 gyro_z
        i2c_field:
            byte_order: big_endian
```

---

## USB

### Overview
Universal Serial Bus. Host-controlled, hierarchical protocol supporting many device classes.

### Physical Characteristics
- **Speed**: 1.5 Mbps (low), 12 Mbps (full), 480 Mbps (high), 5 Gbps (super), 10 Gbps (super+)
- **Max Distance**: 5m (USB 2.0), 3m (USB 3.0)
- **Topology**: Tree with hub devices
- **Power**: Can provide 5V power to devices

### Required Message-Level Attributes

```yaml
usb_config:
  device_class:          # USB device class
    type: enum
    required: true
    values:
      - CDC: "Communications Device Class"
      - HID: "Human Interface Device"
      - MSC: "Mass Storage Class"
      - AUDIO: "Audio Device Class"
      - VIDEO: "Video Device Class"
      - VENDOR: "Vendor-specific"

  vendor_id:             # USB Vendor ID
    type: integer
    required: true
    range: [0x0000, 0xFFFF]
    description: "Assigned by USB-IF"

  product_id:            # USB Product ID
    type: integer
    required: true
    range: [0x0000, 0xFFFF]

  interface_number:      # Interface index
    type: integer
    default: 0

  endpoint_address:      # Endpoint number and direction
    type: integer
    required: true
    range: [0x00, 0xFF]
    description: "Bit 7: 0=OUT, 1=IN; Bits 0-3: endpoint number"

  endpoint_type:         # Transfer type
    type: enum
    required: true
    values: [control, interrupt, bulk, isochronous]

  max_packet_size:       # Maximum packet size
    type: integer
    unit: bytes
    required: true
    description: "Depends on speed and endpoint type"
```

### Required Field-Level Attributes

```yaml
usb_field:
  encoding:              # Data format
    type: enum
    values: [binary, hid_report, ascii]
    default: binary

  report_id:             # For HID devices
    type: integer
    range: [0x00, 0xFF]
    description: "HID report identifier"

  timeout:               # Transfer timeout
    type: integer
    unit: milliseconds
    default: 1000
```

### Rationale

- **Device Class**: Determines driver and protocol requirements
- **VID/PID**: Unique device identification
- **Endpoint**: Each endpoint has a specific purpose and direction
- **Transfer Type**: Determines delivery guarantees and timing
- **Max Packet Size**: Critical for buffer allocation

### Example

```
struct JoystickReport
    [attributes]
        usb_config:
            device_class: HID
            vendor_id: 0x046D  # Logitech
            product_id: 0xC216
            endpoint_address: 0x81  # EP1 IN
            endpoint_type: interrupt
            max_packet_size: 8

    uint8 buttons
    int8 x_axis
    int8 y_axis
        usb_field:
            encoding: hid_report
            report_id: 1
```

---

## Modbus

### Overview
Industrial protocol for PLC and SCADA systems. Simple request-response model over serial or Ethernet.

### Physical Characteristics
- **Transport**: RS-485, RS-232, or TCP/IP
- **Speed**: 9600-115200 bps (serial), any (TCP)
- **Topology**: Master-slave
- **Max Devices**: 247 (serial), unlimited (TCP)

### Required Message-Level Attributes

```yaml
modbus_config:
  variant:               # Modbus variant
    type: enum
    required: true
    values: [rtu, ascii, tcp]
    description: |
      rtu: Binary over serial
      ascii: ASCII over serial
      tcp: Binary over Ethernet

  slave_address:         # Device address (RTU/ASCII only)
    type: integer
    range: [1, 247]      # 0 = broadcast

  tcp_port:              # TCP port (Modbus/TCP only)
    type: integer
    default: 502

  timeout:               # Response timeout
    type: integer
    unit: milliseconds
    default: 1000

  retry_count:           # Retransmission attempts
    type: integer
    default: 3
```

### Required Field-Level Attributes

```yaml
modbus_field:
  function_code:         # Modbus function code
    type: enum
    required: true
    values:
      - 1: "Read Coils"
      - 2: "Read Discrete Inputs"
      - 3: "Read Holding Registers"
      - 4: "Read Input Registers"
      - 5: "Write Single Coil"
      - 6: "Write Single Register"
      - 15: "Write Multiple Coils"
      - 16: "Write Multiple Registers"

  register_address:      # Starting register address
    type: integer
    required: true
    range: [0, 65535]

  register_count:        # Number of registers
    type: integer
    default: 1
    range: [1, 125]      # Maximum per transaction

  data_type:             # Register interpretation
    type: enum
    values: [uint16, int16, uint32, int32, float32, bit]
    default: uint16
    description: "32-bit types use 2 registers"

  byte_order:            # For multi-register values
    type: enum
    values: [big_endian, little_endian, big_endian_swap, little_endian_swap]
    default: big_endian
    description: "Word and byte swapping for 32-bit types"

  scaling:               # Physical value conversion
    type: object
    properties:
      scale: {type: float, default: 1.0}
      offset: {type: float, default: 0.0}
```

### Rationale

- **Variant**: Different framing and error checking
- **Slave Address**: Required for multi-drop serial networks
- **Function Code**: Determines operation type
- **Register Address**: Modbus uses register-based addressing
- **Data Type**: Registers are 16-bit, but can represent larger types
- **Byte Order**: Complex due to word and byte swapping variations

### Example

```
struct ProcessData
    [attributes]
        modbus_config:
            variant: rtu
            slave_address: 1
            timeout: 500

    float32 temperature
        modbus_field:
            function_code: 3  # Read holding registers
            register_address: 100
            register_count: 2
            data_type: float32
            byte_order: big_endian_swap
            scaling:
                scale: 0.1
                offset: -273.15

    uint16 status
        modbus_field:
            function_code: 3
            register_address: 200
            data_type: uint16
```

---

## MQTT

### Overview
Lightweight pub/sub messaging protocol for IoT. Uses topic-based routing over TCP/IP.

### Physical Characteristics
- **Transport**: TCP/IP (typically port 1883, 8883 for TLS)
- **Model**: Publish/Subscribe via broker
- **QoS Levels**: 0 (at most once), 1 (at least once), 2 (exactly once)

### Required Message-Level Attributes

```yaml
mqtt_config:
  broker_url:            # MQTT broker address
    type: string
    required: true
    format: "mqtt://host:port" or "mqtts://host:port"

  client_id:             # Unique client identifier
    type: string
    required: true
    description: "Must be unique per broker"

  topic:                 # MQTT topic
    type: string
    required: true
    pattern: "^[^#+]*$"  # No wildcards in publish
    examples: ["sensors/temperature", "robot/status"]

  qos:                   # Quality of Service
    type: enum
    values: [0, 1, 2]
    default: 0
    description: |
      0: At most once (fire and forget)
      1: At least once (acknowledged)
      2: Exactly once (assured delivery)

  retained:              # Retain last message
    type: boolean
    default: false
    description: "Broker stores last message for new subscribers"

  keepalive:             # Connection keepalive
    type: integer
    unit: seconds
    default: 60

  clean_session:         # Clean session on connect
    type: boolean
    default: true
    description: "false = persistent session"
```

### Required Field-Level Attributes

```yaml
mqtt_field:
  encoding:              # Message payload format
    type: enum
    values: [json, msgpack, protobuf, binary, text]
    default: json

  compression:           # Payload compression
    type: enum
    values: [none, gzip, lz4]
    default: none

  timestamp:             # Add timestamp to message
    type: boolean
    default: true

  schema_version:        # Message schema version
    type: string
    description: "For schema evolution"
```

### Rationale

- **Topic**: Hierarchical naming for message routing
- **QoS**: Balance between reliability and overhead
- **Retained**: Last-value cache for status topics
- **Client ID**: Required for session management
- **Encoding**: MQTT is payload-agnostic, need to specify format

### Example

```
struct SensorReading
    [attributes]
        mqtt_config:
            broker_url: "mqtt://broker.example.com:1883"
            client_id: "sensor_node_01"
            topic: "factory/floor1/temperature"
            qos: 1  # At least once delivery
            retained: true  # Keep last value

    uint64 timestamp
    string sensor_id
    float32 temperature
    float32 humidity
        mqtt_field:
            encoding: json
            compression: none
            schema_version: "1.0"
```

---

## DDS (Data Distribution Service)

### Overview
Real-time pub/sub middleware standard (OMG). Decentralized, discovery-based, QoS-rich protocol for distributed systems.

### Physical Characteristics
- **Transport**: UDP/IP (typically), TCP/IP, shared memory
- **Model**: Data-Centric Publish/Subscribe
- **Discovery**: Automatic peer discovery
- **QoS**: 22 configurable QoS policies

### Required Message-Level Attributes

```yaml
dds_config:
  domain_id:             # DDS domain
    type: integer
    required: true
    range: [0, 232]
    description: "Logical partition of network"

  topic_name:            # DDS topic name
    type: string
    required: true

  type_name:             # Data type name
    type: string
    description: "Usually derived from struct name"
```

### Required QoS Attributes

```yaml
dds_qos:
  reliability:           # Delivery reliability
    type: enum
    values: [best_effort, reliable]
    default: reliable

  durability:            # Data persistence
    type: enum
    values: [volatile, transient_local, transient, persistent]
    default: volatile
    description: |
      volatile: No persistence
      transient_local: Stored in memory
      transient: Stored beyond process life
      persistent: Stored on disk

  history:               # Sample retention
    type: object
    properties:
      kind:
        type: enum
        values: [keep_last, keep_all]
        default: keep_last
      depth:
        type: integer
        default: 1
        description: "Number of samples to keep (keep_last only)"

  deadline:              # Maximum inter-sample period
    type: integer
    unit: milliseconds
    description: "Alert if no new data within period"

  latency_budget:        # Target latency
    type: integer
    unit: milliseconds
    description: "Hint to middleware for optimization"

  lifespan:              # Sample expiration time
    type: integer
    unit: milliseconds
    description: "Discard samples older than this"

  liveliness:            # Writer liveliness assertion
    type: object
    properties:
      kind:
        type: enum
        values: [automatic, manual_by_participant, manual_by_topic]
        default: automatic
      lease_duration:
        type: integer
        unit: milliseconds

  ownership:             # Multiple writers policy
    type: enum
    values: [shared, exclusive]
    default: shared
    description: "exclusive: highest strength writer wins"

  partition:             # Logical partitions
    type: array
    items: {type: string}
    description: "Topic filtering by partition name"
```

### Rationale

- **Domain ID**: Isolate DDS networks
- **Reliability**: Critical for control vs. best-effort for telemetry
- **Durability**: Late-joining subscribers need historical data
- **History**: Balance memory usage vs. data availability
- **Deadline/Lifespan**: Time-critical data validation
- **Ownership**: Multiple sources with priority

### Example

```
struct RobotPose
    [attributes]
        dds_config:
            domain_id: 0
            topic_name: "robot_pose"

        dds_qos:
            reliability: reliable
            durability: transient_local  # Late joiners get last pose
            history:
                kind: keep_last
                depth: 10
            deadline: 100  # Expect updates at 10+ Hz
            liveliness:
                kind: automatic
                lease_duration: 500
            partition: ["robot1"]

    uint64 timestamp
    float64 x
    float64 y
    float64 z
    float64 qx
    float64 qy
    float64 qz
    float64 qw
```

---

## WebSocket

### Overview
Full-duplex communication over HTTP. Provides persistent connection for real-time web applications.

### Physical Characteristics
- **Transport**: TCP/IP (HTTP upgrade)
- **Ports**: 80 (ws://), 443 (wss:// with TLS)
- **Model**: Bidirectional message streaming
- **Framing**: Built-in message framing

### Required Message-Level Attributes

```yaml
websocket_config:
  url:                   # WebSocket URL
    type: string
    required: true
    pattern: "^wss?://.*"
    examples: ["ws://localhost:8080/data", "wss://api.example.com/stream"]

  subprotocol:           # WebSocket sub-protocol
    type: string
    description: "Application-level protocol negotiation"
    examples: ["mqtt", "stomp", "wamp"]

  compression:           # Per-message deflate
    type: boolean
    default: false
    description: "RFC 7692 compression extension"

  max_message_size:      # Maximum message size
    type: integer
    unit: bytes
    default: 1048576     # 1 MB

  ping_interval:         # Keep-alive ping interval
    type: integer
    unit: seconds
    default: 30

  reconnect:             # Auto-reconnect on disconnect
    type: boolean
    default: true

  reconnect_delay:       # Delay before reconnect attempt
    type: integer
    unit: seconds
    default: 5
```

### Required Field-Level Attributes

```yaml
websocket_field:
  message_type:          # WebSocket frame type
    type: enum
    values: [text, binary]
    default: text

  encoding:              # Message payload format
    type: enum
    values: [json, msgpack, protobuf, binary, text]
    default: json
    description: "text frames typically use JSON"

  fragmentation:         # Allow message fragmentation
    type: boolean
    default: false
    description: "Split large messages into frames"
```

### Rationale

- **URL**: Includes protocol, host, port, and path
- **Subprotocol**: Allows protocol layering over WebSocket
- **Compression**: Reduces bandwidth for text-heavy data
- **Ping Interval**: Keeps connection alive through firewalls/proxies
- **Message Type**: Text for JSON, binary for efficient encoding

### Example

```
struct ChatMessage
    [attributes]
        websocket_config:
            url: "wss://chat.example.com/stream"
            subprotocol: "chat.v1"
            compression: true
            ping_interval: 30

    string user_id
    string message
    uint64 timestamp
        websocket_field:
            message_type: text
            encoding: json
```

---

## Comparison Matrix

### Speed & Distance

| Interface  | Max Speed      | Max Distance  | Notes                        |
|------------|----------------|---------------|------------------------------|
| CAN        | 1 Mbps         | 40m - 1000m   | Speed/distance tradeoff      |
| Ethernet   | 100 Gbps       | 100m - 40km   | Depends on physical medium   |
| TCP/IP     | Network-dep.   | Global        | Internet-scale               |
| UDP/IP     | Network-dep.   | Global        | Internet-scale               |
| UART       | 921 Kbps       | 15m           | Point-to-point only          |
| RS-485     | 10 Mbps        | 1200m         | Multi-drop capable           |
| SPI        | 100 Mbps       | ~3m           | PCB-level only               |
| I2C        | 3.4 Mbps       | ~1m           | PCB-level only               |
| USB        | 10 Gbps        | 3-5m          | Host-controlled topology     |
| Modbus     | Varies         | Varies        | Runs over serial or TCP      |
| MQTT       | Network-dep.   | Global        | Requires broker              |
| DDS        | Network-dep.   | LAN/WAN       | Peer-to-peer discovery       |
| WebSocket  | Network-dep.   | Global        | HTTP-based                   |

### Key Characteristics

| Interface  | Topology       | Reliability   | Real-time | Complexity |
|------------|----------------|---------------|-----------|------------|
| CAN        | Bus            | High          | Yes       | Medium     |
| Ethernet   | Star/Mesh      | Medium        | Possible  | Medium     |
| TCP/IP     | Any            | Guaranteed    | No        | High       |
| UDP/IP     | Any            | None          | Yes       | Medium     |
| UART       | Point-to-point | Medium        | Yes       | Low        |
| RS-485     | Bus            | Medium        | Yes       | Medium     |
| SPI        | Master-slave   | High          | Yes       | Low        |
| I2C        | Bus            | Medium        | Yes       | Low        |
| USB        | Tree           | High          | Possible  | High       |
| Modbus     | Master-slave   | Medium        | Limited   | Medium     |
| MQTT       | Star (broker)  | Configurable  | No        | Medium     |
| DDS        | Peer-to-peer   | Configurable  | Yes       | High       |
| WebSocket  | Client-server  | TCP-based     | Possible  | Medium     |

### Use Cases

| Interface  | Typical Applications                                    |
|------------|---------------------------------------------------------|
| CAN        | Automotive, industrial machines, medical devices        |
| Ethernet   | Office networks, industrial Ethernet, data centers      |
| TCP/IP     | Web services, file transfer, databases                  |
| UDP/IP     | Video streaming, gaming, VoIP, real-time telemetry      |
| UART       | Sensor interfacing, debug consoles, GPS modules         |
| RS-485     | Industrial control, building automation, access control |
| SPI        | Flash memory, SD cards, displays, sensor chips          |
| I2C        | Sensor interfacing, EEPROMs, real-time clocks           |
| USB        | Peripherals, storage devices, debug interfaces          |
| Modbus     | PLCs, SCADA systems, industrial automation              |
| MQTT       | IoT devices, home automation, mobile notifications      |
| DDS        | Robotics, autonomous vehicles, aerospace, defense       |
| WebSocket  | Real-time web apps, live dashboards, chat systems       |

---

## Attribute Schema Recommendations

### Priority 1 (Core Attributes)

These should be implemented first as they cover the most common use cases:

1. **CAN Bus** - Critical for automotive and industrial
2. **TCP/IP** - Universal network communication
3. **UDP/IP** - Real-time streaming and telemetry
4. **UART** - Ubiquitous in embedded systems
5. **Modbus** - Industrial standard

### Priority 2 (Extended Support)

6. **RS-485** - Industrial multi-drop networks
7. **MQTT** - IoT and cloud connectivity
8. **Ethernet** - Low-level network control
9. **WebSocket** - Web-based interfaces

### Priority 3 (Specialized)

10. **DDS** - Advanced robotics and aerospace
11. **SPI** - Low-level peripheral interfacing
12. **I2C** - Sensor integration
13. **USB** - Device interfacing

---

## Implementation Notes

### Schema Modularity

Each interface should be a separate YAML schema file that can be enabled independently:

```toml
[attributes]
enabled_schemas = ["can_bus", "tcp", "udp", "uart", "modbus"]
```

### Validation Hierarchy

1. **Physical Layer**: Baud rate, voltage levels, timing
2. **Data Link Layer**: Framing, addressing, error detection
3. **Transport Layer**: Reliability, ordering, flow control
4. **Application Layer**: Encoding, compression, message structure

### Code Generation

Different generators should extract relevant attributes:

- **CAN DBC Generator**: Uses `can_message` and `can_signal` attributes
- **Modbus Generator**: Uses `modbus_config` and `modbus_field` attributes
- **C++ Generator**: May ignore interface-specific attributes or generate interface abstraction

### Multi-Interface Support

A single message type could support multiple interfaces:

```
struct SensorData
    [attributes]
        can_message:
            id: 0x100
        modbus_config:
            slave_address: 1
        mqtt_config:
            topic: "sensors/data"

    float32 temperature
    float32 pressure
```

This allows the same data structure to be used across different communication channels in a system.

---

## Conclusion

This guide provides a comprehensive overview of communication interface requirements for encoding/decoding in LumosInterface IDL. The attribute-based approach allows:

1. **Flexibility**: Support any interface without grammar changes
2. **Extensibility**: Add new interfaces via YAML schemas
3. **Separation**: Each interface has independent attributes
4. **Multi-interface**: Same message on multiple transports
5. **Tool Generation**: Generate interface-specific code from attributes

The modular schema design ensures that projects only enable and validate the interfaces they actually use, keeping the system lightweight and maintainable.
