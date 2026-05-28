import os
import yaml
import math

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped

from tf_transformations import quaternion_from_euler
from ament_index_python.packages import get_package_share_directory
from std_msgs.msg import String


class WaypointManager(Node):

    def __init__(self):
        super().__init__('waypoint_manager')

        # Load waypoint yaml
        self.waypoints = self.load_waypoints()

        # Nav2 action client
        self.nav_client = ActionClient(
            self,
            NavigateToPose,
            '/navigate_to_pose'
        )

        # Subscriber for location commands

        self.create_subscription(
            String,
            '/go_to_location',
            self.location_callback,
            10
        )

        self.get_logger().info("Waypoint Manager Started")

    # ---------------------------------------
    # Load waypoints from yaml
    # ---------------------------------------
    def load_waypoints(self):

        package_path = get_package_share_directory('hb_nav')

        yaml_path = os.path.join(
            package_path,
            'config',
            'waypoint.yaml'
        )

        with open(yaml_path, 'r') as file:
            waypoints = yaml.safe_load(file)

        self.get_logger().info(f"Loaded {len(waypoints)} waypoints")

        return waypoints

    # ---------------------------------------
    # Go to location
    # ---------------------------------------
    def go_to_location(self, location_name):

        if location_name not in self.waypoints:
            self.get_logger().error(
                f"Waypoint '{location_name}' not found"
            )
            return

        waypoint = self.waypoints[location_name]

        x = waypoint['x']
        y = waypoint['y']
        yaw = waypoint['yaw']

        self.get_logger().info(
            f"Navigating to {location_name}"
        )

        self.send_goal(x, y, yaw)


    def location_callback(self, msg):

        location = msg.data

        self.get_logger().info(
            f"Received location: {location}"
        )

        self.go_to_location(location)    

    # ---------------------------------------
    # Send Nav2 goal
    # ---------------------------------------
    def send_goal(self, x, y, yaw):

        goal_msg = NavigateToPose.Goal()

        goal_msg.pose = PoseStamped()

        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()

        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.position.z = 0.0

        q = quaternion_from_euler(0, 0, yaw)

        goal_msg.pose.pose.orientation.x = q[0]
        goal_msg.pose.pose.orientation.y = q[1]
        goal_msg.pose.pose.orientation.z = q[2]
        goal_msg.pose.pose.orientation.w = q[3]

        self.nav_client.wait_for_server()

        self.send_goal_future = self.nav_client.send_goal_async(goal_msg)

        self.send_goal_future.add_done_callback(
            self.goal_response_callback
        )

    # ---------------------------------------
    # Goal response
    # ---------------------------------------
    def goal_response_callback(self, future):

        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().error("Goal Rejected")
            return

        self.get_logger().info("Goal Accepted")

        self.result_future = goal_handle.get_result_async()

        self.result_future.add_done_callback(
            self.goal_result_callback
        )

    # ---------------------------------------
    # Goal result
    # ---------------------------------------
    def goal_result_callback(self, future):

        result = future.result().result

        status = future.result().status

        self.get_logger().info(
            f"Navigation finished with status: {status}"
        )


# ---------------------------------------
# Main
# ---------------------------------------
def main(args=None):

    rclpy.init(args=args)

    node = WaypointManager()

    # # TEST
    # node.go_to_location("kitchen")

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()