# my_robot_description

A ROS 2 robot description package for a two-wheeled differential-drive mobile robot, built using Xacro. The robot includes a body, two drive wheels, a caster wheel for balance, a LiDAR sensor, and a camera (with a separate optical frame).

## Project Overview

This package models a complete two-wheeled mobile robot using URDF/Xacro. It demonstrates:
- Proper link/joint hierarchy starting from `base_footprint`
- Reusable Xacro macros (used for the left/right wheels)
- Visual, collision, and inertial properties for every physical link
- Custom mesh models for the LiDAR and camera sensors
- A camera optical frame for correct image-processing coordinate conventions

## Robot Structure (Links & Joints)

```
base_footprint
  └── base_link                  (fixed joint: base_joint)
        ├── left_wheel            (continuous joint: left_wheel_joint)
        ├── right_wheel           (continuous joint: right_wheel_joint)
        ├── caster_wheel          (fixed joint: caster_joint)
        ├── lidar_link            (fixed joint: lidar_joint)
        └── camera_link           (fixed joint: camera_joint)
              └── camera_optical_link   (fixed joint: camera_optical_joint)
```

| Link | Shape | Purpose |
|---|---|---|
| `base_footprint` | none (reference frame) | Ground-level reference frame |
| `base_link` | box | Main robot body |
| `left_wheel` / `right_wheel` | cylinder | Drive wheels (continuous joints, rotate freely) |
| `caster_wheel` | sphere | Passive support wheel for balance |
| `lidar_link` | mesh (`lidar.STL`) | LiDAR sensor, mounted on top of the body |
| `camera_link` | mesh (`zed.stl`) | Camera sensor, mounted on the front face |
| `camera_optical_link` | none (reference frame) | Rotated frame matching camera image coordinate convention (X-right, Y-down, Z-forward) |

## Folder Structure

```
my_robot_description/
├── urdf/
│   └── robot_description.urdf.xacro   # Main Xacro robot description
├── meshes/
│   ├── lidar.STL                      # LiDAR visual mesh
│   └── zed.stl                        # Camera visual mesh
├── launch/
│   └── display.launch.py              # Launches robot_state_publisher + RViz2
├── CMakeLists.txt
├── package.xml
├── .gitignore
└── README.md
```

## How to Preview the Robot

### Option A — VS Code URDF Visualizer extension
1. Open `urdf/robot_description.urdf.xacro` in VS Code.
2. Temporarily set the mesh path arg to a relative path for the extension to resolve it:
   ```xml
   <xacro:arg name="mesh_path" default="../meshes/"/>
   ```
3. Open the URDF Visualizer preview panel on this file.
4. Scroll to zoom / drag to rotate and confirm the full robot displays correctly.
5. **Switch the mesh path back to `package://my_robot_description/meshes/` before building/running in ROS.**

### Option B — RViz2 (full ROS 2 environment)
```bash
cd ~/workspaces/my_robot_ws
colcon build
source install/setup.bash
ros2 launch my_robot_description display.launch.py
```
In RViz2:
1. Set **Fixed Frame** to `base_footprint`.
2. Click **Add** → **RobotModel** → set Description Topic to `/robot_description`.
3. Click **Add** → **TF** to view all coordinate frames.

## Screenshots

*(You will find the video and screenshot named Robot_urdf )*


## Notes

- Mesh files must match filename case exactly (`lidar.STL`, `zed.stl`) since Linux/ROS filesystems are case-sensitive.
- The `mesh_path` xacro argument must be set to `package://my_robot_description/meshes/` for real ROS 2 builds (RViz/Gazebo); the relative path (`../meshes/`) is only for previewing inside the VS Code extension.
