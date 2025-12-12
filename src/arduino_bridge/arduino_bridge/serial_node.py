#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, MagneticField
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, TransformStamped, Quaternion
from tf2_ros import TransformBroadcaster
import serial
import math
import time
import numpy as np
import re  # <-- NEW: for robust number extraction


# --- CONSTANTS ---
SERIAL_PORT = '/dev/ttyACM0'  # Confirmed by your code
SERIAL_BAUDRATE = 115200

# Kinematics Constants (Confirmed by your code)
TICKS_PER_REV = 236.0
WHEEL_DIAM = 0.065            # Diameter in meters
WHEEL_RADIUS = WHEEL_DIAM / 2.0
WHEEL_BASE = 0.20             # Wheel separation (L) in meters

# Derived constants
TICKS_PER_METER = TICKS_PER_REV / (math.pi * WHEEL_DIAM)
MAX_PWM = 80.0               # L298N max
MAX_LINEAR_SPEED = 0.1        # Max linear speed in m/s (Adjust this if needed)

# IMU Conversion constants
G_TO_ACCEL = 9.80665  # Standard gravity (m/s^2)
DEG_TO_RAD = math.pi / 180.0

# Expected number of values per serial line from Arduino
EXPECTED_FIELDS = 14

# Regex pattern to extract floats (handles "187.", "-0.2004", "0.5", "42")
FLOAT_RE = re.compile(r'[+-]?(?:\d+\.\d*|\d*\.\d+|\d+)')


