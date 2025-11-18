import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # Get the path to the robot_description package
    pkg_path = get_package_share_directory('robot_description')
    
    # Locate the XACRO file we created in Step 2.3
    xacro_file = os.path.join(pkg_path, 'urdf', 'robot.urdf.xacro')

    # Read the content of the XACRO file into a string
    with open(xacro_file, 'r') as infp:
        robot_desc = infp.read()
    
    # 1. Robot State Publisher Node
    # This node reads the robot_desc (URDF) and publishes the fixed transforms (/tf)
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        # Pass the model string to the node as a parameter
        parameters=[{'robot_description': robot_desc}],
    )
    
    return LaunchDescription([
        robot_state_publisher_node,
    ])
