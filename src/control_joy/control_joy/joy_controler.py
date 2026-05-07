import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist

class JoyToTwistNode(Node):
    def __init__(self):
        super().__init__('vel_ctrl_joy')
        self.subscription = self.create_subscription(
            Joy,
            'joy',
            self.joy_callback,
            10)
        self.publisher = self.create_publisher(
            Twist,
            '/diff_cont/cmd_vel_unstamped',
            10
        )
        self.get_logger().info('Joy to Twist node started.')

    def joy_callback(self, msg: Joy):
        twist = Twist()
        # Map joystick axes to Twist message
        twist.linear.x = msg.axes[1] * 3  # Assuming forward/backward on left stick Y-axis
        twist.angular.z = msg.axes[3] * 2.5  # Assuming left/right on left stick X-axis
        self.publisher.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = JoyToTwistNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()