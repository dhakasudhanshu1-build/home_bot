import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    hb_nav_dir = get_package_share_directory('hb_nav')
    
    demo_world_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(hb_nav_dir, 'launch', 'demo_world.launch.py')
        )
    )

    return LaunchDescription([
        demo_world_launch
    ])
