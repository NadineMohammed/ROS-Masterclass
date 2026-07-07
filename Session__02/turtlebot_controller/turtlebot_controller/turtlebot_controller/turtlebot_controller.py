

import sys
import termios
import tty

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class TurtlebotController(Node):

    def __init__(self):
        super().__init__('turtlebot_controller')

        # Publisher: sends Twist messages on /cmd_vel, queue depth 10
        self.velocity_publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        # Speed settings - adjust if robot moves too fast/slow
        self.linear_speed = 0.2   # meters/second
        self.angular_speed = 0.5  # radians/second

        self.get_logger().info(
            'Controller started. Use W/A/S/D to move, Q to quit.'
        )

    def get_key(self):
        """Read a single keypress from stdin without waiting for Enter."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)  # save current terminal settings
        try:
            tty.setcbreak(fd)  # switch to cbreak mode: instant single-char read
            key = sys.stdin.read(1)  # blocks until exactly one character typed
        finally:
            # always restore original terminal settings, even on error
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return key

    def run(self):
        """Main loop: read keys, build Twist messages, publish them."""
        try:
            while rclpy.ok():
                key = self.get_key()
                twist = Twist()  # all fields default to 0.0

                if key == 'w':
                    twist.linear.x = self.linear_speed
                elif key == 's':
                    twist.linear.x = -self.linear_speed
                elif key == 'a':
                    twist.angular.z = self.angular_speed
                elif key == 'd':
                    twist.angular.z = -self.angular_speed
                elif key == 'q':
                    # publish zero velocity before exiting so robot doesn't
                    # keep moving on its last received command
                    self.velocity_publisher.publish(Twist())
                    self.get_logger().info('Q pressed. Stopping and exiting.')
                    break
                else:
                    # ignore any other key, do not publish garbage commands
                    continue

                self.velocity_publisher.publish(twist)
                self.get_logger().info(
                    f'Published: linear.x={twist.linear.x:.2f}, '
                    f'angular.z={twist.angular.z:.2f}'
                )
        except KeyboardInterrupt:
            pass


def main(args=None):
    rclpy.init(args=args)
    controller = TurtlebotController()
    controller.run()
    controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
