# slam_toolbox_demo — Session 7: Map the World and Localize the Robot Within It

## 1. Project Overview

This package demonstrates a complete SLAM (Simultaneous Localization and Mapping)
workflow using **SLAM Toolbox** in ROS 2. It builds on the differential-drive robot
from Session 6 and runs entirely in the `turtlebot3_world` Gazebo environment.

The project has two phases:

1. **Mapping** — drive the robot through the unknown world using keyboard teleop
   while SLAM Toolbox builds a live occupancy grid map from LiDAR (`/scan`) and
   odometry (`/odom`) data. The finished map and its pose graph are saved to disk.
2. **Localization** — reload that saved map and pose graph, and have the robot
   determine its own position within the already-known map using LiDAR scan
   matching, without building any new map data.

## 2. Package Structure

```
slam_toolbox_demo/
├── config/
│   ├── slam_toolbox_online_async.yaml   # Mapping mode parameters
│   └── slam_toolbox_localization.yaml   # Localization mode parameters
├── launch/
│   ├── slam_toolbox_online_async.launch.py   # Launches SLAM Toolbox in mapping mode
│   └── localization.launch.py                # Launches SLAM Toolbox in localization mode
├── map/
│   ├── turtlebot3_world_map.yaml        # Saved occupancy grid metadata
│   └── turtlebot3_world_map.pgm         # Saved occupancy grid image
├── posegraph/
│   ├── turtlebot3_world.posegraph       # Serialized SLAM pose graph
│   └── turtlebot3_world.data            # Serialized SLAM pose graph data
├── screenshots/                         # Proof-of-work screenshots (see Section 9)
├── videos/                              # Demo videos + GIFs (see Section 9)
├── CMakeLists.txt
├── package.xml
└── README.md
```

**Note:** SLAM Toolbox itself does not launch Gazebo, spawn the robot, or open
RViz — these launch files assume the robot's own Gazebo + bridge + RViz session
(from the `my_robot_description` package, Session 6) is already running, with
`/scan` and `/odom` actively publishing.

## 3. Step-by-Step Setup Instructions

### Prerequisites
```bash
sudo apt install ros-${ROS_DISTRO}-slam-toolbox ros-${ROS_DISTRO}-nav2-map-server
```

### Build
```bash
cd ~/workspaces/slam_ws
colcon build --packages-select slam_toolbox_demo
source install/setup.bash
```

### Phase 1 — Mapping

1. In a separate terminal/workspace, launch the robot in `turtlebot3_world`
   (Gazebo + bridge + RViz), confirming `/scan` and `/odom` are publishing.
2. Launch SLAM Toolbox in mapping mode:
   ```bash
   ros2 launch slam_toolbox_demo slam_toolbox_online_async.launch.py
   ```
3. In RViz, set **Fixed Frame** to `map` and add displays: `RobotModel`, `TF`,
   `LaserScan` (topic `/scan`), and `Map` (topic `/map`).
4. Drive the robot around the entire world using keyboard teleop:
   ```bash
   ros2 run teleop_twist_keyboard teleop_twist_keyboard
   ```
5. Watch the occupancy grid build live in RViz as you explore.
6. Once mapping is complete, save the map:
   ```bash
   ros2 run nav2_map_server map_saver_cli -f ~/workspaces/slam_ws/src/slam_toolbox_demo/map/turtlebot3_world_map
   ```
7. Serialize the pose graph for later localization:
   ```bash
   ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph "{filename: '/root/workspaces/slam_ws/src/slam_toolbox_demo/posegraph/turtlebot3_world'}"
   ```
8. Stop the mapping node (`Ctrl+C`) before starting localization — the two
   modes cannot run at the same time.

### Phase 2 — Localization

1. Confirm `slam_toolbox_localization.yaml` points `map_file_name` at the
   pose graph saved above (already configured in this package).
2. Launch SLAM Toolbox in localization mode:
   ```bash
   ros2 launch slam_toolbox_demo localization.launch.py
   ```
3. In RViz, the `Map` display now shows the fixed, previously saved map
   instead of a live-growing one.
4. Click **2D Pose Estimate** and give the robot a deliberately wrong
   starting pose — observe the LaserScan misaligning with the map
   (see Section 8).
5. Click **2D Pose Estimate** again, this time at the robot's true position
   and orientation — observe the LaserScan snapping into alignment with the
   map (see Section 8).
6. Drive the robot around and confirm the LaserScan stays aligned with the
   map as it moves, verifying localization is actively tracking.

