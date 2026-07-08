import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from obstacle_direction_interfaces.srv import SetDirection


class DirectionAutopilotNode(Node):
    """
    Autonomously avoids obstacles using LiDAR data via a forward/turn/reverse
    state machine. When an obstacle is detected, the robot scans a wide arc
    in front of it, divides it into narrow sectors, and steers toward the
    sector with the farthest average clearance. Exposes a /set_direction
    service that lets an operator override the robot's movement at any time.
    """

    def __init__(self):
        super().__init__('direction_autopilot_node')

        # Subscriber
        self.scan_subscription = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10)

        # Publisher
        self.velocity_publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        # Service server: lets an operator override the current direction
        self.override_srv = self.create_service(
            SetDirection, '/set_direction', self.set_direction_callback)

        # Parameters
        self.obstacle_threshold = 0.50
        self.free_forward_threshold = 1.00
        self.forward_velocity = 0.20
        self.angular_velocity = 0.50
        self.turning_direction = 0
        self.state = 'forward'

        # Farthest-sector scan settings
        self.scan_width = math.radians(160)   # total arc scanned in front
        self.num_sectors = 8                  # how many slices to divide it into

        # Cached latest scan data (used by the farthest-sector search)
        self.latest_ranges = None
        self.latest_angle_min = None
        self.latest_angle_increment = None

        # Operator override: None means autonomous mode is in control
        self.manual_override = None

        self.get_logger().info('Direction Autopilot Node started. State: forward')

    def set_direction_callback(self, request, response):
        """
        Service callback for /set_direction.
        Accepts: forward, reverse, left, right, auto.
        Sets a manual override that takes control of the robot until
        cleared (send direction 'auto' to release control back to the
        autonomous state machine).
        """
        valid_directions = ['forward', 'reverse', 'left', 'right', 'auto']
        direction = request.direction.lower().strip()

        if direction not in valid_directions:
            response.success = False
            response.message = (
                f"Invalid direction '{request.direction}'. "
                f"Must be one of: {valid_directions}"
            )
            self.get_logger().warn(response.message)
            return response

        if direction == 'auto':
            self.manual_override = None
            response.success = True
            response.message = "Manual override released. Returning to autonomous mode."
            self.get_logger().info(response.message)
            return response

        self.manual_override = direction
        response.success = True
        response.message = f"Manual override accepted: moving '{direction}'"
        self.get_logger().info(response.message)
        return response

    def scan_callback(self, msg: LaserScan):
        """Process LiDAR scan and compute distances using angles."""

        ranges = msg.ranges
        angle_min = msg.angle_min
        angle_increment = msg.angle_increment

        # Cache for use by the farthest-sector search
        self.latest_ranges = ranges
        self.latest_angle_min = angle_min
        self.latest_angle_increment = angle_increment

        front_distance = self._sector_distance(
            ranges, angle_min, angle_increment, 0.0, math.radians(30), 5.0
        )
        left_distance = self._sector_distance(
            ranges, angle_min, angle_increment, math.pi / 2, math.radians(30), 5.0
        )
        right_distance = self._sector_distance(
            ranges, angle_min, angle_increment, -math.pi / 2, math.radians(30), 5.0
        )

        self.get_logger().info(
            f'F:{front_distance:.2f}m | L:{left_distance:.2f}m | R:{right_distance:.2f}m'
        )

        # If an operator override is active, obey it and skip autonomous logic
        if self.manual_override is not None:
            self._apply_manual_override()
            return

        self._control_robot(front_distance, left_distance, right_distance)

    def _apply_manual_override(self):
        """Publishes a Twist command based on the active manual override."""
        cmd = Twist()
        if self.manual_override == 'forward':
            cmd.linear.x = self.forward_velocity
        elif self.manual_override == 'reverse':
            cmd.linear.x = -self.forward_velocity
        elif self.manual_override == 'left':
            cmd.angular.z = self.angular_velocity
        elif self.manual_override == 'right':
            cmd.angular.z = -self.angular_velocity

        self.get_logger().info(f'ACTION: MANUAL OVERRIDE ({self.manual_override})')
        self.velocity_publisher.publish(cmd)

    def _normalize_angle(self, angle: float) -> float:
        return math.atan2(math.sin(angle), math.cos(angle))

    def _angle_to_index(self, angle: float, angle_min: float, angle_increment: float, size: int) -> int:
        desired = self._normalize_angle(angle)
        base = self._normalize_angle(angle_min)
        delta = desired - base
        if delta < 0.0:
            delta += 2.0 * math.pi
        index = int(round(delta / angle_increment))
        return max(0, min(size - 1, index))

    def _sector_distance(
        self,
        ranges,
        angle_min: float,
        angle_increment: float,
        center_angle: float,
        width: float,
        max_distance: float,
    ) -> float:
        n = len(ranges)
        half_width = width / 2.0
        start_idx = self._angle_to_index(center_angle - half_width, angle_min, angle_increment, n)
        end_idx = self._angle_to_index(center_angle + half_width, angle_min, angle_increment, n)

        if start_idx <= end_idx:
            sector = ranges[start_idx:end_idx + 1]
        else:
            sector = ranges[start_idx:] + ranges[:end_idx + 1]

        valid = [r for r in sector if 0.1 < r < max_distance]
        return min(valid) if valid else max_distance

    def _find_farthest_sector_angle(self, max_distance=5.0):
        """
        Scans a wide arc in front of the robot, divided into self.num_sectors
        slices, and returns the center angle (radians) and distance of
        whichever sector has the farthest average clearance -- i.e. the
        most open direction to steer toward. Positive angle = left,
        negative angle = right.
        """
        if self.latest_ranges is None:
            return 0.0, 0.0

        half_width = self.scan_width / 2.0
        sector_width = self.scan_width / self.num_sectors

        best_angle = 0.0
        best_distance = -1.0

        for i in range(self.num_sectors):
            center = -half_width + sector_width * (i + 0.5)
            distance = self._sector_distance(
                self.latest_ranges, self.latest_angle_min, self.latest_angle_increment,
                center, sector_width, max_distance
            )
            if distance > best_distance:
                best_distance = distance
                best_angle = center

        return best_angle, best_distance

    def _control_robot(self, front, left, right):
        """State machine: forward -> turn -> reverse, with turn direction
        chosen by scanning for the farthest open sector."""

        cmd = Twist()
        TURN_SAFETY = 0.40

        can_turn_left = left > TURN_SAFETY
        can_turn_right = right > TURN_SAFETY

        if self.state == 'forward':
            if front <= self.obstacle_threshold:
                self.state = 'turn'
                best_angle, best_dist = self._find_farthest_sector_angle()
                self.turning_direction = 1 if best_angle >= 0 else -1
                side = 'LEFT' if self.turning_direction > 0 else 'RIGHT'
                self.get_logger().warn(
                    f'OBSTACLE: Front {front:.2f}m <= {self.obstacle_threshold:.2f}m, switching to TURN state'
                )
                self.get_logger().warn(
                    f'Farthest open path at {math.degrees(best_angle):.1f} deg '
                    f'({best_dist:.2f}m) -> ROTATE {side}'
                )
            else:
                cmd.linear.x = self.forward_velocity
                cmd.angular.z = 0.0
                self.get_logger().info('ACTION: FORWARD')

        if self.state == 'turn':
            if self.turning_direction > 0 and not can_turn_left and can_turn_right:
                self.turning_direction = -1
            elif self.turning_direction < 0 and not can_turn_right and can_turn_left:
                self.turning_direction = 1
            elif self.turning_direction > 0 and not can_turn_left:
                self.turning_direction = 0
            elif self.turning_direction < 0 and not can_turn_right:
                self.turning_direction = 0

            if self.turning_direction == 0:
                if can_turn_left or can_turn_right:
                    best_angle, best_dist = self._find_farthest_sector_angle()
                    self.turning_direction = 1 if best_angle >= 0 else -1
                else:
                    self.state = 'reverse'
                    self.get_logger().error(
                        f'TRAPPED! No safe turn direction (L:{left:.2f} R:{right:.2f}), switching to REVERSE'
                    )

            if self.state == 'turn':
                if front > self.free_forward_threshold:
                    self.state = 'forward'
                    self.turning_direction = 0
                    cmd.linear.x = self.forward_velocity
                    cmd.angular.z = 0.0
                    self.get_logger().info('PATH CLEAR. Stopping rotation and moving forward.')
                    self.get_logger().info('ACTION: FORWARD')
                else:
                    cmd.linear.x = 0.0
                    cmd.angular.z = self.angular_velocity * self.turning_direction
                    side = 'LEFT' if self.turning_direction > 0 else 'RIGHT'
                    self.get_logger().warn(f'ROTATE {side} until front path is free')

        if self.state == 'reverse':
            cmd.linear.x = -0.10
            cmd.angular.z = self.angular_velocity if left >= right else -self.angular_velocity
            self.get_logger().error(
                f'REVERSE and rotate to safer side (L:{left:.2f} R:{right:.2f})'
            )
            if front > self.free_forward_threshold and (can_turn_left or can_turn_right):
                self.state = 'forward'
                self.turning_direction = 0
                self.get_logger().info('RECOVERED. Switching back to FORWARD state.')

        self.velocity_publisher.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = DirectionAutopilotNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
