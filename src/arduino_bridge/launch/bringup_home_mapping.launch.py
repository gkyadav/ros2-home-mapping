from launch import LaunchDescription
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    # Paths to config files
    pkg_share = get_package_share_directory('arduino_bridge')

    ekf_params = os.path.join(pkg_share, 'config', 'ekf.yaml')
    slam_params = os.path.join(pkg_share, 'config', 'slam_params.yaml')

    # -------------------------
    # 1. Serial Node (Arduino)
    # -------------------------
    serial_node = Node(
        package='arduino_bridge',
        executable='serial_node',
        name='serial_node',
        output='screen'
    )

    # -------------------------
    # 2. EKF Node (robot_localization)
    # -------------------------
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_params]
    )

    # ------------------------------------
    # 3. LiDAR Node (Slamtec C1 – sllidar)
    # ------------------------------------
    lidar_node = Node(
        package='sllidar_ros2',
        executable='sllidar_node',
        name='sllidar_node',
        output='screen',
        parameters=[{
            "serial_port": "/dev/ttyUSB0",
            "serial_baudrate": 460800,
            "frame_id": "laser",
            "angle_compensate": True
        }]
    )

    # --------------------------------------
    # 4. Static TF (base_link → laser)
    # --------------------------------------
    static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_to_laser',
        arguments=[
            "0.16",     # x
            "0.16",     # y
            "0.14",     # z
            "0", "0", "0",  # roll pitch yaw
            "base_link",
            "laser"
        ]
    )

    # --------------------------------------
    # 5. SLAM Toolbox (Lifecycle Node)
    # --------------------------------------
    slam_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[slam_params]
    )

    # -------------------------------------------------
    # 6. Lifecycle Manager for SLAM (auto activate it)
    # -------------------------------------------------
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_slam',
        output='screen',
        parameters=[{
            'autostart': True,
            'node_names': ['slam_toolbox'],
            'use_sim_time': False
        }]
    )

    return LaunchDescription([
        serial_node,
        ekf_node,
        lidar_node,
        static_tf,
        slam_node,
        lifecycle_manager
    ])
