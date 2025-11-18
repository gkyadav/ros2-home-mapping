# Hardware Overview – Home Mapping Robot

## Main Components

- Vacuum robot chassis (drive base, wheels, encoders)
- Arduino Uno – motor control + encoders + IMU + magnetometer
- Raspberry Pi 4 – runs ROS 2 (Jazzy)
- LiDAR – SL Lidar C1 (USB)
- Motor driver – L298 or similar
- Power – battery pack + regulators (TODO: fill exact details)

## Roles

- **Arduino Uno**
  - Reads encoder ticks.
  - Reads IMU + magnetometer.
  - Controls motors via motor driver.
  - Sends sensor + status data over serial to Raspberry Pi.

- **Raspberry Pi**
  - Runs ROS 2 nodes:
    - `serial_node` for Arduino bridge.
    - EKF fusion node.
    - LiDAR driver.
    - (Later) SLAM and navigation stack.

- **LiDAR**
  - Provides 2D scan data `/scan` for mapping and localization.
