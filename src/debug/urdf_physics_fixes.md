# URDF & Gazebo Physics Debugging Log

This document tracks the critical changes made to the `home_botv2_description` URDF and Gazebo configurations to resolve odometry drift, physics instability, and RViz/Gazebo mismatches.

## 1. Wheel Collision Cylinders Orientation
*   **Change:** Rotated the wheel collision cylinders by 90 degrees (`1.5708` rad) around the X-axis (`rpy="1.5708 0 0"` and `-1.5708 0 0`) in `home_botv2.xacro`.
*   **Why:** In URDF, a cylinder primitive is aligned with the Z-axis by default. However, the differential drive wheel joints rotate around the Y-axis. Without this rotation, Gazebo was trying to roll the robot on the flat circular faces of the cylinders instead of the curved edges. This caused completely broken wheel physics, reverse turning behavior, and heavily corrupted odometry.

## 2. Leveled Robot Chassis (Caster Z-origin Fix)
*   **Change:** Lowered the left and right caster joints (`Rigid_3`, `Rigid_4`) Z-origin from `-0.005m` to `-0.02m` in `home_botv2.xacro`.
*   **Why:** There was a `15mm` height discrepancy between the front and back wheels:
    *   Bottom of drive wheels relative to `base_link`: `Joint Z (0.02m) - Radius (0.06m) = -0.04m`
    *   Bottom of casters (Before): `Joint Z (-0.005m) - Radius (0.02m) = -0.025m`
    Because the casters were higher, gravity forced the entire robot chassis to permanently tilt forward. When a tilted robot rotates, the drive wheels don't turn on a flat 2D plane; they fight the angle of the ground, causing microscopic but continuous slipping. The Ignition DiffDrive plugin assumes perfect grip on a flat plane, so this slip caused the physical robot in Gazebo to rotate slower than the odometry reported, leading to the massive RViz/Gazebo drift.

## 3. LiDAR Update Rate & Samples Optimization
*   **Change:** Increased the `gpu_lidar` plugin `<update_rate>` from `10` to `20` Hz, and decreased `<samples>` from `640` to `320` in `home_botv2.xacro`.
*   **Why:** SLAM Toolbox relies heavily on fast, accurate laser scans to correct minor odometry drift via scan matching. At `10` Hz, the robot rotates significantly between scans, causing "motion blur". Increasing it to `20` Hz provides the SLAM algorithm with denser data. Dropping samples to `320` cut the GPU/CPU rendering workload in half, preventing Gazebo from lagging.

## 4. Odometry Publish Rate Explicit Definition
*   **Change:** Added `<odom_publish_frequency>50</odom_publish_frequency>` to the Ignition DiffDrive plugin in `home_botv2.gazebo`.
*   **Why:** Without explicitly defining the publish rate, the Ignition plugin might publish odometry erratically or at the extremely high physics simulation step rate. This can flood the `ros_gz_bridge` and the ROS 2 TF tree. Enforcing a strict 50Hz rate provides a smooth, reliable odometry stream required by Nav2 and SLAM Toolbox.

## 5. Wheel Friction Coefficients 
*   **Change:** Set drive wheels `mu1`/`mu2` to `1.0` (high friction) and caster links `mu1`/`mu2` to `0.00` (zero friction) in `home_botv2.gazebo`.
*   **Why:** The mathematical model for a differential drive robot assumes the drive wheels do not slip sideways, and the casters offer zero resistance to turning. If the casters had friction, they would act like anchors, fighting the drive wheels during rotation and causing further odometry slip.

## 6. Removed Duplicate joint_state_publisher
*   **Change:** Cleaned up launch files to ensure only one `joint_state_publisher` is active.
*   **Why:** Having duplicate publishers broadcasting the wheel joints causes the TF tree to constantly jump back and forth in time. This time jitter breaks RViz visualization and causes SLAM algorithms to throw "Extrapolation into the past/future" TF errors.

## 7. Corrected CAD Inertia Tensors
*   **Change:** Recalculated `ixx`, `iyy`, `izz` for all links using geometric primitives based on actual masses and dimensions. For example, `base_link`'s `izz` dropped from `6.33` to `0.072`.
*   **Why:** CAD software often exports inertias relative to wrong origins or in `grams * mm^2`. The physically impossible inertias made the robot act like it was made of super-dense dark matter. The drive wheels did not have enough grip to rotate a `6.33 kg*m^2` mass, causing them to constantly slip in Gazebo. RViz saw the wheels turning and assumed the robot moved, completely destroying the odometry tracking.

## 8. Fixed LiDAR Self-Collision and Minimum Range (Map Jumping)
*   **Change:** Set `self_collide="false"` on all structural links (`tower_link`, `lidar_link`, `camera_link`). Increased LiDAR `<min>` range from `0.08m` to `0.30m`.
*   **Why:** The laser rays were originating from the center of the `lidar_link` and immediately hitting the robot's own collision meshes. This created a "fake circular wall" of laser points that followed the robot perfectly. SLAM Toolbox got confused trying to match the moving real walls to the static fake walls, causing the map to jitter and jump violently.

## 9. Added Acceleration Limits and Increased Wheel Stiffness
*   **Change:** Added `<max_linear_acceleration>` and `<max_angular_acceleration>` to the `DiffDrive` plugin. Increased `<kp>` (contact stiffness) from `50000.0` to `1000000.0` on all wheels.
*   **Why:** Without acceleration limits, joystick commands applied infinite instantaneous torque to the wheels, causing the robot to violently skid or jerk. The soft `kp` value made the wheels act like rubber balls, causing the robot to bounce and lose traction. Stiffening the wheels and limiting acceleration smoothed out the driving mechanics.

## 10. Fixed `base_link` Collision Box Dragging & Clipping
*   **Change:** Removed the `rpy="0 0 1.5708"` 90-degree Z-rotation from the `base_link` collision geometry, and shifted its Z `<origin>` to `0.05m`.
*   **Why:** The 90-degree rotation accidentally rotated the `0.45m` box length into the robot's Y-axis. Since the wheels are only `0.34m` apart, the invisible collision box stuck out 5cm past the wheels on both sides, causing the robot to clip into obstacles and spin out of control. Furthermore, without the Z-shift, the bottom of the box was `2cm` deeper than the wheels, causing the robot to drag its belly on the ground and get stuck.
