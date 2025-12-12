#!/usr/bin/env python3
import sys
import threading
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class KeyboardTeleop(Node):
    """
    Simple WASD teleop with 0.5s jog:
      w = forward
      s = backward
      a = rotate left
      d = rotate right
      space = stop
      q = quit

    Behavior:
      - When you press a key + Enter, the robot moves for ~0.5 seconds.
      - After 0.5 seconds it automatically sends STOP (zero Twist).
      - New key press overrides the previous command.
    """

    def __init__(self):
        super().__init__('keyboard_teleop')

        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)

        # Current command we keep publishing
        self.current_twist = Twist()
        self.lock = threading.Lock()

        # How long each command should last (seconds)
        self.command_duration = 0.5
        self.last_cmd_time = None

        # Timer: how often to (re)publish the current command
        self.timer = self.create_timer(0.1, self.timer_callback)

        # Start a separate thread to read keyboard input
        self.running = True
        self.input_thread = threading.Thread(target=self.keyboard_loop, daemon=True)
        self.input_thread.start()

        self.print_help()

    def print_help(self):
        msg = """
Keyboard Teleop (WASD, 0.5s jog):

  w = forward
  s = backward
  a = rotate left
  d = rotate right
  space = stop
  q = quit

Type a key and press Enter.
Robot moves for ~0.5s, then auto-stops unless you press another key.
"""
        self.get_logger().info(msg)

    def keyboard_loop(self):
        """
        Runs in a separate thread, reads keys from stdin.
        """
        while self.running:
            try:
                line = sys.stdin.readline()
            except Exception:
                continue

            if not line:
                time.sleep(0.1)
                continue

            key = line.strip().lower()
            if len(key) == 0:
                continue

            k = key[0]

            twist = Twist()

            # Linear and angular speeds (tune if needed)
            linear_speed = 0.25   # m/s
            angular_speed = 2.5   # rad/s

            if k == 'w':
                twist.linear.x = linear_speed
                twist.angular.z = 0.0
                self.get_logger().info("Command: FORWARD (0.5s)")
            elif k == 's':
                twist.linear.x = -linear_speed
                twist.angular.z = 0.0
                self.get_logger().info("Command: BACKWARD (0.5s)")
            elif k == 'a':
                twist.linear.x = 0.0
                twist.angular.z = +angular_speed
                self.get_logger().info("Command: TURN LEFT (0.5s)")
            elif k == 'd':
                twist.linear.x = 0.0
                twist.angular.z = -angular_speed
                self.get_logger().info("Command: TURN RIGHT (0.5s)")
            elif k == ' ':
                twist = Twist()
                self.get_logger().info("Command: STOP")
            elif k == 'q':
                self.get_logger().info("Quitting teleop, stopping robot.")
                self.running = False
                # Send a stop before exiting
                with self.lock:
                    self.current_twist = Twist()
                    self.last_cmd_time = time.time()
                self.pub.publish(self.current_twist)
                if rclpy.ok():
                    rclpy.shutdown()
                return
            else:
                self.get_logger().info(f"Unknown key '{k}'. Use w/s/a/d, space, or q.")
                continue

            # Update the current twist and timestamp
            now = time.time()
            with self.lock:
                self.current_twist = twist
                self.last_cmd_time = now

    def timer_callback(self):
        """
        Periodically publish the current Twist command.
        Auto-zero it if 0.5s have passed since last key press.
        """
        now = time.time()
        with self.lock:
            # If we have a last command time and 0.5s have passed, auto-stop
            if self.last_cmd_time is not None:
                if (now - self.last_cmd_time) > self.command_duration:
                    self.current_twist = Twist()
            cmd = self.current_twist

        self.pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = KeyboardTeleop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Make sure robot is stopped on exit
        stop = Twist()
        node.pub.publish(stop)
        node.running = False
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
