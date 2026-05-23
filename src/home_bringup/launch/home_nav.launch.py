import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    hb_w_dir = get_package_share_directory('hb_w')

    rviz_config = os.path.join(
    get_package_share_directory('hb_nav'),
    'rviz',
    'nav2.rviz'
)
    
    home_sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(hb_w_dir, 'launch', 'home_sim.launch.py')
        )
    )
    amcl_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('hb_nav'), 'launch', 'amcl.launch.py')
        )
    )
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('hb_nav'), 'launch', 'nav2.launch.py')
        )
    )
    rviz = Node(
    package='rviz2',
    executable='rviz2',
    name='rviz2',
    output='screen',
    arguments=['-d', rviz_config]
)

    return LaunchDescription([
    home_sim_launch,

    TimerAction(
        period=8.0,
        actions=[amcl_launch]
    ),

    TimerAction(
        period=12.0,
        actions=[nav2_launch]
    ),

    TimerAction(
        period=15.0,
        actions=[rviz]
    )
])