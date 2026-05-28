import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    # PACKAGE PATH
    pkg_share = get_package_share_directory('hb_nav')

    # MAP FILE PATH
    map_file = os.path.join(
        pkg_share,
        'maps',
        'home2map.yaml'
    )

    # RVIZ CONFIG PATH
    rviz_config = os.path.join(
        pkg_share,
        'rviz',
        'sim.rviz'
    )

    # MAP SERVER NODE
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[
            {'use_sim_time': True},
            {'yaml_filename': map_file}
        ]
    )

    # LIFECYCLE MANAGER
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_map',
        output='screen',
        parameters=[
            {'use_sim_time': True},
            {'autostart': True},
            {'node_names': ['map_server']}
        ]
    )

    # RVIZ
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[
            {'use_sim_time': True}
        ]
    )

    return LaunchDescription([

        map_server,
        lifecycle_manager,
        rviz

    ])