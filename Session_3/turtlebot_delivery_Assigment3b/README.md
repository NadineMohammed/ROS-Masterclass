# turtlebot_delivery

An autonomous package delivery system for TurtleBot3, built as a ROS 2 workspace containing two packages that work together using **ROS 2 Actions**:

- **`delivery_mission_interfaces`** — defines the `DeliveryMission` action: the goal, result, and feedback structure shared between client and server.
- **`delivery_mission_controller`** — an action **server** node (`delivery_mission_node`) that executes a full 3-phase delivery mission, publishing movement commands and streaming live progress feedback throughout.

Unlike a topic (fire-and-forget) or a service (single request/response), an **action** is built for long-running tasks: the client sends a goal, receives continuous feedback while it's in progress, and gets a final result once it succeeds, is canceled, or times out. That's exactly the shape of a delivery mission — it takes time, progress matters, and it needs to be cancelable.

---

## What the Mission Actually Does

When a goal is sent, the robot executes three phases in sequence:

| Phase | What happens | Feedback `phase` value |
|---|---|---|
| **1. Drive to pickup** | Robot drives forward at the goal's `speed` for `pickup_duration` seconds | `DRIVING_TO_PICKUP` |
| **2. Pickup** | Robot stops completely and simulates a fixed 3-second pickup while still streaming feedback | `PICKING_UP` |
| **3. Drive to delivery** | Robot drives forward at `speed` for `delivery_duration` seconds | `DELIVERING` |

Throughout all three phases, feedback is published roughly 10 times per second containing:
- `phase` — which of the three phases is currently active
- `time_remaining` — seconds left in the current phase
- `progress` — a 0.0–1.0 fraction of how far through the current phase the mission is

If the **total elapsed time** since the goal was accepted ever exceeds the goal's `timeout` value, the mission is immediately aborted, the robot is stopped, and a failure result is returned — regardless of which phase it's in.

If a **cancel request** arrives at any point, the robot is stopped immediately and a canceled result is returned, without waiting for the current phase to finish.

---

## 1. Step-by-Step Setup Instructions

### Prerequisites
- Ubuntu with ROS 2 installed (Humble or later)
- A ROS 2 workspace already created (this guide assumes `~/workspaces/ws_ros2`)
- TurtleBot3 simulation packages installed (for Gazebo testing)

> **Note — ETGAH Platform users:** ROS 2 and the TurtleBot3 simulation packages come **pre-installed** on ETGAH, and Gazebo is **already running/launched** for you. Skip installing ROS 2 / TurtleBot3 packages and launching Gazebo manually — go straight to cloning and building.

### Steps

1. **Clone the repository into your workspace's `src` folder:**
   ```bash
   cd ~/workspaces/ws_ros2/src
   git clone https://github.com/YOUR-USERNAME/turtlebot_delivery.git
   ```

2. **Move into your workspace root:**
   ```bash
   cd ~/workspaces/ws_ros2
   ```

3. **Build the interfaces package first** (the action definition must compile before the controller package can import it):
   ```bash
   colcon build --packages-select delivery_mission_interfaces
   source install/setup.bash
   ```

4. **Build the controller package:**
   ```bash
   colcon build --packages-select delivery_mission_controller
   ```

5. **Source the workspace again** so both packages are available in this terminal:
   ```bash
   source install/setup.bash
   ```

---

## 2. Every ROS 2 Command Used (and What It Does)

| Command | What it does |
|---|---|
| `colcon build --packages-select delivery_mission_interfaces` | Compiles the interfaces package, generating the Python code for the `DeliveryMission` action (Goal, Result, and Feedback message types) from the `.action` file. |
| `colcon build --packages-select delivery_mission_controller` | Compiles the controller package, which depends on the interfaces package being built first. |
| `source install/setup.bash` | Loads the newly built packages into the current terminal session so `ros2 run` and `ros2 action` can find them. |
| `ros2 run delivery_mission_controller delivery_mission_node` | Starts the action server: it advertises the `/delivery_mission` action and waits for goals. |
| `ros2 action send_goal /delivery_mission delivery_mission_interfaces/action/DeliveryMission "{...}" --feedback` | Sends a goal to the action server from the terminal and prints live feedback as it streams in. |
| `ros2 action list` | Lists all currently active actions, used to confirm `/delivery_mission` is being advertised by the server. |
| `ros2 action info /delivery_mission` | Shows details about the action, including how many clients/servers are currently connected to it. |
| `ros2 topic echo /cmd_vel` | Prints raw `Twist` messages being published on `/cmd_vel`, useful for confirming movement commands without watching the robot move. |
| `ros2 node list` | Lists all currently running nodes, used to confirm `delivery_mission_node` is active. |
| `ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py` | Launches the TurtleBot3 simulation in Gazebo (not needed on ETGAH — already running). |

---

## 3. How to Test the Nodes

Three separate tests are needed to exercise every path through the mission logic: the happy path, the timeout path, and the cancel path.

### Test 1 — Full mission, completed successfully

Terminal 1 — start the server:
```bash
ros2 run delivery_mission_controller delivery_mission_node
```

Terminal 2 — send a goal with feedback printed live:
```bash
source ~/workspaces/ws_ros2/install/setup.bash
ros2 action send_goal /delivery_mission delivery_mission_interfaces/action/DeliveryMission "{speed: 0.2, pickup_duration: 5.0, delivery_duration: 5.0, timeout: 30.0}" --feedback
```

