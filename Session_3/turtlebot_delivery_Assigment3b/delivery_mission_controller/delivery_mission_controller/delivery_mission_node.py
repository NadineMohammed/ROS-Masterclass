import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from geometry_msgs.msg import Twist

from delivery_mission_interfaces.action import DeliveryMission


class DeliveryMissionNode(Node):
    """
    Action server that runs a 3-phase autonomous package delivery mission:
      Phase 1 - Drive forward for pickup_duration (heading to pickup location)
      Phase 2 - Stop and simulate pickup while streaming progress feedback
      Phase 3 - Drive forward for delivery_duration (heading to delivery location)

    Supports cancellation at any point (stops the robot immediately) and
    aborts the mission if the total elapsed time exceeds the goal's timeout.
    """

    def __init__(self):
        super().__init__('delivery_mission_node')

        self.cmd_vel_publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        self._action_server = ActionServer(
            self,
            DeliveryMission,
            'delivery_mission',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=ReentrantCallbackGroup(),
        )

        self.get_logger().info('Delivery Mission action server started, waiting for goals.')

    def goal_callback(self, goal_request):
        """Accepts or rejects an incoming goal request."""
        if goal_request.speed <= 0.0:
            self.get_logger().warn('Rejected goal: speed must be greater than 0.')
            return GoalResponse.REJECT
        if goal_request.timeout <= 0.0:
            self.get_logger().warn('Rejected goal: timeout must be greater than 0.')
            return GoalResponse.REJECT

        self.get_logger().info(
            f'Goal accepted: speed={goal_request.speed}, '
            f'pickup_duration={goal_request.pickup_duration}, '
            f'delivery_duration={goal_request.delivery_duration}, '
            f'timeout={goal_request.timeout}'
        )
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        """Accepts any cancel request."""
        self.get_logger().warn('Cancel request received.')
        return CancelResponse.ACCEPT

    def _stop_robot(self):
        self.cmd_vel_publisher.publish(Twist())

    def _drive_forward(self, speed):
        cmd = Twist()
        cmd.linear.x = speed
        self.cmd_vel_publisher.publish(cmd)

    def execute_callback(self, goal_handle):
        goal = goal_handle.request
        result = DeliveryMission.Result()
        feedback = DeliveryMission.Feedback()

        mission_start = time.time()
        loop_rate = 0.1  # seconds, i.e. 10 Hz feedback/control loop

        def elapsed():
            return time.time() - mission_start

        def timed_out():
            if elapsed() > goal.timeout:
                self.get_logger().error(
                    f'Mission ABORTED: elapsed {elapsed():.1f}s exceeded timeout {goal.timeout:.1f}s'
                )
                return True
            return False

        # ---------- PHASE 1: Drive forward for pickup_duration ----------
        self.get_logger().info('PHASE 1: Driving to pickup location.')
        phase_start = time.time()
        while (time.time() - phase_start) < goal.pickup_duration:
            if goal_handle.is_cancel_requested:
                return self._handle_cancel(goal_handle, result, 'PHASE 1 (drive to pickup)')

            if timed_out():
                return self._handle_timeout(goal_handle, result)

            self._drive_forward(goal.speed)

            feedback.phase = 'DRIVING_TO_PICKUP'
            feedback.time_remaining = goal.pickup_duration - (time.time() - phase_start)
            feedback.progress = (time.time() - phase_start) / goal.pickup_duration
            goal_handle.publish_feedback(feedback)

            time.sleep(loop_rate)

        # ---------- PHASE 2: Stop and simulate pickup ----------
        self.get_logger().info('PHASE 2: Stopped, simulating pickup.')
        self._stop_robot()
        phase_start = time.time()
        while (time.time() - phase_start) < 3.0:  # fixed 3s pickup simulation
            if goal_handle.is_cancel_requested:
                return self._handle_cancel(goal_handle, result, 'PHASE 2 (pickup)')

            if timed_out():
                return self._handle_timeout(goal_handle, result)

            feedback.phase = 'PICKING_UP'
            feedback.time_remaining = 3.0 - (time.time() - phase_start)
            feedback.progress = (time.time() - phase_start) / 3.0
            goal_handle.publish_feedback(feedback)

            time.sleep(loop_rate)

        # ---------- PHASE 3: Drive forward for delivery_duration ----------
        self.get_logger().info('PHASE 3: Driving to delivery location.')
        phase_start = time.time()
        while (time.time() - phase_start) < goal.delivery_duration:
            if goal_handle.is_cancel_requested:
                return self._handle_cancel(goal_handle, result, 'PHASE 3 (drive to delivery)')

            if timed_out():
                return self._handle_timeout(goal_handle, result)

            self._drive_forward(goal.speed)

            feedback.phase = 'DELIVERING'
            feedback.time_remaining = goal.delivery_duration - (time.time() - phase_start)
            feedback.progress = (time.time() - phase_start) / goal.delivery_duration
            goal_handle.publish_feedback(feedback)

            time.sleep(loop_rate)

        # ---------- Mission complete ----------
        self._stop_robot()
        goal_handle.succeed()
        result.success = True
        result.message = f'Delivery mission completed successfully in {elapsed():.1f}s.'
        self.get_logger().info(result.message)
        return result

    def _handle_cancel(self, goal_handle, result, phase_name):
        """Stops the robot immediately and returns a canceled result."""
        self._stop_robot()
        goal_handle.canceled()
        result.success = False
        result.message = f'Mission canceled during {phase_name}.'
        self.get_logger().warn(result.message)
        return result

    def _handle_timeout(self, goal_handle, result):
        """Stops the robot immediately and aborts the mission."""
        self._stop_robot()
        goal_handle.abort()
        result.success = False
        result.message = 'Mission aborted: timeout exceeded.'
        self.get_logger().error(result.message)
        return result


def main(args=None):
    rclpy.init(args=args)
    node = DeliveryMissionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
