from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    slam_params_file = LaunchConfiguration('slam_params_file')

    slam_params_arg = DeclareLaunchArgument(
        'slam_params_file',
        default_value=PathJoinSubstitution(
            [FindPackageShare('ros2-home-mapping'), 'config', 'slam_lidar_only.yaml']
        ),
        description='Full path to slam_toolbox params file'
    )

    # 1) Static TF: base_link -> laser_frame
    # Replace 'laser_frame' with whatever frame_id /scan uses
    static_tf_laser = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_to_laser_tf',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'laser_frame']
    )

    # 2) SLAM toolbox node
    slam_node = Node(
        package='slam_toolbox',
        executable='sync_slam_toolbox_node',
        name='slam_toolbox',
        parameters=[slam_params_file],
        output='screen',
    )

    return LaunchDescription([
        slam_params_arg,
        static_tf_laser,
        slam_node,
    ])