**Expected:** the robot drives forward for 5s, stops for 3s, drives forward again for 5s, then the server reports success and the robot stays stopped.

### Test 2 — Timeout abort

Send a goal where the timeout is shorter than the total mission time:
```bash
ros2 action send_goal /delivery_mission delivery_mission_interfaces/action/DeliveryMission "{speed: 0.2, pickup_duration: 10.0, delivery_duration: 10.0, timeout: 5.0}" --feedback
```

**Expected:** around the 5-second mark, the mission aborts, the robot stops immediately (even mid-drive), and the result reports `Mission aborted: timeout exceeded.`

### Test 3 — Mid-mission cancellation

Send a longer-running goal:
```bash
ros2 action send_goal /delivery_mission delivery_mission_interfaces/action/DeliveryMission "{speed: 0.2, pickup_duration: 15.0, delivery_duration: 15.0, timeout: 60.0}" --feedback
```

While it's running, press `Ctrl+C` in that terminal to cancel the goal from the client side.

**Expected:** the robot stops immediately regardless of which phase it was in, and the server logs `Mission canceled during <phase name>.`

---

## 4. Expected Output

**Server terminal**, over the course of a full successful mission:
```
[INFO] [delivery_mission_node]: Delivery Mission action server started, waiting for goals.
[INFO] [delivery_mission_node]: Goal accepted: speed=0.2, pickup_duration=5.0, delivery_duration=5.0, timeout=30.0
[INFO] [delivery_mission_node]: PHASE 1: Driving to pickup location.
[INFO] [delivery_mission_node]: PHASE 2: Stopped, simulating pickup.
[INFO] [delivery_mission_node]: PHASE 3: Driving to delivery location.
[INFO] [delivery_mission_node]: Delivery mission completed successfully in 13.0s.
```

**Client terminal**, feedback streaming during execution:
```
Feedback: delivery_mission_interfaces.action.DeliveryMission_Feedback(time_remaining=3.4, phase='DRIVING_TO_PICKUP', progress=0.32)
Feedback: delivery_mission_interfaces.action.DeliveryMission_Feedback(time_remaining=2.1, phase='PICKING_UP', progress=0.30)
Feedback: delivery_mission_interfaces.action.DeliveryMission_Feedback(time_remaining=1.8, phase='DELIVERING', progress=0.64)

Result: delivery_mission_interfaces.action.DeliveryMission_Result(success=True, message='Delivery mission completed successfully in 13.0s.')
```

**On timeout**, the result instead looks like:
```
Result: delivery_mission_interfaces.action.DeliveryMission_Result(success=False, message='Mission aborted: timeout exceeded.')
```

**On cancellation**, the result looks like:
```
Result: delivery_mission_interfaces.action.DeliveryMission_Result(success=False, message='Mission canceled during PHASE 1 (drive to pickup).')
```

**Gazebo simulation** should show the TurtleBot3:
- Driving forward during Phase 1 and Phase 3
- Coming to a complete stop during Phase 2 (pickup)
- Stopping immediately, mid-motion if necessary, on both timeout and cancellation

---

## 5. Demo

A video recording of real test runs (all three test cases: successful completion, timeout abort, and mid-mission cancel) is available here: [Demo Video](PASTE_YOUR_VIDEO_LINK_HERE)

The video shows:
- A full mission running, with all 3 phases executing and feedback streaming live in the client terminal.
- A mission aborting due to timeout, with the corresponding server log.
- A mission being canceled mid-execution, with the robot visibly stopped in Gazebo.

---

## Package Structure

```
turtlebot_delivery/
    delivery_mission_controller/
        delivery_mission_controller/
            __init__.py
            delivery_mission_node.py
        resource/
            delivery_mission_controller
        test/
        package.xml
        setup.py
        setup.cfg
    delivery_mission_interfaces/
        action/
            DeliveryMission.action
        CMakeLists.txt
        package.xml
    README.md
```

## The Action Definition

```
float32 speed
float32 pickup_duration
float32 delivery_duration
float32 timeout
---
bool success
string message
---
float32 time_remaining
string phase
float32 progress
```

Reading top to bottom, separated by `---`:
- **Goal** (what the client sends): `speed`, `pickup_duration`, `delivery_duration`, `timeout` — all floats, all set once when the mission starts.
- **Result** (returned once the mission ends, however it ends): `success` (bool) and `message` (string) explaining the outcome.
- **Feedback** (streamed repeatedly while the mission runs): `time_remaining` in the current phase, the current `phase` name, and `progress` through that phase as a 0.0–1.0 fraction.

## Design Notes

- **Pickup duration is fixed at 3 seconds** in Phase 2, separate from the goal's `pickup_duration` field (which controls how long the robot drives *to* the pickup location in Phase 1, not the pickup itself).
- **Cancel and timeout checks run on every control-loop iteration** (10 times per second) within each phase, so the robot responds almost instantly rather than only at phase boundaries.
- **A `ReentrantCallbackGroup` is used** on the action server so that cancel requests can be processed while a goal is actively executing — without it, the long-running `execute_callback` would block the executor and cancel requests would never be handled.

## Dependencies

- `rclpy` — Python client library for ROS 2, including action server/client support (`rclpy.action`)
- `geometry_msgs` — provides the `Twist` message type used to represent linear and angular velocity commands
- `delivery_mission_interfaces` — this workspace's own package, providing the `DeliveryMission` action definition
- `action_msgs` — underlying ROS 2 package that actions are built on top of (goal IDs, status, cancel handling)
