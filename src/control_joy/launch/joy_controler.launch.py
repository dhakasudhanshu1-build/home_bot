import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    

    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[{
            'deadzone': 0.05,
            'autorepeat_rate': 20.0,
        }]
    )


    custom_joy_to_twist = Node(
        package='control_joy',
        executable='joy_controler',
        name='vel_ctrl_joy',
        output='screen'
    )

    return LaunchDescription([
        joy_node,
        custom_joy_to_twist
    ])