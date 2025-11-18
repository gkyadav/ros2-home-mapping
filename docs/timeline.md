# Home Mapping Robot – Project Timeline

This document tracks the journey of building my home mapping robot step by step.

---

## Stage 1 – Basic robot motion with Arduino

**Goal:** Make the vacuum robot chassis move reliably using Arduino only.

- Mounted Arduino Uno on the vacuum robot base.
- Connected motor driver (L298 / similar) to motors and Arduino PWM pins.
- Wrote simple Arduino code to:
  - Spin wheels forward.
  - Test left/right turns.
  - Try to move as straight as possible using only fixed PWM values.
- Verified: robot can move around but has no idea where it is (no odometry yet).

---

## Stage 2 – Wheel encoders + basic odometry on Arduino

**Goal:** Measure how far the robot moves using wheel encoders.

- Connected wheel encoders to Arduino interrupt pins.
- Measured ticks per revolution (approx. **236 ticks/rev** from experiment).
- Wrote Arduino code to:
  - Count encoder ticks while the wheel rotates.
  - Compute distance moved using:

    \[
    \text{distance} = \text{ticks} \times \frac{\text{wheel circumference}}{\text{ticks per rev}}
    \]

- Tested:
  - Move wheel one revolution.
  - Stop motor after target tick count is reached.
- Result: Arduino can estimate distance traveled using encoder ticks.

---

## Stage 3 – Adding IMU + magnetometer on Arduino

**Goal:** Get orientation and acceleration data.

- Connected IMU (MPU6050 or similar) + magnetometer (e.g. QMC5883L) to Arduino via I2C.
- Wrote Arduino code to read:
  - Acceleration (ax, ay, az)
  - Gyro (gx, gy, gz)
  - Magnetometer heading
- Designed a serial output format (one line with multiple comma-separated values), e.g.:

  ```text
  READY: SENSORS + MOTOR CONTROL ACTIVE
  1,1,-0.1899,-0.1194,1.0251,-24.3053,6.1832,0.5725,59.71,-12.02,3.23,82.00,181.00,-141.00
Now Arduino is sending:

Motor control state

Encoder-derived info

IMU + mag data
all over USB serial to the Raspberry Pi.

Stage 4 – Raspberry Pi + ROS 2 bridge (arduino_bridge package)
Goal: Bring Arduino data into ROS 2 as proper topics.

On Raspberry Pi, created a ROS 2 workspace: ~/ros2_ws.

Created a package: ~/ros2_ws/src/arduino_bridge.

Implemented serial_node to:

Open /dev/ttyACM* to talk to Arduino.

Read each serial line.

Parse the values.

Publish ROS 2 topics like:

/odom_raw (wheel encoder odometry)

/imu/data_raw

/mag

Verified using:

bash
Copy code
ros2 topic list
ros2 topic echo /odom_raw
ros2 topic echo /imu/data_raw
Result: Arduino sensor data is now inside the ROS 2 graph.

Stage 5 – EKF fusion node (robot_localization)
Goal: Fuse encoders + IMU (+ mag) into a better estimate of robot pose.

Installed and configured EKF node (e.g. robot_localization).

Created an EKF config file (ekf.yaml) with inputs:

/odom_raw

/imu/data_raw

optional: /mag

Launched EKF node using a launch file:

Subscribes to raw topics.

Publishes /odometry/filtered in frame odom → base_link.

Verified with:

bash
Copy code
ros2 topic echo /odometry/filtered --once
Result: I now have a fused odometry estimate combining wheel encoders + IMU.

Stage 6 – Adding LiDAR to the system
Goal: Get 2D laser scans for mapping and future SLAM.

Connected LiDAR to Raspberry Pi via USB (/dev/ttyUSB0).

Used sllidar_ros2 driver with a launch command like:

bash
Copy code
ros2 launch sllidar_ros2 sllidar_c1_launch.py serial_port:=/dev/ttyUSB0
Verified:

/scan topic exists.

Laser scan data is streaming.

Now I have:

/odometry/filtered from EKF.

/scan from LiDAR.

This is the foundation for 2D SLAM and home mapping.

Stage 7 – Current status and next steps
Current status:

Arduino → RPi serial bridge working.

Raw topics /odom_raw, /imu/data_raw, /mag available.

EKF node running and publishing /odometry/filtered.

LiDAR node running and publishing /scan.

Next steps:

Integrate a SLAM package (e.g. slam_toolbox).

Feed /scan + /odometry/filtered into SLAM for map building.

Create a single launch file to start:

Arduino bridge

EKF node

LiDAR driver

SLAM node (later)