class ArduinoBridge(Node):
    def __init__(self):
        super().__init__('arduino_bridge')

        # 1. Serial Port Setup
        try:
            self.ser = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=0.01)
            time.sleep(2)
            self.get_logger().info(f"Connected to Arduino on {SERIAL_PORT}")
        except serial.SerialException as e:
            self.get_logger().error(f"Failed to connect to Arduino on {SERIAL_PORT}: {e}")
            self.ser = None
            return

        # 2. ROS Publishers, Subscribers, and Broadcaster
        self.pub_imu = self.create_publisher(Imu, 'imu/data_raw', 50)
        self.pub_mag = self.create_publisher(MagneticField, 'mag', 10)
        self.pub_odom = self.create_publisher(Odometry, 'odom_raw', 50)
        self.tf_broadcaster = TransformBroadcaster(self)

        self.sub_cmd_vel = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10
        )

        # 3. Timer and State
        self.create_timer(0.02, self.loop)
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.last_time = time.time()

        self.get_logger().info("Arduino Bridge running. Ready for /cmd_vel commands.")

    def cmd_vel_callback(self, msg: Twist):
        """Converts ROS Twist message to PWM commands and sends them to the Arduino."""
        linear_x = np.clip(msg.linear.x, -MAX_LINEAR_SPEED, MAX_LINEAR_SPEED)
        angular_z = msg.angular.z  # No clipping on angular, let the kinematics handle it

        # Differential Drive Kinematics (Vx, Wz -> Vr, Vl)
        v_l = linear_x - (angular_z * WHEEL_BASE / 2.0)
        v_r = linear_x + (angular_z * WHEEL_BASE / 2.0)

        # Convert velocity (m/s) to target PWM (0-255)
        # This assumes the MAX_LINEAR_SPEED corresponds to MAX_PWM
        target_pwm_l = int(v_l / MAX_LINEAR_SPEED * MAX_PWM)
        target_pwm_r = int(v_r / MAX_LINEAR_SPEED * MAX_PWM)

        # Format and send command
        # Note: Arduino handles the sign (direction) based on the L298N logic
        command = f"L:{target_pwm_l} R:{target_pwm_r}\n"
        try:
            self.ser.write(command.encode('utf-8'))
        except serial.SerialException as e:
            self.get_logger().error(f"Error sending command: {e}")

    def loop(self):
        """Main read loop for incoming serial data."""
        if not self.ser:
            return

        line = self.ser.readline().decode(errors="ignore").strip()
        if not line:
            return

        # --- Robust numeric parsing ---
        # Extract all numbers from the line, ignore garbage like extra commas, etc.
        matches = FLOAT_RE.findall(line)

        if len(matches) < EXPECTED_FIELDS:
            # Not enough numbers → partial/corrupt line, skip it
            self.get_logger().warn(
                f"Skipping malformed line (got {len(matches)} numbers, expected at least {EXPECTED_FIELDS}): {line}"
            )
            return

        # Take the FIRST 14 numbers as one complete sample
        # (if we accidentally captured more than one frame glued together, we just use the first one)
        try:
            values = [float(m) for m in matches[:EXPECTED_FIELDS]]
            # Destructuring the received data
            encL, encR, ax, ay, az, gx, gy, gz, yaw_deg, pitch_deg, roll_deg, mx, my, mz = values
        except ValueError as e:
            self.get_logger().error(f"Error converting numbers: {e} | Line: {line}")
            return

        # --- Time Step ---
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        if dt <= 0:
            return

        current_ros_time = self.get_clock().now().to_msg()

        # --- ODOMETRY ---
        self._update_and_publish_odom(current_ros_time, dt, encL, encR)

        # --- IMU ---
        self._publish_imu(current_ros_time, ax, ay, az, gx, gy, gz,
                          yaw_deg, pitch_deg, roll_deg)

        # --- MAG ---
        self._publish_mag(current_ros_time, mx, my, mz)

    def _update_and_publish_odom(self, current_ros_time, dt, encL_delta, encR_delta):
        """Calculates odometry and publishes the message and TF."""

        distL = encL_delta / TICKS_PER_METER
        distR = encR_delta / TICKS_PER_METER
        dist = (distL + distR) / 2.0

        dtheta = (distR - distL) / WHEEL_BASE

        # Dead Reckoning Update
        self.x += dist * math.cos(self.yaw)
        self.y += dist * math.sin(self.yaw)
        self.yaw += dtheta

        # --- 1. Publish TF (odom -> base_link) ---
        t = TransformStamped()
        t.header.stamp = current_ros_time
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'

        q_odom = self._euler_to_quaternion(0.0, 0.0, self.yaw)

        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation = q_odom

        self.tf_broadcaster.sendTransform(t)

        # --- 2. Publish Odometry Message ---
        odom = Odometry()
        odom.header.stamp = current_ros_time
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"

        # Pose
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation = q_odom

        # Twist
        odom.twist.twist.linear.x = dist / dt
        odom.twist.twist.angular.z = dtheta / dt

        # Set covariance (essential for EKF/SLAM)
        odom.pose.covariance[0] = 0.0001
        odom.pose.covariance[7] = 0.0001
        odom.pose.covariance[35] = 0.001
        odom.twist.covariance[0] = 0.0001
        odom.twist.covariance[35] = 0.001

        self.pub_odom.publish(odom)

    def _publish_imu(self, current_ros_time, ax, ay, az, gx, gy, gz,
                     yaw_deg, pitch_deg, roll_deg):
        """Publishes the IMU message using the Arduino's calculated orientation."""
        imu = Imu()
        imu.header.stamp = current_ros_time
        imu.header.frame_id = "base_link"  # Assuming IMU is centered on base_link for simplicity

        # Angular Velocity (rad/s)
        imu.angular_velocity.x = gx
        imu.angular_velocity.y = gy
        imu.angular_velocity.z = gz

        # Linear Acceleration (m/s^2) - Scale Arduino's normalized values back to m/s^2
        imu.linear_acceleration.x = ax * G_TO_ACCEL
        imu.linear_acceleration.y = ay * G_TO_ACCEL
        imu.linear_acceleration.z = az * G_TO_ACCEL

        # Orientation (from Arduino's complementary filter)
        q_imu = self._euler_to_quaternion(
            roll_deg * DEG_TO_RAD,
            pitch_deg * DEG_TO_RAD,
            yaw_deg * DEG_TO_RAD
        )
        imu.orientation = q_imu

        # Set covariance (high certainty for the fused orientation)
        imu.orientation_covariance[0] = 0.01  # Roll
        imu.orientation_covariance[4] = 0.01  # Pitch
        imu.orientation_covariance[8] = 0.05  # Yaw

        # Raw accel/gyro covariance (low certainty for raw measurements)
        imu.angular_velocity_covariance[0] = 0.01
        imu.linear_acceleration_covariance[0] = 0.1

        self.pub_imu.publish(imu)

    def _publish_mag(self, current_ros_time, mx, my, mz):
        """Publishes the MagneticField message."""
        mag = MagneticField()
        mag.header.stamp = current_ros_time
        mag.header.frame_id = "base_link"

        # Publish raw magnetometer data (conversion to Tesla is complex and often done
        # via calibration, so we publish the raw counts in a generic format for now)
        # Note: You may need to tune a conversion factor if using this data heavily.
        MOCK_CONVERSION = 1e-6
        mag.magnetic_field.x = mx * MOCK_CONVERSION
        mag.magnetic_field.y = my * MOCK_CONVERSION
        mag.magnetic_field.z = mz * MOCK_CONVERSION

        self.pub_mag.publish(mag)

    def _euler_to_quaternion(self, roll, pitch, yaw):
        """Converts Euler angles (rad) to a Quaternion object for ROS messages."""
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)

        q = Quaternion()
        q.w = cy * cp * cr + sy * sp * sr
        q.x = cy * cp * sr - sy * sp * cr
        q.y = sy * cp * sr + cy * sp * cr
        q.z = sy * cp * cr - cy * sp * sr
        return q


def main(args=None):
    rclpy.init(args=args)
    node = ArduinoBridge()
    if node.ser:
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            pass
        finally:
            node.ser.close()
            node.destroy_node()
            rclpy.shutdown()
    else:
        # Node failed to initialize due to serial error
        rclpy.shutdown()


if __name__ == '__main__':
    main()
