# turtlebot_operation

An obstacle-avoiding TurtleBot3 with runtime override capability, built as a ROS 2 workspace containing two packages that work together:

- **`obstacle_direction_interfaces`** — defines the `SetDirection` service used to override the robot's movement direction at runtime.
- **`obstacle_direction_controller`** — processes LiDAR data, autonomously avoids obstacles by steering toward the most open direction, and exposes the `/set_direction` service so an operator can take control at any time.

Both nodes communicate through standard ROS 2 topics and services: `/scan` (LiDAR input), `/cmd_vel` (movement output), and `/set_direction` (manual override).

---

## 1. Step-by-Step Setup Instructions

### Prerequisites
- Ubuntu with ROS 2 installed (Humble or later)
- A ROS 2 workspace already created (this guide assumes `~/workspaces/ws_ros2`)
- TurtleBot3 simulation packages installed (for Gazebo testing)

> **Note — ETGAH Platform users:** ROS 2 and the TurtleBot3 simulation packages come **pre-installed** on ETGAH, and Gazebo is **already running/launched** for you. Skip the "Install ROS 2," "Install TurtleBot3 simulation packages," and "Launch Gazebo" steps below — go straight to cloning and building the packages.

### Steps

1. **Clone the repository into your workspace's `src` folder:**
   ```bash
   cd ~/workspaces/ws_ros2/src
   git clone https://github.com/YOUR-USERNAME/turtlebot_operation_YOUR-NAME.git
   ```

2. **Move into your workspace root:**
   ```bash
   cd ~/workspaces/ws_ros2
   ```

3. **Build the interfaces package first** (it must compile before the controller package can use it):
   ```bash
   colcon build --packages-select obstacle_direction_interfaces
   ```

4. **Source the workspace, then build the controller package:**
   ```bash
   source install/setup.bash
   colcon build --packages-select obstacle_direction_controller
   ```

5. **Source the workspace again** so both packages are available:
   ```bash
   source install/setup.bash
   ```

---

## 2. Every ROS 2 Command Used (and What It Does)

| Command | What it does |
|---|---|
| `colcon build --packages-select obstacle_direction_interfaces` | Compiles the interfaces package, generating the Python/C++ code for the `SetDirection` service from the `.srv` file. |
| `colcon build --packages-select obstacle_direction_controller` | Compiles the controller package, which depends on the interfaces package being built first. |
| `source install/setup.bash` | Loads the newly built packages into the current terminal session so `ros2 run` can find them. |
| `ros2 run obstacle_direction_controller direction_autopilot_node` | Runs the main node: subscribes to `/scan`, publishes to `/cmd_vel`, and exposes the `/set_direction` service. |
| `ros2 service call /set_direction obstacle_direction_interfaces/srv/SetDirection "{direction: 'left'}"` | Manually calls the override service from the terminal, forcing the robot to move in the given direction (`forward`, `reverse`, `left`, `right`, or `auto` to release control back to autonomous mode). |
| `ros2 service list` | Lists all currently active services, used to confirm `/set_direction` is being advertised. |
| `ros2 topic echo /cmd_vel` | Prints raw `Twist` messages being published on `/cmd_vel`, useful for verifying commands without watching the robot move. |
| `ros2 node list` | Lists all currently running nodes, used to confirm `direction_autopilot_node` is active. |
| `ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py` | Launches the TurtleBot3 simulation in Gazebo (not needed on ETGAH — already running). |

---

## 3. How to Test the Nodes

### Test 1 — Autonomous obstacle avoidance
1. Run the node:
   ```bash
   ros2 run obstacle_direction_controller direction_autopilot_node
   ```
2. Drive (or let) the robot approach an obstacle in Gazebo.
3. Watch the terminal — you should see live `F:`, `L:`, `R:` distance readings every cycle.
4. When the front distance drops below the obstacle threshold (0.50m), the robot switches from `forward` to `turn` state, scans a wide arc for the farthest open direction, and rotates that way until the path ahead is clear again.

