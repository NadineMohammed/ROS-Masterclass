# TurtleBot3 Keyboard Controller

A ROS 2 Python package with two independent nodes demonstrating topic-based
publish/subscribe communication. One node reads keyboard input and publishes
velocity commands to control a TurtleBot3 robot. A second node listens to the
same topic and reports what commands are being sent. Both nodes communicate
purely through the shared topic, with no direct reference to one another.

- **`turtlebot_controller_node`** (Publisher) — reads keyboard input and sends movement commands.
- **`turtlebot_monitor_node`** (Subscriber) — listens to those commands and prints them out in real time.

Both nodes communicate through the `/cmd_vel` topic using the `Twist` message type from `geometry_msgs`.

---

## 1. Step-by-Step Setup Instructions

### Prerequisites
- Ubuntu with ROS 2 installed (Humble or later)
- A ROS 2 workspace already created (this guide assumes `~/workspaces/ws_ros2`)
- TurtleBot3 simulation packages installed (for Gazebo testing)

> **Note — ETGAH Platform users:** If you are working on the ETGAH platform, ROS 2 and the TurtleBot3 simulation packages come **pre-installed**, and Gazebo is **already running/launched** for you. Skip the "Install ROS 2," "Install TurtleBot3 simulation packages," and "Launch Gazebo" steps below — go straight to cloning the package and building it.

### Steps

1. **Clone the repository into your workspace's `src` folder:**
```bash
   cd ~/workspaces/ws_ros2/src
   git clone https://github.com/YOUR-USERNAME/turtlebot-controller-YOUR-NAME.git turtlebot_controller
```

2. **Move into your workspace root:**
```bash
   cd ~/workspaces/ws_ros2
```

3. **Build the package:**
```bash
   colcon build --packages-select turtlebot_controller
```

4. **Source the workspace so ROS 2 can find the new package:**
```bash
   source install/setup.bash
```

   > Tip: Add this line to your `~/.bashrc` so you don't have to run it in every new terminal:
   > `echo "source ~/workspaces/ws_ros2/install/setup.bash" >> ~/.bashrc`

---

## 2. Every Linux Command Used (and What It Does)

| Command | What it does |
|---|---|
| `cd <path>` | Changes the current directory to `<path>`. Used to navigate into the workspace and package folders. |
| `mkdir -p <path>` | Creates a directory (and any missing parent directories) if it doesn't already exist. |
| `git clone <url>` | Downloads (clones) a remote GitHub repository to your local machine. |
| `git init` | Initializes a new, empty Git repository in the current folder. |
| `git add .` | Stages all changed/new files in the current folder for the next commit. |
| `git commit -m "message"` | Saves the staged changes as a new commit with a descriptive message. |
| `git remote add origin <url>` | Links the local repository to a remote GitHub repository named `origin`. |
| `git push -u origin main` | Uploads local commits to the `main` branch on GitHub and sets it as the default upstream branch. |
| `source <file>` | Runs a shell script in the current terminal session so its environment changes (like ROS 2 paths) take effect immediately. |
| `chmod +x <file>` | Makes a file executable (sometimes needed for scripts). |
| `Ctrl+C` | Sends an interrupt signal to stop a currently running program in the terminal. |

---

## 3. Every ROS 2 Command Used (and What It Does)

| Command | What it does |
|---|---|
| `colcon build --packages-select turtlebot_controller` | Compiles/builds only the `turtlebot_controller` package (instead of the whole workspace), generating the `build/`, `install/`, and `log/` folders. |
| `ros2 run turtlebot_controller turtlebot_controller_node` | Runs the publisher node, which reads keyboard input and publishes `Twist` messages to `/cmd_vel`. |
| `ros2 run turtlebot_controller turtlebot_monitor_node` | Runs the subscriber node, which listens on `/cmd_vel` and prints the linear and angular velocity values it receives. |
| `ros2 topic list` | Lists all currently active topics, used to confirm `/cmd_vel` is being published/subscribed to. |
| `ros2 topic echo /cmd_vel` | Prints raw `Twist` messages being published on `/cmd_vel` directly from the command line (useful for debugging without the monitor node). |
| `ros2 node list` | Lists all currently running ROS 2 nodes, used to confirm both nodes are active. |
| `ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py` | Launches the TurtleBot3 simulation in Gazebo so the robot can be controlled and observed visually. |

---

## 4. How to Test the Nodes

1. **Start the TurtleBot3 simulation** (in its own terminal):
```bash
   export TURTLEBOT3_MODEL=burger
   ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```
   > **ETGAH Platform users:** Skip this step — Gazebo and the TurtleBot3 simulation are already launched and running for you on the platform.

2. **Open a second terminal**, source the workspace, and start the monitor (subscriber) node:
```bash
   source ~/workspaces/ws_ros2/install/setup.bash
   ros2 run turtlebot_controller turtlebot_monitor_node
```

3. **Open a third terminal**, source the workspace, and start the controller (publisher) node:
```bash
   source ~/workspaces/ws_ros2/install/setup.bash
   ros2 run turtlebot_controller turtlebot_controller_node
```

4. **Use the keyboard to control the robot** in the terminal running the controller node:
   - `W` → move forward
   - `S` → move backward
   - `A` → turn left
   - `D` → turn right
   - `Q` → stop and exit (publishes one final zero-velocity command so the robot doesn't keep drifting)

5. **Watch the results:**
   - The robot should move in Gazebo as you press keys.
   - The terminal running the monitor node should print the `linear.x` and `angular.z` values every time a command is sent.

---

## 5. Expected Output

**Controller node terminal**, once running, waits silently for key presses (no output needed to function, just listens for W/A/S/D/Q).

**Monitor node terminal** should print something like:
```
[INFO] Received cmd_vel -> linear.x: 0.20, angular.z: 0.00
[INFO] Received cmd_vel -> linear.x: 0.00, angular.z: 0.50
[INFO] Received cmd_vel -> linear.x: -0.20, angular.z: 0.00
[INFO] Received cmd_vel -> linear.x: 0.00, angular.z: -0.50
```

**Gazebo simulation** should show the TurtleBot3 physically moving forward, backward, left, and right in sync with the keys pressed, and stopping completely when `Q` is pressed.

---

## 6. Demo

Terminal screenshots from a real test run (publisher, subscriber, and Gazebo simulation working together) are included in this repository under [`demo/`](./demo).

- Screenshot of the controller node running and accepting W/A/S/D/Q key presses.
- Screenshot of the monitor node printing `linear.x` and `angular.z` values in real time as commands are sent.
- Screenshot of the TurtleBot3 moving in the Gazebo simulation on the ETGAH platform in response to those commands.

---

## Package Structure

```
turtlebot_controller/
    turtlebot_controller/
        __init__.py
        turtlebot_controller.py     # Publisher node
        turtlebot_monitor.py        # Subscriber node
    resource/
        turtlebot_controller
    test/
    package.xml
    setup.py
    setup.cfg
    README.md
```

## Dependencies

- `rclpy` — Python client library for ROS 2
- `geometry_msgs` — provides the `Twist` message type used to represent linear and angular velocity commands
