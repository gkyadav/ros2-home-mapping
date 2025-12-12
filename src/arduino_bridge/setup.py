import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'arduino_bridge'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        # Required for ament index
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),

        # Package manifest
        ('share/' + package_name, ['package.xml']),

        # Install all launch files (e.g. launch/ekf.launch.py)
        (os.path.join('share', package_name, 'launch'),
         glob('launch/*.launch.py')),

        # Install all config files (e.g. config/ekf.yaml)
        (os.path.join('share', package_name, 'config'),
         glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='makermatics',
    maintainer_email='makermatics@todo.todo',
    description='Arduino to ROS 2 bridge for IMU, magnetometer and wheel encoder data.',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # Your serial bridge node
            'serial_node = arduino_bridge.serial_node:main',
            'keyboard_teleop = arduino_bridge.keyboard_teleop_node:main',
        ],
    },
)
