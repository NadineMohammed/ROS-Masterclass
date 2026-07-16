# my_robot_description — Session 6: Complete Robot Simulation Using TF & Gazebo Plugins

## 1. Project Overview

This package contains a complete ROS 2 simulation of a two-wheeled differential-drive
mobile robot with a caster wheel, a 2D LiDAR sensor, and an RGB camera. It builds on
the URDF/Xacro robot description created in the previous assignment by adding:

- Gazebo simulation plugins (Differential Drive, Joint State Publisher, Odometry Publisher)
- A LiDAR sensor plugin publishing `/scan`
- An RGB camera sensor plugin publishing `/camera/image_raw`
- A ROS–Gazebo bridge configuration (`gz_bridge.yaml`)
- Two launch files: one for RViz-only visualization (`display.launch.py`) and one for
  full Gazebo simulation with RViz (`gazebo.launch.py`)
- A saved RViz configuration (`robot_view.rviz`) showing RobotModel, TF, LaserScan,
  and the live camera feed
- A fully connected TF tree with no missing or disconnected frames

The robot can be driven using `/cmd_vel`, and both its LiDAR and camera data can be
visualized live in RViz while the simulation runs in Gazebo.

## 2. Package Structure

```
my_robot_description/
├── urdf/
│   ├── robot.urdf.xacro        # Main robot description (links, joints, sensors geometry)
│   └── robot.gazebo.xacro      # Gazebo plugins: DiffDrive, JointStatePublisher,
│                                  OdometryPublisher, LiDAR sensor, Camera sensor
├── meshes/
│   ├── lidar.STL                # LiDAR visual mesh
│   └── zed.stl                  # Camera visual mesh
├── config/
│   └── gz_bridge.yaml           # ROS <-> Gazebo topic bridge configuration
├── launch/
│   ├── display.launch.py        # RViz + robot_state_publisher + joint_state_publisher_gui
│   └── gazebo.launch.py         # Full Gazebo simulation + bridge + RViz
├── rviz/
│   └── robot_view.rviz          # Saved RViz display configuration
├── screenshots/                 # Proof-of-work screenshots (see below)
├── videos/
│   └── TestVideo.mp4            # Demonstration video of the robot moving in Gazebo
├── package.xml
├── CMakeLists.txt
└── README.md
```

## 3. Linux Commands Used

```bash
# Navigate to workspace
cd ~/workspaces/my_robot_ws

# Check running nodes / processes
ros2 node list
ps aux | grep gz
top
free -h
```

## 4. ROS 2 Commands Used

```bash
# Build the package
colcon build --packages-select my_robot_description
source install/setup.bash

# Confirm package is discoverable
ros2 pkg prefix my_robot_description

# Launch RViz-only visualization (no physics/Gazebo)
ros2 launch my_robot_description display.launch.py

# Launch full Gazebo simulation with RViz
ros2 launch my_robot_description gazebo.launch.py

# Inspect topics
ros2 topic list
ros2 topic echo /joint_states
ros2 topic echo /scan
ros2 topic echo /camera/image_raw
ros2 topic hz /scan

# Verify the TF tree
ros2 run tf2_tools view_frames

# Move the robot
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}, angular: {z: 0.0}}"
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## 5. How to Launch RViz

```bash
cd ~/workspaces/my_robot_ws
source install/setup.bash
ros2 launch my_robot_description display.launch.py
```

This starts `robot_state_publisher`, `joint_state_publisher_gui` (manual sliders for
each wheel joint), and RViz with the saved `robot_view.rviz` configuration loaded.
No Gazebo/physics is running in this mode — it is used purely to verify the robot
model and TF tree.

## 6. How to Launch Gazebo

```bash
cd ~/workspaces/my_robot_ws
source install/setup.bash
ros2 launch my_robot_description gazebo.launch.py
```

This starts:
1. Gazebo (`turtlebot3_house.world`)
2. `robot_state_publisher` (with `use_sim_time` enabled)
3. The robot spawn node
4. The `ros_gz_bridge` (using `gz_bridge.yaml`)
5. RViz (with the same saved configuration, now showing live `/scan` and
   `/camera/image_raw` data since the sensors are active)

## 7. Expected Topics

| Topic | Type | Direction | Purpose |
|---|---|---|---|
| `/cmd_vel` | `geometry_msgs/msg/Twist` | ROS → Gazebo | Drive command input |
| `/odom` | `nav_msgs/msg/Odometry` | Gazebo → ROS | Estimated robot odometry |
| `/tf` | `tf2_msgs/msg/TFMessage` | Gazebo → ROS | Transform tree updates |
| `/joint_states` | `sensor_msgs/msg/JointState` | Gazebo → ROS | Wheel joint positions/velocities |
| `/scan` | `sensor_msgs/msg/LaserScan` | Gazebo → ROS | LiDAR distance readings |
| `/camera/image_raw` | `sensor_msgs/msg/Image` | Gazebo → ROS | RGB camera image stream |
| `/clock` | `rosgraph_msgs/msg/Clock` | Gazebo → ROS | Simulation time source |

## 8. How to Move the Robot

With `gazebo.launch.py` running, open a second terminal:

```bash
source ~/workspaces/my_robot_ws/install/setup.bash
```

**Single nudge (one command, robot moves briefly then stops):**
```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