## 4. How to Test Your Nodes

```bash
# Confirm sensor data is flowing
ros2 topic hz /scan
ros2 topic hz /odom

# Confirm the map is being published
ros2 topic list | grep map
ros2 topic echo /map --once

# Confirm the TF tree is fully connected
ros2 run tf2_tools view_frames

# Confirm nodes are alive
ros2 node list
```

## 5. Expected Output

- **Mapping phase:** the occupancy grid in RViz grows to match the real
  layout of `turtlebot3_world` as the robot explores; loop closures (cyan
  lines in the pose graph visualization) appear when the robot revisits an
  already-mapped area, correcting accumulated drift.
- **Localization phase:** with a correct pose estimate, the LaserScan
  consistently overlays the saved map's walls as the robot drives, and the
  map itself never changes — only the robot's estimated position updates.

## 6. TF Tree Explanation

With SLAM Toolbox running, an additional `map` frame is added on top of the
existing TF tree from Session 6:

```
map
 └── odom
      └── base_footprint
           └── base_link
                ├── left_wheel
                ├── right_wheel
                ├── caster_wheel
                ├── lidar_link
                └── camera_link
                     └── camera_optical_link
```

- `map → odom`: published by SLAM Toolbox. This transform is what gets
  corrected whenever scan matching detects drift — it represents "how wrong
  the robot's odometry has become relative to the true map."
- `odom → base_footprint`: published by the robot's own odometry system
  (DiffDrive plugin), same as in Session 6 — this is the raw, uncorrected
  wheel-based estimate.
- Everything from `base_footprint` downward is unchanged from Session 6.

This two-layer correction (`map → odom` correcting drift, `odom → base_link`
providing continuous raw motion) is the standard ROS 2 localization pattern.

## 7. `/odom` Terminal Output

```
$ ros2 topic echo /odom
---
header:
  stamp:
    sec: <value>
    nanosec: <value>
  frame_id: odom
child_frame_id: base_footprint
pose:
  pose:
    position:
      x: <value>
      y: <value>
      z: 0.0
    orientation:
      x: 0.0
      y: 0.0
      z: <value>
      w: <value>
twist:
  twist:
    linear:
      x: <value>
      y: 0.0
      z: 0.0
    angular:
      x: 0.0
      y: 0.0
      z: <value>
---
```

*(Replace the placeholder values above with an actual snippet captured from
your own terminal session before submitting.)*

## 8. Wrong Pose vs. Correct Pose — Observations

**Wrong 2D Pose Estimate:**
After providing a deliberately incorrect 2D Pose Estimate (clicking a
location in a different area of the world than the robot's actual position),
the LaserScan data did not align with the map's walls — scan points appeared
in open floor space with no corresponding obstacle on the map, and the
robot's estimated position visually conflicted with its actual location in
Gazebo. See `screenshots/wrong_pose_estimate.png`.

**Correct 2D Pose Estimate:**
After providing an accurate 2D Pose Estimate matching the robot's true
position and orientation, the LaserScan snapped into close alignment with
the map's walls, and this alignment was maintained while driving the robot
around afterward, confirming localization was actively and correctly
tracking the robot's position. See `screenshots/correct_pose_estimate.png`.

## 9. Demo — Screenshots and Videos

| File | Description |
|---|---|
| `screenshots/build_clean.png` | Clean `colcon build`, no errors |
| `screenshots/mapping_launch_clean.png` | Mapping node activating with no errors |
| `screenshots/completed_map_rviz.png` | Finished map with RobotModel, TF, LaserScan |
| `screenshots/localization_launch_clean.png` | Localization node activating with no errors |
| `screenshots/wrong_pose_estimate.png` | LaserScan misaligned with map |
| `screenshots/correct_pose_estimate.png` | LaserScan aligned with map |
| `screenshots/tf_tree.png` | `map → odom → base_footprint → base_link` |

### Mapping Demo

![Mapping Demo](videos/mapping_demo.gif)

### Localization Demo

![Localization Demo](videos/localization_demo.gif)

*(Full-length videos are also included as `videos/mapping_demo.mp4` and
`videos/localization_demo.mp4` for reference, since GitHub does not render
`.mp4` playback inline within a README.)*

## 10. Known Environment Notes

This project was developed on a cloud-based VM without dedicated GPU
acceleration (carried over from Session 6). Sensor publish rates may run
below their configured values under load, but do not affect the correctness
of the mapping or localization results demonstrated here.
