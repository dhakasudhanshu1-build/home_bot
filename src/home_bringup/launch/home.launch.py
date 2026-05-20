import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    hb_w_dir = get_package_share_directory('hb_w')
    
    home_sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(hb_w_dir, 'launch', 'home_sim.launch.py')
        )
    )

    return LaunchDescription([
        home_sim_launch
    ])