**Continuous movement (keeps moving until Ctrl+C, then send a zero command to stop):**
```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}, angular: {z: 0.0}}"
# Ctrl+C, then:
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.0}}"
```

**Keyboard teleoperation:**
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
Use `i` (forward), `,` (backward), `j` / `l` (turn left/right), any other key to stop.

## 9. TF Tree Explanation

The transform tree describes how every link's position/orientation is calculated
relative to its parent:

```
odom
 └── base_footprint            (published by the Odometry Publisher plugin)
      └── base_link            (fixed offset, height = wheel_radius)
           ├── left_wheel       (continuous joint, rotates around Y axis)
           ├── right_wheel      (continuous joint, rotates around Y axis)
           ├── caster_wheel     (fixed joint, passive support point)
           ├── lidar_link       (fixed joint, LiDAR sensor mounted on top)
           └── camera_link      (fixed joint, camera housing mounted on front)
                └── camera_optical_link   (fixed joint, rotated to match the
                                            standard ROS optical frame convention:
                                            Z forward, X right, Y down)
```

- `odom` → `base_footprint` is published dynamically by the DiffDrive /
  OdometryPublisher plugins as the robot moves.
- `base_footprint` → `base_link` is a static offset lifting the chassis up by the
  wheel radius so it sits correctly on the ground.
- `left_wheel_joint` / `right_wheel_joint` are the only two continuously moving
  joints; their live angles come from `/joint_states`, published by the
  JointStatePublisher plugin and consumed by `robot_state_publisher` to update
  `/tf`.
- `camera_optical_link` exists separately from `camera_link` purely to apply the
  standard camera-optical-frame rotation, so image data is correctly oriented for
  ROS vision tools.

Verified using:
```bash
ros2 run tf2_tools view_frames
```
which generates `frames.pdf`, confirming a single connected tree with no orphaned
or disconnected frames (see `screenshots/tf_tree.png`).

## 10. Screenshots

| File | Description |
|---|---|
| `screenshots/rviz_view.png` | Robot fully rendered in RViz — RobotModel, TF, LaserScan (red scan boundary), and live camera feed, no errors |
| `screenshots/gazebo_view.png` | Robot spawned and sitting level inside the `turtlebot3_house.world` Gazebo environment |
| `videos/TestVideo.mp4` | Demonstration of the robot moving via `/cmd_vel`, with LiDAR and camera data visible live in RViz |


- Added the missing `gz_frame_id` tag and an explicit `<vertical>` block to the
  LiDAR sensor definition, which was required for RViz to correctly render the
  LaserScan data relative to the robot's TF tree.
- Ensured `CMakeLists.txt` installs all required directories (`urdf`, `meshes`,
  `launch`, `config`, `rviz`) and `package.xml` declares all runtime dependencies
  actually used by the launch files.
