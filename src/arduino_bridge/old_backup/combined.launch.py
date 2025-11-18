from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    pkg_share = get_package_share_directory('arduino_bridge')
    ekf_path = os.path.join(pkg_share, 'config', 'ekf.yaml')

    return LaunchDescription([

        # ---- SERIAL NODE ----
        Node(
            package='arduino_bridge',
            executable='serial_node',
            name='serial_node',
            output='screen'
        ),

        # ---- EKF NODE ----
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_node',
            output='screen',
            parameters=[ekf_path]
        ),

        # ---- LIDAR NODE ----
        Node(
            package='sllidar_ros2',
            executable='sllidar_node',
            name='sllidar_node',
            output='screen',
            parameters=[
                {
                    'channel_type': 'serial',
                    'serial_port': '/dev/ttyUSB0',
                    'serial_baudrate': 256000,
                    'frame_id': 'laser',
                    'inverted': False,
                    'angle_compensate': True,
                    'scan_mode': 'Standard'
                }
            ]
        ),

        # ---- STATIC TF  ----
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='laser_tf',
            arguments=["0.11", "0.11", "0.08", "0", "0", "0", "base_link", "laser"]
        ),

        # ---- SLAM TOOLBOX ----
        Node(
            package='slam_toolbox',
            executable='sync_slam_toolbox_node',
            name='slam_toolbox',
            output='screen'
        ),
    ])
