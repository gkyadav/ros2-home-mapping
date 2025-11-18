from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    ekf_config = "/home/makermatics/ros2_ws/src/arduino_bridge/config/ekf.yaml"

    return LaunchDescription([
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[ ekf_config ]
        )
    ])
