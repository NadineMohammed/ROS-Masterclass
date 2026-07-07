# TurtleBot3 Keyboard Controller

A ROS 2 Python package with two independent nodes demonstrating topic-based
publish/subscribe communication. One node reads keyboard input and publishes
velocity commands to control a TurtleBot3 robot. A second node listens to the
same topic and reports what commands are being sent. Both nodes communicate
purely through the shared topic, with no direct reference to one another.

## Package Overview

- turtlebot_controller.py (Publisher): Reads W/A/S/D/Q keyboard input, builds
  geometry_msgs/msg/Twist messages, and publishes them to /cmd_vel.
- turtlebot_monitor.py (Subscriber): Subscribes to /cmd_vel, extracts
  linear.x and angular.z from each received message, and prints them.

## Prerequisites

- ROS 2 (Humble or later) installed and sourced
- TurtleBot3 packages installed (turtlebot3, turtlebot3_gazebo, turtlebot3_msgs)
- A configured ROS 2 workspace

## Setup Instructions

### 1. Clone this repository into your workspace's src folder

cd ~/workspaces/ws_ros2/src
git clone https://github.com/NadineMohammed/ROS-Masterclass.git

What this does: cd changes into the workspace's src directory, where colcon
expects to find all packages. git clone downloads the repository's files
from GitHub into a local folder named turtlebot_controller.

### 2. Build the package

cd ~/workspaces/ws_ros2
colcon build --packages-select turtlebot_controller

What this does: cd moves to the workspace root, one level above src, which
is required because colcon build must be run from the workspace root, not
from inside a package folder. colcon build compiles and installs the
package, generating an install/ folder containing the runnable executables
registered in setup.py. --packages-select turtlebot_controller restricts
the build to just this package instead of the entire workspace.

### 3. Source the workspace

source install/setup.bash

What this does: loads this workspace's packages into the current shell's
environment (adds them to AMENT_PREFIX_PATH and the Python path) so that
ros2 run can locate and execute them. This command must be re-run in every
new terminal window you open, since environment variables do not persist
across separate terminal sessions.

## How to Test

Open three separate terminals.

### Terminal 1: Launch the TurtleBot3 Gazebo simulation

export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py

What this does: export TURTLEBOT3_MODEL=burger sets an environment variable
telling the TurtleBot3 packages which physical robot variant to simulate
(the Burger model). ros2 launch starts Gazebo, spawns the robot model into
the simulated world, and starts the internal bridge connecting ROS 2 topics
(including /cmd_vel) to the simulation engine. Leave this terminal running
throughout testing.

### Terminal 2: Run the monitor (subscriber) node

cd ~/workspaces/ws_ros2
source install/setup.bash
ros2 run turtlebot_controller turtlebot_monitor_node

What this does: source install/setup.bash loads the workspace environment
in this new terminal, required separately per terminal session. ros2 run
package_name executable_name launches the node using the entry point
registered in setup.py. This node immediately begins listening on /cmd_vel
and prints any message it receives. Run this before the controller node so
it is already listening when messages start arriving.

### Terminal 3: Run the controller (publisher) node

cd ~/workspaces/ws_ros2
source install/setup.bash
ros2 run turtlebot_controller turtlebot_controller_node

What this does: starts the publisher node. Once running, it immediately
begins reading keyboard input:
- W moves forward
- S moves backward
- A turns left
- D turns right
- Q stops the robot and exits the node

This terminal must remain the active, focused window while pressing keys,
since keyboard input is read directly from this terminal's standard input.

## Expected Output

Terminal 3 (Controller), on pressing W:
[INFO] [turtlebot_controller]: Published: linear.x=0.20, angular.z=0.00

Terminal 2 (Monitor), at the same moment:
[INFO] [turtlebot_monitor]: Received -> linear.x: 0.20, angular.z: 0.00

On pressing Q:
[INFO] [turtlebot_controller]: Q pressed. Stopping and exiting.

A final zero-velocity command is published immediately before the node
exits, ensuring the robot does not continue executing its last received
command after the controller node has stopped.

In Gazebo (Terminal 1's simulation window): the TurtleBot3 model visibly
moves or rotates according to the key pressed, matching the linear and
angular values printed in both Terminal 2 and Terminal 3 at the same time.


## Architecture Notes

Node isolation: each node runs as a separate operating system process with
its own memory space. They never share variables or call each other's
functions directly.

Topic-based decoupling: the publisher and subscriber contain no direct
reference to one another. They are connected only by a shared topic name
(/cmd_vel) and message type (geometry_msgs/msg/Twist).

DDS discovery: ROS 2 nodes locate each other automatically through DDS's
peer discovery mechanism, without any central master process required.

QoS queue depth: both nodes use a queue depth of 10, meaning up to 10
unprocessed messages are buffered before the oldest ones are discarded if a
node falls behind. This is appropriate here since only the most recent
velocity command is meaningful for real-time robot control.
