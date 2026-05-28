import time
import json

import rclpy
from rclpy.node import Node

from std_msgs.msg import String


class TaskExecutor(Node):

    def __init__(self):
        super().__init__('task_executor')

        
        self.location_publisher = self.create_publisher(
            String,
            '/go_to_location',
            10
        )

        self.get_logger().info("Task Executor Started")


    def execute_tasks(self, tasks):

        for task in tasks:

            action = task['action']


            if action == 'go_to':

                location = task['location']
                self.get_logger().info(
                    f"Going to {location}"
                )
                msg = String()
                msg.data = location
                self.location_publisher.publish(msg)
                time.sleep(15)

            elif action == 'wait':
                duration = task['duration']
                self.get_logger().info(
                    f"Waiting for {duration} seconds"
                )
                time.sleep(duration)

            else:
                self.get_logger().warn(
                    f"Unknown action: {action}"
                )


        self.get_logger().info(
            "All tasks completed"
        )



def main(args=None):

    rclpy.init(args=args)

    node = TaskExecutor()

    # TEST TASKS
    tasks = [

        {
            "action": "go_to",
            "location": "kitchen"
        },

        {
            "action": "wait",
            "duration": 5
        },

        {
            "action": "go_to",
            "location": "room1"
        }

    ]

    node.execute_tasks(tasks)

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()