### Test 2 — Manual override service
1. With the node still running, open a second terminal and source the workspace:
   ```bash
   source ~/workspaces/ws_ros2/install/setup.bash
   ```
2. Call the service with each direction to confirm the robot responds and control is correctly handed over:
   ```bash
   ros2 service call /set_direction obstacle_direction_interfaces/srv/SetDirection "{direction: 'forward'}"
   ros2 service call /set_direction obstacle_direction_interfaces/srv/SetDirection "{direction: 'left'}"
   ros2 service call /set_direction obstacle_direction_interfaces/srv/SetDirection "{direction: 'right'}"
   ros2 service call /set_direction obstacle_direction_interfaces/srv/SetDirection "{direction: 'reverse'}"
   ```
3. Release control back to autonomous mode:
   ```bash
   ros2 service call /set_direction obstacle_direction_interfaces/srv/SetDirection "{direction: 'auto'}"
   ```
4. Confirm the robot immediately obeys each override command in Gazebo, and resumes autonomous obstacle avoidance once `auto` is called.

---

## 4. Expected Output

**Node terminal**, once running, prints continuous sensor readings and state transitions:
```
[INFO] [direction_autopilot_node]: Direction Autopilot Node started. State: forward
[INFO] [direction_autopilot_node]: F:2.35m | L:1.80m | R:2.10m
[INFO] [direction_autopilot_node]: ACTION: FORWARD
[WARN] [direction_autopilot_node]: OBSTACLE: Front 0.45m <= 0.50m, switching to TURN state
[WARN] [direction_autopilot_node]: Farthest open path at 45.0 deg (3.20m) -> ROTATE LEFT
[WARN] [direction_autopilot_node]: ROTATE LEFT until front path is free
[INFO] [direction_autopilot_node]: PATH CLEAR. Stopping rotation and moving forward.
[INFO] [direction_autopilot_node]: ACTION: FORWARD
```

**Service call terminal**, when calling `/set_direction`, returns a response like:
```
requester: making request: obstacle_direction_interfaces.srv.SetDirection_Request(direction='left')

response:
obstacle_direction_interfaces.srv.SetDirection_Response(success=True, message="Manual override accepted: moving 'left'")
```

**Gazebo simulation** should show the TurtleBot3:
- Driving forward autonomously until an obstacle appears
- Turning toward the side with the most open space, rather than a fixed direction
- Reversing and re-scanning if it gets fully boxed in
- Immediately obeying manual override commands sent via `/set_direction`, and resuming autonomous behavior when `auto` is called

---

## 5. Demo

Terminal screenshots and/or a recording of a real test run (autonomous avoidance and manual override both working, with the robot moving in Gazebo and the node's console output visible) are included in this repository under [`demo/`](./demo).

- Screenshot of the node running, showing `F:`/`L:`/`R:` distance logs and a state transition into `TURN`.
- Screenshot of the `/set_direction` service call and its response in the terminal.
- Screenshot/recording of the TurtleBot3 avoiding an obstacle and responding to an override command in Gazebo.

---

## Package Structure

```
turtlebot_operation_[YOUR-NAME]/
    obstacle_direction_controller/
        obstacle_direction_controller/
            __init__.py
            direction_autopilot_node.py
        resource/
            obstacle_direction_controller
        test/
        package.xml
        setup.py
        setup.cfg
    obstacle_direction_interfaces/
        srv/
            SetDirection.srv
        CMakeLists.txt
        package.xml
    README.md
```

## Dependencies

- `rclpy` — Python client library for ROS 2
- `sensor_msgs` — provides the `LaserScan` message type used to read LiDAR data
- `geometry_msgs` — provides the `Twist` message type used to represent linear and angular velocity commands
- `obstacle_direction_interfaces` — this workspace's own package, providing the `SetDirection` service definition
