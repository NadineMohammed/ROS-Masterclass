# ============================================================
# Robot Distance Sensor Program
# Session 01 - ROS Masterclass (ETGAH)
#
# This program simulates a robot's front distance sensor.
# It reads a list of distance measurements (in meters) and
# decides what action the robot should take for each reading.
#
# Actions:
#   - STOP : distance < 0.5m  (obstacle too close)
#   - SLOW : distance 0.5m to 1.0m (obstacle nearby)
#   - MOVE : distance > 1.0m  (path is clear)
# ============================================================


class Robot:
    """A class representing a robot with a distance sensor."""

    def __init__(self, name, battery):
        """
        Initialize the robot with a name and battery level.

        Args:
            name    (str): The name of the robot.
            battery (int): Battery percentage (0-100).
        """
        self.name = name
        self.battery = battery
        print(f"Robot '{self.name}' is online. Battery: {self.battery}%\n")

    def decide_action(self, distance):
        """
        Decide what the robot should do based on a single distance reading.

        Args:
            distance (float): Distance in meters from the sensor.

        Returns:
            str: Action string — 'STOP', 'SLOW', or 'MOVE'

        Raises:
            ValueError: If distance is negative or not a number.
        """
        # Validate the input
        if not isinstance(distance, (int, float)):
            raise ValueError(f"Invalid distance value: '{distance}' is not a number.")
        if distance < 0:
            raise ValueError(f"Invalid distance value: {distance}. Distance cannot be negative.")

        # Decide action based on distance thresholds
        if distance < 0.5:
            return "STOP"
        elif distance <= 1.0:
            return "SLOW"
        else:
            return "MOVE"

    def process_sensor_readings(self, distances):
        """
        Process a list of distance readings and print the action for each.

        Args:
            distances (list): A list of distance values in meters.

        Returns:
            list: A list of action strings corresponding to each distance.
        """
        print(f"--- [{self.name}] Processing {len(distances)} sensor readings ---")

        actions = []  # Store all actions here

        for i, distance in enumerate(distances):
            try:
                action = self.decide_action(distance)
                print(f"  Reading {i+1}: {distance}m  →  {action}")
                actions.append(action)
            except ValueError as e:
                # Handle bad distance values gracefully
                print(f"  Reading {i+1}: ERROR — {e}")
                actions.append("ERROR")

        print(f"\nResult: {', '.join(actions)}\n")
        return actions


# ============================================================
# TEST CODE
# Run the robot through different sensor reading scenarios
# ============================================================

if __name__ == "__main__":

    # Create a robot instance
    my_robot = Robot(name="R2D2", battery=95)

    # --- Test Case 1: Example from the assignment ---
    print("TEST 1: Assignment example")
    my_robot.process_sensor_readings([0.3, 1.5, 0.8, 2.0, 0.4])

    # --- Test Case 2: All obstacles very close ---
    print("TEST 2: All obstacles too close (all STOP)")
    my_robot.process_sensor_readings([0.1, 0.2, 0.3, 0.4, 0.49])

    # --- Test Case 3: All paths clear ---
    print("TEST 3: All paths clear (all MOVE)")
    my_robot.process_sensor_readings([1.1, 2.0, 3.5, 5.0, 10.0])

    # --- Test Case 4: Mixed readings ---
    print("TEST 4: Mixed sensor readings")
    my_robot.process_sensor_readings([0.5, 0.75, 1.0, 0.3, 2.5])

    # --- Test Case 5: Edge/boundary values ---
    print("TEST 5: Boundary values (exactly 0.5m and 1.0m)")
    my_robot.process_sensor_readings([0.5, 1.0, 0.0, 1.001, 0.499])

    # --- Test Case 6: Error handling — bad values ---
    print("TEST 6: Bad values (error handling)")
    my_robot.process_sensor_readings([-1.0, "hello", 0.3, None, 2.0])
