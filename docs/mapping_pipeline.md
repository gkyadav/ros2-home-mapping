# Mapping Pipeline – From Sensors to Map

This document explains how data flows through my home mapping robot, from sensors to fused odometry, and then to mapping.

---

## 1. Hardware-level view

**Sensors and compute:**

- **Wheel encoders** → measure wheel rotation.
- **IMU (accelerometer + gyroscope)** → measure linear acceleration + angular velocity.
- **Magnetometer** → measure heading relative to magnetic north.
- **LiDAR (2D)** → measure distance to obstacles around the robot.
- **Arduino Uno** → reads encoders + IMU + magnetometer, controls motors.
- **Raspberry Pi (ROS 2)** → runs all higher-level nodes (bridge, EKF, LiDAR driver, SLAM).

---

## 2. Arduino responsibilities

Arduino is responsible for:

1. **Reading sensors**
   - Counts encoder ticks from wheel encoders.
   - Reads IMU values (ax, ay, az, gx, gy, gz).
   - Reads magnetometer (heading).

2. **Motor control**
   - Sends PWM signals to motor driver to move the wheels.

3. **Sending a data packet over serial**
   - Every loop, Arduino sends a comma-separated line with:
     - Motor/command flags (e.g. left/right motor state)
     - Encoder information
     - IMU values
     - Magnetometer values

   Example:

   ```text
   1,1,-0.1899,-0.1194,1.0251,-24.3053,6.1832,0.5725,59.71,-12.02,3.23,82.00,181.00,-141.00
3. ROS 2 serial bridge on Raspberry Pi
Node: serial_node in package arduino_bridge
Location: ~/ros2_ws/src/arduino_bridge

Responsibilities:

Open the correct serial port (e.g. /dev/ttyACM0).

Read each line from Arduino.

Parse all comma-separated values.

Publish them as ROS 2 messages on topics like:

/odom_raw → encoder-based odometry (position + orientation estimate)

/imu/data_raw → IMU message

/mag → magnetometer data

(Optional) motor diagnostics, etc.

This converts the Arduino world into ROS 2 topics.

4. EKF fusion node
Node: ekf_node (from robot_localization or similar)
Input topics:

/odom_raw (from encoders)

/imu/data_raw (from IMU)

/mag (optional)

Output topic:

/odometry/filtered – best estimate of robot pose in odom frame

Why EKF?
Encoders alone drift (wheel slip, uneven floor).

IMU alone drifts (gyro bias, noise).

Magnetometer is noisy and affected by metal but helps long-term heading.

EKF combines them statistically:

Trusts each sensor based on its noise parameters.

Updates the belief of robot position and orientation over time.

So /odometry/filtered is usually much better than any single sensor.

5. LiDAR node
Node: LiDAR driver (e.g. sllidar_ros2)
Input:

Serial data from LiDAR on /dev/ttyUSB0.

Output:

/scan (sensor_msgs/LaserScan)

This gives a 2D range measurement around the robot, used for:

Obstacle detection

Mapping (SLAM)

Localization against existing maps

6. Putting it together – pipeline diagram (text)
Data flow:

Arduino

Encoders + IMU + mag → serial packet over USB.

Raspberry Pi / ROS 2

serial_node (arduino_bridge) reads serial → publishes:

/odom_raw

/imu/data_raw

/mag

Fusion

ekf_node subscribes to /odom_raw, /imu/data_raw, /mag.

Outputs /odometry/filtered.

LiDAR

LiDAR node publishes /scan.

(Future) SLAM

SLAM node will read /scan + /odometry/filtered.

Builds and updates a 2D map of the home.

In short:

text
Copy code
Encoders + IMU + Mag --(Arduino)--> Serial
Serial --(arduino_bridge)--> /odom_raw, /imu/data_raw, /mag
/odom_raw + /imu/data_raw (+ /mag) --(EKF)--> /odometry/filtered
LiDAR --(driver)--> /scan
/odometry/filtered + /scan --(SLAM)--> Map
7. Frames (tf) concept
Typical frames in this setup:

odom → world-like frame where fused odometry lives.

base_link → robot’s body frame.

LiDAR frame (e.g. laser) attached to base_link.

The EKF node maintains the transform:

text
Copy code
odom → base_link
SLAM will maintain or refine:

text
Copy code
map → odom
This chaining lets ROS know where every sensor is located in the world.

8. Current limitations / assumptions
Odometry is only as good as:

Encoder calibration (ticks per rev, wheel diameter).

IMU calibration and noise parameters.

No SLAM yet – only odometry and LiDAR data stream.

No closed-loop navigation – currently focusing on sensing and mapping first.

yaml
Copy code

Then `Ctrl + O`, `Enter`, then `Ctrl + X` to save and exit.

---
