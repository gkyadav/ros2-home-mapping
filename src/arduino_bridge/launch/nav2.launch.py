import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')

    # Nav2 bringup launch file
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    bringup_launch = os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')

    # Your package's Nav2 params
    my_pkg_dir = get_package_share_directory('arduino_bridge')
    nav2_params = os.path.join(my_pkg_dir, 'config', 'nav2_params.yaml')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'
        ),
        DeclareLaunchArgument(
            'autostart',
            default_value='true',
            description='Automatically startup the nav2 stack'
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(bringup_launch),
            launch_arguments={
                # Use *your* params file
                'params_file': nav2_params,
                # Time / startup
                'use_sim_time': use_sim_time,
                'autostart': autostart,
                # We already have slam_toolbox running separately, so:
                'slam': 'False',
                'use_localization': 'False',
                # No static map yaml (map is coming from SLAM)
                'map': '',
            }.items()
        ),
    ])
