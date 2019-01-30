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


#   JSON format:
#   {
#       "team": <team number>,
#       "ntmode": <"client" or "server", "client" if unspecified>
#       "cameras": [
#           {
#               "name": <camera name>
#               "path": <path, e.g. "/dev/video0">
#               "pixel format": <"MJPEG", "YUYV", etc>   // optional
#               "width": <video mode width>              // optional
#               "height": <video mode height>            // optional
#               "fps": <video mode fps>                  // optional
#               "brightness": <percentage brightness>    // optional
#               "white balance": <"auto", "hold", value> // optional
#               "exposure": <"auto", "hold", value>      // optional
#               "properties": [                          // optional
#                   {
#                       "name": <property name>
#                       "value": <property value>
#                   }
#               ]
#           }
#       ]
#   }

configFile = "/boot/frc.json"

logging.basicConfig(level=logging.DEBUG)

class CameraConfig: pass

team = None
server = False
cameraConfigs = []

"""Report parse error."""
def parseError(str):
    print("config error in '" + configFile + "': " + str, file=sys.stderr)

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

    
    # start cameras
    

    vidcap = cv2.VideoCapture(0)
    Logger = logging.getLogger("debugging logger")
    offset = 10
    cs = CameraServer.putVideo(CameraServer.getInstance(),"Main",640,480)
    
    while(True):
        ret, frame = vidcap.read()
        #   frame = cv2.resize(frame, (640, 480))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        frame = cv2.erode(frame, None, iterations=2)
        frame = cv2.dilate(frame, None, iterations=4)
        frame =  cv2.threshold(frame, 170, 255, cv2.THRESH_BINARY)[1]
        
        cs.putFrame(frame)

        image, contours, hier = cv2.findContours(frame, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        boundingRects = []
        avg = 0
        for c in contours:
            if(cv2.contourArea(c)>100):
                x, y, w, h = cv2.boundingRect(c)
                avg += w
                boundingRects.append([x, y, w, h])
        if(len(contours) > 0):
            avg /= len(contours)
        for b in boundingRects:
            if(b[2]<avg):
                boundingRects.remove(b)
            else:
                print(b)
        
        table.putNumber("x",x)
        table.putNumber("y",y)
        table.putNumber("w",w)
        table.putNumber("h",h)
    print("Connected!")
        
    #vidcap.release()
    #cv2.destroyAllWindows()
        
    
    # loop forever
    while True:
        time.sleep(10)
