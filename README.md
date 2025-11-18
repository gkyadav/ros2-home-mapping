# Home Mapping Robot (RPi + Arduino + LiDAR)

## Overview
The robot is currently able to publish EKF data - filtered numbers for IMU and Odom

## Hardware
- Raspberry Pi 4
- Arduino Uno (encoders + IMU + magnetometer)
- Vacuum robot base (wheels, chassis)
- LiDAR (Slamtec / SL Lidar C1)
- Power configuration

## Software
- Ubuntu on Raspberry Pi
- ROS 2 Jazzy
- arduino_bridge package for serial I/O
- EKF node for sensor fusion
- LiDAR driver (sllidar_ros2)

## Current Capabilities
- Arduino publishes wheel + IMU + mag data over serial
- ROS 2 node reads serial and publishes /odom_raw, /imu/data_raw, /mag
- EKF node publishes /odometry/filtered

## How to Run (short)
1. Start Arduino serial bridge
2. Start EKF
3. (Later) Start LiDAR driver
5. (Later) Start SLAM node

## Documentation
See the `docs/` folder for:
- docs/timeline.md – step-by-step history of how this project evolved
- docs/mapping_pipeline.md – explanation of the full data flow
