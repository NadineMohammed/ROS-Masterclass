

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class TurtlebotMonitor(Node):

    def __init__(self):
        super().__init__('turtlebot_monitor')

        # Subscriber: listens on /cmd_vel, calls listener_callback on each message
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.listener_callback,
            10
        )

        self.get_logger().info('Monitor started. Listening on /cmd_vel...')

    def listener_callback(self, msg):
        """Called automatically every time a new Twist message arrives."""
        # extract the two fields relevant to a ground robot
        linear_x = msg.linear.x
        angular_z = msg.angular.z

        self.get_logger().info(
            f'Received -> linear.x: {linear_x:.2f}, angular.z: {angular_z:.2f}'
        )


def main(args=None):
    rclpy.init(args=args)
    monitor = TurtlebotMonitor()

    try:
        rclpy.spin(monitor)
    except KeyboardInterrupt:
        pass
    finally:
        monitor.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
