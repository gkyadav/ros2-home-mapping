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

## ROS 2 Basics – How All the Pieces Fit Together

If you're coming from Arduino, ROS can feel confusing at first:

- On Arduino you usually have **one `.ino` file** that does *everything*.
- In ROS you suddenly see **nodes, launch files, YAML, TF, URDF…**

This section explains how these pieces fit together in simple terms.

---

### 1. The Real “Atom” in ROS: the **Node**
Node = one small program, that does a specific job.
A node is usually a **Python (`.py`)** or **C++** executable.  
Examples:
- a LiDAR driver node → publishes `/scan`
- an Arduino bridge node → publishes encoder/IMU data
- an EKF node → fuses sensors into odometry
- a SLAM node → builds a `/map`
- RViz → visualizes topics and TF

You can run a node directly:
ros2 run <package_name> <node_executable>
If you have one node, you already have a working ROS “unit”.
Everything else is there to configure, connect, and visualize these nodes.

### 2. YAML Files – Settings, Not Code
YAML = configuration file with parameters for nodes.
Instead of hard-coding values inside the code, we put them in a YAML file:

yaml
Copy code
slam_toolbox:
  ros__parameters:
    scan_topic: /scan
    base_frame: base_link
    odom_frame: odom
    map_frame: map
    resolution: 0.05
Nodes read these parameters at startup.

Change YAML → behavior changes without editing the code.
Typical configs:
 1.Topic names
 2.Frame names (odom, base_link, map)
 3.Filter gains, thresholds, resolutions, etc.

If the YAML is missing, the node may:
   - fall back to defaults, or
   - fail to start if required params are missing.


### 3.TF – The Coordinate System Glue
TF = system that tracks how all coordinate frames relate to each other.

In robotics we care about where things are:
map – global map frame
odom – odometry frame
base_link – robot body center
laser / camera – sensors mounted on the robot

TF defines a tree like:

map  →  odom  →  base_link  →  laser

Nodes publish TF transforms at runtime:
-the EKF publishes odom → base_link
-SLAM publishes map → odom
-static publishers define fixed offsets (e.g. base_link → laser)
-Other nodes and RViz ask TF: “Where is base_link relative to map right now?”
-If TF is missing or wrong: RViz shows errors like “Frame [map] does not exist” or SLAM can’t update the map correctly or Navigation has no idea where the robot is


### 4.URDF – The Robot Blueprint
URDF = a text description of the robot’s physical structure.

URDF (or xacro) describes:
links (bodies): base, wheels, sensors
joints: how they connect
sizes/shapes: cylinders, boxes, meshes
Tools like RViz and simulators (Gazebo) use URDF to:
 1.draw a 3D model of your robot
 2.know its size for collision checking

If URDF is missing: The robot can still move, publish topics, and do SLAM.

You just see axes and laser points instead of a pretty robot model.

### 5.Launch Files – The Manager
Launch file = a script that starts multiple nodes with the right configs.

Manually you could run everything like this:

# Arduino bridge
ros2 run arduino_bridge serial_node

# EKF
ros2 run robot_localization ekf_node --ros-args --params-file ekf.yaml

# LiDAR driver
ros2 launch sllidar_ros2 sllidar_c1_launch.py serial_port:=/dev/ttyUSB0

# SLAM
ros2 launch slam_toolbox online_async_launch.py
That’s annoying to type each time, and easy to mess up.

So we create a launch file, e.g. ekf.launch.py or mapping.launch.py, that:
 - Starts all required nodes
 - Loads their YAML configs
 - Can also spawn static TF publishers and URDF robot description

Then you just do: ros2 launch my_robot mapping.launch.py
If the launch file is missing, you can still run nodes manually – it’s just less convenient and more error-prone.


### 6.How It All Fits Together (Example: LiDAR + Arduino + SLAM)
Here’s a typical pipeline for a small mobile robot:

[Arduino firmware]  (on microcontroller)
      │
      ▼  (serial)
[serial_node]  (ROS node on RPi)
publishes: /odom_raw, /imu/data_raw, /tf? (optional)
      │
      ▼
[EKF node]  (robot_localization)
reads: /odom_raw, /imu/data_raw
uses: ekf.yaml parameters
publishes:
    - /odometry/filtered
    - TF: odom → base_link
      │
      │
[LiDAR node]  (sllidar_ros2)
publishes: /scan (frame_id=base_link)
      │
      ▼
[SLAM node]  (slam_toolbox)
reads: /scan + TF (odom → base_link)
uses: slam_toolbox YAML
publishes:
    - /map
    - TF: map → odom
      │
      ▼
[RViz]
subscribes to: /scan, /map, /tf
shows the robot and map in Fixed Frame = map

Around this pipeline:
 1. Nodes do all the work.
 2. YAML files tune how they behave.
 3. TF connects all coordinate frames.
 4. URDF describes what the robot looks like.
 5. Launch files start everything correctly in one command.


### 7.Mental Model (Quick Recap)
If you like analogies, here’s a handy one:
Node → the worker (does 1 job)
YAML → the worker’s settings sheet
TF → the map of where everyone is standing
URDF → the blueprint/drawing of the robot’s body
Launch file → the manager that calls everyone to work

In Arduino: one .ino file tries to be all of these at once.
In ROS: we split responsibilities into smaller, reusable pieces.
This structure is what makes large robot projects easier to manage, debug, and extend.



## Quickstart – How to Run the System

### 1. Start Arduino serial bridge

On Raspberry Pi:

```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run arduino_bridge serial_node

2. Start EKF node
bash
Copy code
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch arduino_bridge ekf.launch.py

3. Start LiDAR driver
bash
Copy code
ros2 launch sllidar_ros2 sllidar_c1_launch.py serial_port:=/dev/ttyUSB0

4. (Later) Start SLAM
TODO: add SLAM launch command once configured.
When all are running, you should see:
/odom_raw, /imu/data_raw, /mag from Arduino bridge
/odometry/filtered from EKF
/scan from LiDAR

## Arduino Firmware
The Arduino code used for motor control + encoders + IMU + magnetometer lives in: `firmware/arduino/home_mapping_controller/`

This firmware:
- Reads wheel encoders, IMU, and magnetometer
- Controls the motors via L298
- Sends a comma-separated sensor packet over serial to the Raspberry Pi
