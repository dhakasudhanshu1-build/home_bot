from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    pkg_share = get_package_share_directory('hb_nav')

    nav2_params = os.path.join(
        pkg_share,
        'config',
        'nav2.yaml'
    )
    # amcl_params = os.path.join(
    #     pkg_share,
    #     'config',
    #     'amcl.yaml'
    # )

    # map_file = os.path.join(
    #     pkg_share,
    #     'maps',
    #     'home_map.yaml'
    # )

    # MAP SERVER
    # map_server = Node(
    #     package='nav2_map_server',
    #     executable='map_server',
    #     name='map_server',
    #     output='screen',
    #     parameters=[
    #         {'yaml_filename': map_file},
    #         {'use_sim_time': True}
    #     ]
    # )

    # AMCL
    # amcl = Node(
    #     package='nav2_amcl',
    #     executable='amcl',
    #     name='amcl',
    #     output='screen',
    #     parameters=[amcl_params]
    # )

    # CONTROLLER SERVER
    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        output='screen',
        parameters=[nav2_params]
    )

    # PLANNER SERVER
    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[nav2_params]
    )

    # BEHAVIOR SERVER
    behavior_server = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[nav2_params]
    )

    # BT NAVIGATOR
    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[nav2_params]
    )

    # WAYPOINT FOLLOWER
    waypoint_follower = Node(
        package='nav2_waypoint_follower',
        executable='waypoint_follower',
        name='waypoint_follower',
        output='screen',
        parameters=[nav2_params]
    )

    # SMOOTHER SERVER
    smoother_server = Node(
        package='nav2_smoother',
        executable='smoother_server',
        name='smoother_server',
        output='screen',
        parameters=[nav2_params]
    )

    # VELOCITY SMOOTHER
    velocity_smoother = Node(
        package='nav2_velocity_smoother',
        executable='velocity_smoother',
        name='velocity_smoother',
        output='screen',
        parameters=[nav2_params]
    )

    # LIFECYCLE MANAGER
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[
            {'use_sim_time': True},
            {'autostart': True},
            {
                'node_names': [
                    # 'map_server',
                    # 'amcl',
                    'controller_server',
                    'planner_server',
                    'behavior_server',
                    'bt_navigator',
                    'waypoint_follower',
                    'smoother_server',
                    'velocity_smoother'
                ]
            }
        ]
    )

    return LaunchDescription([

        # map_server,
        # amcl,

        controller_server,
        planner_server,
        behavior_server,
        bt_navigator,

        waypoint_follower,
        smoother_server,
        velocity_smoother,

        lifecycle_manager
    ])