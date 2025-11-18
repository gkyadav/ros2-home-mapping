# Nodes and Topics – Home Mapping Robot

This document lists all important ROS 2 nodes and topics in my system.

---

## 1. Node list

### Raspberry Pi – main nodes

- `arduino_bridge` package
  - **Node:** `serial_node`
  - **Role:** Reads serial data from Arduino, publishes sensor topics.

- `ekf_node` (from `robot_localization`)
  - **Role:** Fuses `/odom_raw`, `/imu/data_raw`, `/mag` into `/odometry/filtered`.

- LiDAR driver (e.g. `sllidar_ros2`)
  - **Node:** `sllidar_node` (or similar)
  - **Role:** Publishes `/scan`.

- (Future) SLAM node
  - **Package:** TBD
  - **Role:** Takes `/scan` + `/odometry/filtered` and builds a map.

---

## 2. Topics overview

### From `serial_node` (arduino_bridge)

- `/odom_raw`
  - **Type:** nav_msgs/Odometry
  - **From:** Arduino encoders
  - **Used by:** EKF

- `/imu/data_raw`
  - **Type:** sensor_msgs/Imu
  - **From:** IMU
  - **Used by:** EKF

- `/mag`
  - **Type:** (e.g. geometry_msgs/Vector3 or custom)
  - **From:** Magnetometer
  - **Used by:** EKF (optional)

### From EKF node

- `/odometry/filtered`
  - **Type:** nav_msgs/Odometry
  - **From:** EKF fusion of `/odom_raw` + `/imu/data_raw` (+ `/mag`)
  - **Used by:** SLAM, navigation (future)

### From LiDAR node

- `/scan`
  - **Type:** sensor_msgs/LaserScan
  - **From:** LiDAR (C1)
  - **Used by:** SLAM, obstacle avoidance (future)

---

## 3. Command cheatsheet

To inspect nodes:

```bash
ros2 node list
ros2 node info <node_name>
To inspect topics:

bash
Copy code
ros2 topic list
ros2 topic info <topic_name>
When all nodes are running, I should see at least:

/odom_raw

/imu/data_raw

/mag

/odometry/filtered

/scan

