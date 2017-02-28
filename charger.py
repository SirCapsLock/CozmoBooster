import time

import cozmo
from cozmo.util import degrees, speed_mmps, distance_mm

SPIN_SPEED = 15.0

def cozmo_program(robot:cozmo.robot.Robot):
    robot.set_head_angle(degrees(0))
    robot.set_lift_height(0, in_parallel=True).wait_for_completed()
    #turn in circles until you see the charger
    robot.drive_wheels(SPIN_SPEED, -SPIN_SPEED)
    charger = robot.world.wait_for_observed_charger(timeout=30)
    robot.drive_wheels(0.0, 0.0)

    if charger:
        if robot.pose.is_comparable(charger.pose):
            #they're both on the same origin (cozmo)
            print('going to charger pose')
            robot.go_to_pose(charger.pose,in_parallel=True).wait_for_completed()
            robot.set_lift_height(.2,in_parallel=True).wait_for_completed()
            robot.turn_in_place(degrees(180)).wait_for_completed()
            wiggle_for_charger(robot)
    else:
        print('charger not found.')

def wiggle_for_charger(robot:cozmo.robot.Robot):
    robot.set_lift_height(0, accel=20).wait_for_completed()
    drive = robot.drive_straight(distance=distance_mm(-200), speed=speed_mmps(50))
    ax0 = robot.accelerometer.x
    dx = None
    while True:
        ax1 = robot.accelerometer.x
        dx = ax1 - ax0
        ax0 = ax1
        time.sleep(.1) #useless to take a dx at every iteration of the While loop
        if abs(dx) > 1000:
            #pretty sure we hit the charger
            print('Hit charger!')
            drive.abort()
            #proceed to wiggle
            robot.drive_wheels(-100.0, -100.0, l_wheel_acc=150, r_wheel_acc=150)
            while not robot.is_on_charger:
                # robot.set_lift_height(1, accel=100, duration=0, in_parallel=True)
                # robot.set_lift_height(.6, accel=100, duration=0, in_parallel=True)
                robot.move_lift(10)
                time.sleep(.05)
                robot.move_lift(-10)
                time.sleep(1)
            robot.drive_wheels(0.0, 0.0)
            time.sleep(3)
            robot.drive_off_charger_contacts().wait_for_completed()
            robot.drive_straight(distance=distance_mm(125), speed=speed_mmps(100)).wait_for_completed()
            break
    robot.play_anim_trigger(cozmo.anim.Triggers.CubePounceWinHand).wait_for_completed()

cozmo.run_program(cozmo_program, use_viewer=True, force_viewer_on_top=True)
