

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_robot = get_package_share_directory('home_botv2_description')
    pkg_nav = get_package_share_directory('hb_nav')
    pkg_joy = get_package_share_directory('control_joy')
    pkg_w = get_package_share_directory('hb_w')

    # 1. World File — Ignition-native SDF (no external model dependencies)
    world_file = os.path.join(pkg_w, 'worlds', 'office_small.sdf')

    # 2. Robot Description
    robot_description_file = os.path.join(
        pkg_robot,
        'urdf',
        'home_botv2.xacro'
    )
    robot_description_config = xacro.process_file(robot_description_file)
    robot_description = {'robot_description': robot_description_config.toxml()}

    # 3. Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")),
        launch_arguments={"gz_args": f"-r -v 4 {world_file}"}.items()
    )

    # 4. Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description, {'use_sim_time': True}]
    )

    # 5. Spawn Robot
    spawn_robot = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                arguments=[
                    "-topic", "/robot_description",
                    "-name", "home_botv2",
                    "-x", "0.0",
                    "-y", "0.0",
                    "-z", "0.3"
                ],
                output='screen'
            )
        ]
    )

    # 6. ROS-Gazebo Bridge
    ros_gz_bridge_config = os.path.join(pkg_robot, 'config', 'ros_gz_bridge_gazebo.yaml')
    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': ros_gz_bridge_config, 'use_sim_time': True}],
        output='screen'
    )

    # 7. Joystick
    joy_control = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_joy, 'launch', 'joy_controler.launch.py'))
    )

    # 8. RViz
    # rviz_config_file = os.path.join(pkg_nav, 'rviz', 'sim.rviz')
    # rviz2 = Node(
    #     package='rviz2',
    #     executable='rviz2',
    #     name='rviz2',
    #     arguments=['-d', rviz_config_file],
    #     parameters=[{'use_sim_time': True}],
    #     output='screen'
    # )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_robot,
        ros_gz_bridge,
        TimerAction(period=2.0, actions=[joy_control])
        # TimerAction(period=3.0, actions=[rviz2])
    ])
