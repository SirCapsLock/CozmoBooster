import cozmo
import sys

import time
from cozmo.lights import Light, Color

from cozmo.util import degrees, Pose


class BuildPyramid:
    def __init__(self, robot):
        self.CUBE_SIZE = 38  # a cube is 38mm (1.5inches) square
        self.ROBOT_SIZE = self.CUBE_SIZE * 1.6

        self.init_pose = robot.pose
        self.robot = robot
        self.curStep = 1

        self.stack_cube = None
        self.right_cube = None
        self.corner_cube = None

    def run(self):
        self.robot.set_head_light(False)
        self.robot.set_head_angle(degrees(0)).wait_for_completed()
        self.robot.set_lift_height(0, in_parallel=True).wait_for_completed()
        self.robot.drive_wheels(15.0, -15.0)
        cubes = self.robot.world.wait_until_observe_num_objects(3, cozmo.objects.LightCube)

        # found cubes, stop turning
        self.robot.drive_wheels(0.0, 0.0)
        time.sleep(1)  # let cozmo observe the cubes for a second

        if len(cubes) == 3:
            # sort the cubes from furthest left to furthest right
            def sort_by_y_posn(cube):
                return cube.pose.position.y

            cubes.sort(key=sort_by_y_posn, reverse=True)
            '''
                      [stack_cube]
                [corner_cube][right_cube]

            '''
            self.corner_cube = cubes[0]
            self.right_cube = cubes[1]
            self.stack_cube = cubes[2]

            while True:
                if self.curStep == 1:
                    self.step1_pickup()
                elif self.curStep == 2:
                    self.step2_place_right_cube_next_to_pickup()
                elif self.curStep == 3:
                    self.step3_pickup_stack_cube()
                elif self.curStep == 4:
                    self.step4_drop_stack_on_top()
                else:
                    print("I did it!!")
                    self.reset_pose()
                    self.robot.play_anim_trigger(cozmo.anim.Triggers.CubePounceWinSession).wait_for_completed()
                    break

    def reset_pose(self):
        self.robot.go_to_pose(self.init_pose, num_retries=3).wait_for_completed()

    def increment_step(self):
        self.curStep += 1

    def step1_pickup(self):
        """
        Step 1: pick up the right cube

        :return: None
        """

        print('**step 1**')
        pickup = self.robot.pickup_object(self.right_cube, num_retries=3)
        pickup.wait_for_completed()
        if pickup.has_succeeded:
            # bring Cozmo back to his initial position so he gets a better view of the cubes
            self.reset_pose()
            self.increment_step()

    def step2_place_right_cube_next_to_pickup(self):
        """
        Step 2: place the right cube next to the corner cube
        :return: None
        """
        print('**step 2**')


        pickup_posn = self.corner_cube.pose.position
        next_to_pickup_pose = Pose(pickup_posn.x - self.ROBOT_SIZE, pickup_posn.y - self.CUBE_SIZE - 14, pickup_posn.z,
                                   angle_z=degrees(0.0))
        go_to_next_to_pickup = self.robot.go_to_pose(next_to_pickup_pose)
        go_to_next_to_pickup.wait_for_completed()
        if go_to_next_to_pickup.has_succeeded:
            drop_action = self.robot.place_object_on_ground_here(self.right_cube, num_retries=3)
            drop_action.wait_for_completed()
            if drop_action.has_succeeded:
                purple_light = Color(int_color=0xff00ffff)
                self.corner_cube.set_lights(Light(on_color=purple_light, off_color=purple_light))
                self.right_cube.set_lights(Light(on_color=purple_light, off_color=purple_light))
                self.reset_pose()
                self.increment_step()

    def step3_pickup_stack_cube(self):
        """
        Step 3: Pick up the stack cube that will go at the top of the pyramid
        :return:
        """
        print('**step 3**')
        pickup_stack_cube = self.robot.pickup_object(self.stack_cube, num_retries=3)
        pickup_stack_cube.wait_for_completed()
        if pickup_stack_cube.has_succeeded:
            self.reset_pose()
            self.increment_step()

    def step4_drop_stack_on_top(self):
        """
        Place the stack cube in the middle of the corner cube and right cube
        :return:
        """
        print('**step 4**')
        pickup_posn = self.corner_cube.pose.position
        right_posn = self.right_cube.pose.position

        # find an x coordinate that places cozmo at a position far enough away from the cubes such that when he
        # places the stack cube, it will land on top
        robot_x = pickup_posn.x - self.CUBE_SIZE * 1.6

        # find y coordinate for position in the middle of blocks
        middle_y = pickup_posn.y + (right_posn.y - pickup_posn.y) / 2
        # (assume an angle of 0 degrees as I'm not yet accounting for cubes that are rotated
        destination_pose = Pose(robot_x,
                                middle_y,
                                pickup_posn.z,
                                angle_z=degrees(0))
        go_to_destination_pose = self.robot.go_to_pose(destination_pose, num_retries=3)
        go_to_destination_pose.wait_for_completed()
        drop_stack = self.robot.place_object_on_ground_here(self.stack_cube, num_retries=3)
        drop_stack.wait_for_completed()

        self.stack_cube.set_lights(Light(on_color=Color(int_color=0xff00ffff), off_color=Color(int_color=0xff00ffff)))
        # I can't check for has_succeeded here because Cozmo won't think he's actually succeeded in dropping the cube
        # so let's just assume he was successful
        self.increment_step()


def run(sdk_conn):
    robot = sdk_conn.wait_for_robot()
    try:
        build_pyramid = BuildPyramid(robot)
        build_pyramid.run()
    except KeyboardInterrupt:
        print("Exit requested")


if __name__ == '__main__':
    cozmo.setup_basic_logging()
    cozmo.robot.Robot.drive_off_charger_on_connect = True
    try:
        cozmo.connect_with_tkviewer(run, force_on_top=True)
    except cozmo.ConnectionError as e:
        sys.exit("Connection error: " + str(e))
