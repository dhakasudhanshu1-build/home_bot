import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseWithCovarianceStamped
from sensor_msgs.msg import Image
from nav_msgs.msg import OccupancyGrid, Odometry
from cv_bridge import CvBridge
import cv2
import numpy as np
import base64
import math
import time
import json
import threading
import asyncio

class DashboardNode(Node):
    def __init__(self):
        super().__init__('hb_dashboard_node')
        self.get_logger().info('Dashboard Node initialized')

        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # --- Camera ---
        self.bridge = CvBridge()
        self.latest_frame_b64 = None
        self._camera_clients = []
        self._camera_lock = threading.Lock()
        self.create_subscription(Image, '/camera/image_raw', self._camera_callback, 10)

        # --- Map ---
        self._map_data = None          # dict with map metadata + base64 PNG
        self._map_clients = []         # asyncio queues for map WS clients
        self._map_lock = threading.Lock()
        self.create_subscription(OccupancyGrid, '/map', self._map_callback, 10)

        # --- Robot Pose ---
        self._pose = None              # dict {x, y, yaw}
        self._last_pose_push = 0.0
        self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self._amcl_callback, 10)
        self.create_subscription(Odometry, '/odom', self._odom_callback, 10)

        self.get_logger().info('All subscribers initialized')

    # ==================== CMD VEL ====================
    def publish_cmd_vel(self, linear_x: float, angular_z: float):
        msg = Twist()
        msg.linear.x = float(linear_x)
        msg.angular.z = float(angular_z)
        self.cmd_vel_pub.publish(msg)

    # ==================== CAMERA ====================
    def _camera_callback(self, msg: Image):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            _, jpeg_buf = cv2.imencode('.jpg', cv_image, [cv2.IMWRITE_JPEG_QUALITY, 60])
            b64_str = base64.b64encode(jpeg_buf.tobytes()).decode('utf-8')
            with self._camera_lock:
                self.latest_frame_b64 = b64_str
                for q in self._camera_clients:
                    try:
                        q.put_nowait(b64_str)
                    except asyncio.QueueFull:
                        try: q.get_nowait()
                        except asyncio.QueueEmpty: pass
                        q.put_nowait(b64_str)
        except Exception as e:
            self.get_logger().warn(f'Camera frame error: {e}')

    def register_camera_client(self):
        q = asyncio.Queue(maxsize=2)
        with self._camera_lock:
            self._camera_clients.append(q)
        return q

    def unregister_camera_client(self, q):
        with self._camera_lock:
            if q in self._camera_clients:
                self._camera_clients.remove(q)

    # ==================== MAP ====================
    def _map_callback(self, msg: OccupancyGrid):
        try:
            w, h = msg.info.width, msg.info.height
            data = np.array(msg.data, dtype=np.int8).reshape(h, w)

            # Convert occupancy values to grayscale pixels
            img = np.full((h, w), 128, dtype=np.uint8)  # default unknown=gray
            free = data == 0
            occupied = data == 100
            known = (data >= 0) & (data <= 100)
            img[free] = 255
            img[occupied] = 0
            img[known & ~free & ~occupied] = (255 - (data[known & ~free & ~occupied].astype(np.float32) * 255.0 / 100.0)).astype(np.uint8)

            # Flip Y (ROS origin is bottom-left, canvas is top-left)
            img = np.flipud(img)

            _, png_buf = cv2.imencode('.png', img)
            b64_png = base64.b64encode(png_buf.tobytes()).decode('utf-8')

            origin = msg.info.origin.position
            q = msg.info.origin.orientation
            origin_yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))

            map_msg = {
                "type": "map",
                "width": w,
                "height": h,
                "resolution": msg.info.resolution,
                "origin_x": origin.x,
                "origin_y": origin.y,
                "origin_yaw": origin_yaw,
                "data": b64_png
            }

            with self._map_lock:
                self._map_data = map_msg
                json_str = json.dumps(map_msg)
                for mq in self._map_clients:
                    try: mq.put_nowait(json_str)
                    except asyncio.QueueFull:
                        try: mq.get_nowait()
                        except asyncio.QueueEmpty: pass
                        mq.put_nowait(json_str)

            self.get_logger().info(f'Map received: {w}x{h}, res={msg.info.resolution}', throttle_duration_sec=10.0)
        except Exception as e:
            self.get_logger().error(f'Map processing error: {e}')

    # ==================== POSE ====================
    def _quat_to_yaw(self, q):
        return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))

    def _push_pose(self, x, y, yaw):
        now = time.time()
        if now - self._last_pose_push < 0.1:  # throttle to ~10Hz
            return
        self._last_pose_push = now
        pose_msg = json.dumps({"type": "pose", "x": x, "y": y, "yaw": yaw})
        with self._map_lock:
            self._pose = {"x": x, "y": y, "yaw": yaw}
            for mq in self._map_clients:
                try: mq.put_nowait(pose_msg)
                except asyncio.QueueFull:
                    try: mq.get_nowait()
                    except asyncio.QueueEmpty: pass
                    mq.put_nowait(pose_msg)

    def _amcl_callback(self, msg: PoseWithCovarianceStamped):
        p = msg.pose.pose
        self._push_pose(p.position.x, p.position.y, self._quat_to_yaw(p.orientation))

    def _odom_callback(self, msg: Odometry):
        p = msg.pose.pose
        self._push_pose(p.position.x, p.position.y, self._quat_to_yaw(p.orientation))

    # ==================== MAP CLIENT MANAGEMENT ====================
    def register_map_client(self):
        q = asyncio.Queue(maxsize=5)
        with self._map_lock:
            self._map_clients.append(q)
        return q

    def unregister_map_client(self, q):
        with self._map_lock:
            if q in self._map_clients:
                self._map_clients.remove(q)

    def get_latest_map_json(self):
        with self._map_lock:
            if self._map_data:
                return json.dumps(self._map_data)
        return None


def spin_node(node):
    rclpy.spin(node)

_node_instance = None

def get_node():
    return _node_instance

def init_ros():
    global _node_instance
    if not rclpy.ok():
        rclpy.init()
    _node_instance = DashboardNode()
    thread = threading.Thread(target=spin_node, args=(_node_instance,), daemon=True)
    thread.start()
