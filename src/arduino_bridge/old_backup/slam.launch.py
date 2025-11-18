from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        
        # --- Static transform: base_link -> laser ---
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0.11', '0.11', '0.08', '0', '0', '0', 'base_link', 'laser']
        ),

        # --- SLAM Toolbox ---
        Node(
            package='slam_toolbox',
            executable='sync_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=["/opt/ros/jazzy/share/slam_toolbox/config/mapper_params_online_async.yaml"]
        ),
    ])
