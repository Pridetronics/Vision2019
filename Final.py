#!/usr/bin/env python3
#----------------------------------------------------------------------------
# Copyright (c) 2018 FIRST. All Rights Reserved.
# Open Source Software - may be modified and shared by FRC teams. The code
# must be accompanied by the FIRST BSD license file in the root directory of
# the project.
#----------------------------------------------------------------------------

import json
import time
import sys
import cv2
import logging
import threading
import numpy as np
import socket
from cscore import CameraServer, VideoSource
from networktables import NetworkTables

def inches(inch):
    return inch/12

def translate(value, leftMin, leftMax, rightMin, rightMax):
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin
    valueScaled = float(value - leftMin) / float(leftSpan)
    return rightMin + (valueScaled * rightSpan)

tapeHeight = .5
focalLength = 500
d1 = 1
d2 = inches(8)
d3 = pow(d1*d1+(d2*d2)/4,1/2)
d4 = 0
theta1 = 0
theta2 = 0
theta3 = np.arctan(2*d1/d2)
theta4 = 0
theta7 = np.arctan(d2/(2*d1))
configFile = "/boot/frc.json"

logging.basicConfig(level=logging.DEBUG)

class CameraConfig: pass

team = None
server = False
cameraConfigs = []

"""Report parse error."""
def parseError(str):
    print("config error in '" + configFile + "': " + str, file=sys.stderr)

def takeArea(elem):
    return elem[4]
def takeX(elem):
    return elem[0]

"""Read single camera configuration."""
def readCameraConfig(config):
    cam = CameraConfig()

    # name
    try:
        cam.name = config["name"]
    except KeyError:
        parseError("could not read camera name")
        return False

    # path
    try:
        cam.path = config["path"]
    except KeyError:
        parseError("camera '{}': could not read path".format(cam.name))
        return False

    cam.config = config

    cameraConfigs.append(cam)
    return True

"""Read configuration file."""
def readConfig():
    global team
    global server

    # parse file
    try:
        with open(configFile, "rt") as f:
            j = json.load(f)
    except OSError as err:
        print("could not open '{}': {}".format(configFile, err), file=sys.stderr)
        return False

    # top level must be an object
    if not isinstance(j, dict):
        parseError("must be JSON object")
        return False

    # team number
    try:
        team = j["team"]
    except KeyError:
        parseError("could not read team number")
        return False

    # ntmode (optional)
    if "ntmode" in j:
        str = j["ntmode"]
        if str.lower() == "client":
            server = False
        elif str.lower() == "server":
            server = True
        else:
            parseError("could not understand ntmode value '{}'".format(str))

    # cameras
    try:
        cameras = j["cameras"]
    except KeyError:
        parseError("could not read cameras")
        return False
    for camera in cameras:
        if not readCameraConfig(camera):
            return False

    return True

"""Start running the camera."""
def startCamera(config):
    print("Starting camera '{}' on {}".format(config.name, config.path))
    camera = CameraServer.getInstance() \
        .startAutomaticCapture(name=config.name, path=config.path)

    camera.setConfigJson(json.dumps(config.config))

    return camera

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        configFile = sys.argv[1]

    # read configuration
    if not readConfig():
        sys.exit(1)
    '''
    # start NetworkTables 
    cond = threading.Condition()
    notified = [False]

    def connectionListener(connected, info):
        print(info, '; Connected=%s' % connected)
        with cond:
            notified[0] = True
            cond.notify()

    NetworkTables.initialize(server='10.38.53.2')
    NetworkTables.addConnectionListener(connectionListener, immediateNotify=True)
    table = NetworkTables.getTable('Shuffleboard')

    with cond:
        print("Waiting")
        if not notified[0]:
            cond.wait()

    '''
    # start cameras
    

    vidcap = cv2.VideoCapture(0)
    Logger = logging.getLogger("debugging logger")
    offset = 10
    cs = CameraServer.putVideo(CameraServer.getInstance(),"Main",1080,720)
    
    while(True):
        ret, frame = vidcap.read()
        #   frame = cv2.resize(frame, (640, 480))
        
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        frame = cv2.erode(frame, None, iterations=2)
        frame = cv2.dilate(frame, None, iterations=4)
        frame =  cv2.threshold(frame, 170, 255, cv2.THRESH_BINARY)[1]
        

        frame, contours, hier = cv2.findContours(frame, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        boundingRects = []
        
        for c in contours:
            ca = cv2.contourArea(c)
            x, y, w, h = cv2.boundingRect(c)
            boundingRects.append([x, y, w, h, ca])
        if(len(boundingRects)>1):
            boundingRects.sort(key=takeArea)
            boundingRects=boundingRects[len(boundingRects)-2:] 
            for b in boundingRects:
                x, y, w, h, ca = b
                frame = cv2.rectangle(frame,(x,y),(x+w,y+h),(255,255,255),5)
            boundingRects.sort(key=takeX)
            tapeLeft = boundingRects[0]
            tapeRight = boundingRects[1]
            direction = 0
            if tapeLeft[3] > tapeRight[3]:
                direction = 1
                d4 = tapeHeight*focalLength/tapeLeft[3]
                d6 = tapeHeight*focalLength/tapeRight[3]
                theta4 = translate(tapeLeft[0],0,1080,-30,30)
            else:
                d6 = tapeHeight*focalLength/tapeLeft[3]
                d4 = tapeHeight*focalLength/tapeRight[3]
                theta4 = translate(tapeRight[0],0,1080,-30,30)
            
            theta1 = np.arccos((d4*d4+d2*d2-d6*d6)/(2*d4*d2)) - theta3
            d5 = pow(d3*d3+d4*d4-(2*d3*d4*np.cos(theta1)),1/2)
            theta2 = np.arcsin(d3*np.sin(theta1)/d5)
            theta5 = theta2-theta4
            theta6 = 180-theta7-(180-theta1-theta2)
            Logger.debug("Rotate: "+str(theta5)+" Forward: "+str(d5)+"Rotate Back: "+str(d6))
        cs.putFrame(frame)
        '''   
        table.putNumber("angle",a)
        table.putNumber("distance",d)
        print("connected")
        '''
    #vidcap.release()
    #cv2.destroyAllWindows()
        
    
    # loop forever
    while True:
        time.sleep(10)
