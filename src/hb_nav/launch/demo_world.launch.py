import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro
from os.path import join

def generate_launch_description():

    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    pkg_robot = get_package_share_directory(
        'home_botv2_description'
    )

    pkg_nav = get_package_share_directory(
        'hb_nav'
    )

    # WORLD
    world_file = os.path.join(
        pkg_nav,
        'worlds',
        'demo.sdf'
    )

    # ROBOT
    robot_description_file = os.path.join(
        pkg_robot,
        'urdf',
        'home_botv2.xacro'
    )

    ros_gz_bridge_config = os.path.join(
        pkg_robot,
        'config',
        'ros_gz_bridge_gazebo.yaml'
    )

    robot_description_config = xacro.process_file(
        robot_description_file
    )

    robot_description = {
        'robot_description':
        robot_description_config.toxml()
    }

    # ROBOT STATE PUBLISHER
    robot_state_publisher = Node(
    package='robot_state_publisher',
    executable='robot_state_publisher',
    output='screen',
    parameters=[
        robot_description,
        {'use_sim_time': True}
    ],
    )

    # GAZEBO
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            join(
                pkg_ros_gz_sim,
                "launch",
                "gz_sim.launch.py"
            )
        ),
        launch_arguments={
            "gz_args": f"-r -v 4 {world_file}"
        }.items()
    )

    # SPAWN ROBOT
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

    # BRIDGE
    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': ros_gz_bridge_config
        }],
        output='screen'
    )

    # CONTROLLERS
    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen",
    )

    diff_drive_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_cont"],
        output="screen",
    )

    return LaunchDescription([

        gazebo,

        robot_state_publisher,

        spawn_robot,

        ros_gz_bridge,

        TimerAction(
            period=8.0,
            actions=[joint_state_broadcaster]
        ),

        TimerAction(
            period=10.0,
            actions=[diff_drive_controller]
        ),
    ])