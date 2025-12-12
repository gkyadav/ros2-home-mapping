from launch import LaunchDescription
from launch_ros.actions import Node
import os


def generate_launch_description():
    # Path to slam_params.yaml (relative to this launch file)
    slam_params_file = os.path.join(
        os.path.dirname(__file__),   # .../arduino_bridge/launch
        '..',                        # .../arduino_bridge
        'config',                    # .../arduino_bridge/config
        'slam_params.yaml'           # file we created
    )

    slam_params_file = os.path.normpath(slam_params_file)

    slam_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',   # or 'sync_slam_toolbox_node' if you prefer
        name='slam_toolbox',
        output='screen',
        parameters=[slam_params_file],
    )

    # Lifecycle manager to automatically configure + activate slam_toolbox
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_slam',
        output='screen',
        parameters=[{
            'autostart': True,
            'node_names': ['slam_toolbox'],
        }]
    )

    # 👇 Both nodes are launched: slam_toolbox + its lifecycle manager
    return LaunchDescription([
        slam_node,
        lifecycle_manager,
    ])
