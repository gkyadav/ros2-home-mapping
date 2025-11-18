# Wiring – Raspberry Pi, Arduino, LiDAR, Motors

> This is a living document. I will keep updating it as I refine the wiring.

---

## 1. Arduino connections

### Encoders

- Encoder A → Arduino pin: TODO
- Encoder B → Arduino pin: TODO
- Power and ground shared with Arduino.

### IMU + Magnetometer (I2C)

- SDA → Arduino SDA (A4 on Uno)
- SCL → Arduino SCL (A5 on Uno)
- VCC → 5V or 3.3V depending on module
- GND → common ground

### Motor driver

- IN1, IN2, ENA → Arduino pins: TODO
- IN3, IN4, ENB → Arduino pins: TODO
- Motor power input → battery (through appropriate regulator/fuse)
- Motor outputs → left/right motors

---

## 2. Raspberry Pi connections

- USB to Arduino:
  - Arduino appears as `/dev/ttyACM0` (most of the time).
- USB to LiDAR:
  - LiDAR appears as `/dev/ttyUSB0`.

- (Optional) Any GPIOs used: TODO.

---

## 3. Power notes

- Common ground between:
  - Arduino
  - Raspberry Pi
  - Motor driver
  - LiDAR (if needed)

- Battery setup:
  - TODO: describe battery type, regulators, and voltage levels.
