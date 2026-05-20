import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():

    pkg_nav = get_package_share_directory('hb_nav')
    pkg_joy = get_package_share_directory('control_joy')

    # Path to original Gazebo world launch
    demo_world_launch = os.path.join(
        pkg_nav,
        'launch',
        'demo_world.launch.py'
    )

    # Path to joystick launch
    joy_control_launch = os.path.join(
        pkg_joy,
        'launch',
        'joy_controler.launch.py'
    )

    # Path to RViz config
    rviz_config_file = os.path.join(
        pkg_nav,
        'rviz',
        'sim.rviz'
    )

    # Include Demo World Launch
    demo_world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(demo_world_launch)
    )

    # Include Joystick Launch
    joy_control = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(joy_control_launch)
    )

    # RViz Node
    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    return LaunchDescription([
        demo_world,
        
        # Start joystick slightly delayed to ensure bridge is up
        TimerAction(
            period=2.0,
            actions=[joy_control]
        ),
        
        # Start RViz
        TimerAction(
            period=3.0,
            actions=[rviz2]
        )
    ])
