#! /usr/bin/python 

import math
from time import sleep

import rospy
from std_msgs.msg import UInt8, Header
from geometry_msgs.msg import Vector3Stamped, Vector3

from dji_sdk.msg import Gimbal 
from dji_sdk.srv import CameraAction, CameraActionRequest, CameraActionResponse

# Gimbal Mode defs
# The ABS or REL refers to whether the gimbal's position should be set relative to its current position, 
# or absolute (relative to vehicale frame). The ALL, YAW, ROLL, and PITCH refers to which angles can be controlled.
# For example if you use ABS_ROLL, you can set Roll relative to vehicle body, and no other angles will change.
ABS_ALL   = 0x01
ABS_YAW   = 0x0D
ABS_ROLL  = 0x0B
ABS_PITCH = 0x07
REL_ALL   = 0x00
REL_YAW  = 0x0C
REL_ROLL  = 0x0A
REL_PITCH = 0x06

'''
    The GimbalControl class is used to manage gimbal operations.
'''
class GimbalControl(object):
    def __init__(self):
        
        if rospy.has_param('/gimbal_initial_position/x/'):
            self.initial_position = Vector3()
            self.initial_position.x = rospy.get_param('/gimbal_initial_position/x/',None)
            self.initial_position.y = rospy.get_param('/gimbal_initial_position/y/',None)
            self.initial_position.z = rospy.get_param('/gimbal_initial_position/z/',None)
        else:
            self.initial_position = None


        self.current_position = None

        self.mode = REL_ALL
        self.ts = 1

        # Define camera action service proxy.
        rospy.wait_for_service('dji_sdk/camera_action')
        self.cam_action = rospy.ServiceProxy('dji_sdk/camera_action', CameraAction)

        # Define publishers.
        self.angle_cmd = rospy.Publisher('/dji_sdk/gimbal_angle_cmd',Gimbal, queue_size=10)
        self.speed_cmd = rospy.Publisher('/dji_sdk/gimbal_speed_cmd', Vector3Stamped, queue_size=10)

        # Define subscriber 
        rospy.Subscriber('/dji_sdk/gimbal_angle', Vector3Stamped, self.gimbal_cb, queue_size=10)


    # Send the relevent gimbal command (in degrees) and sleeps until the command is finished.
    def command(self, roll=0, pitch=0, yaw=0, m=None, t=None):
        # Set mode and time variables.
        ts = (self.ts if t == None else t)
        mode = (self.mode if m == None else m)
            
        # Initialize gimbal structure.
        msg = Gimbal()

        # Fill message structure.
        msg.mode    = mode
        msg.ts      = ts
        msg.roll    = math.radians(roll)
        msg.pitch   = math.radians(pitch)
        msg.yaw     = math.radians(yaw)

        # Publish message and sleep until it's done.
        self.angle_cmd.publish(msg)
        sleep(ts)

    # Set the camera gimbal rotations speed in degrees/second.
    def setSpeed(self, roll=15, pitch=15, yaw=15):
        msg = Vector3Stamped()
        msg.vector.y = math.radians(roll)
        msg.vector.x = math.radians(pitch)
        msg.vector.z = math.radians(yaw)

        self.speed_cmd.publish(msg)
        sleep(1)

    # Sets the gimbal mode for control.
    def setMode(self, mode):
        self.mode = mode
    
    # Sets the time period for gimbal motions.
    def setTime(self, ts):
        self.ts = ts

    # Reset gimbal to it's original positon.
    def reset(self):
        self.command(0, 0, 0, m=ABS_ALL, t=1)
        sleep(1)

    # Take a picture with the camera.
    def takePicture(self):
        self.cam_action(0)
    
    # Start a video with the camera.
    def startVideo(self):
        self.cam_action(1)

    # End the current video with the camera.
    def endVideo(self):
        self.cam_action(2)


    # Gimbal callback function.
    def gimbal_cb(self, msg):
        self.current_position = msg.vector

        if self.initial_position == None:
            self.initial_position = msg.vector
            rospy.set_param('/gimbal_initial_position/x/', msg.vector.x)
            rospy.set_param('/gimbal_initial_position/y/', msg.vector.y)
            rospy.set_param('/gimbal_initial_position/z/', msg.vector.z)
