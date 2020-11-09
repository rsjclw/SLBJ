import numpy as np
from utils import Globe, Control
from datetime import datetime
from serial import Serial
from threading import Thread
from TCPClient import TCPClient
from time import sleep
import random

class Boat:
    def __init__(self, serialName=None, serverIP=None, serverPort=None):
        self.serialConnected = False
        self.tcpConn = TCPClient()
        if serialName != None:
            self.serialConn = Serial("/dev/ttyUSB0", 19200, timeout=0)
            self.serialConnected = True
        if serverIP != None and serverPort != None: self.tcpConn.connect(serverIP, serverPort)
        self.on = False
        t = Thread(target=self.__run)
        t.daemon = True
        t.start()
        self.status = None
        self.lat = None
        self.lon = None
        self.heading = None
        self.serialData = ""
        self.serialDataStartFlag = False
    
    def __run(self):
        self.on = True
        while self.on:
            if self.tcpConn.isConnected(): self.__tcpHandler()
            if self.serialConnected: self.__serialHandler()
            sleep(0.001)
        
    
    def __tcpHandler(self):
        tcpData = self.tcpConn.read()
        if tcpData is None: return
        if len(tcpData) > 1: print(tcpData)
    
    def __serialHandler(self):
        n = self.serialConn.in_waiting()
        serialData = self.serialConn.read(n)
        startIdx = 0
        idxA = -1
        if self.serialDataStartFlag == False:
            idxA = serialData.find('$')
            if idxA != -1:
                startIdx = idxA+1
                self.serialData = ""
                self.serialDataStartFlag = True
        if self.serialDataStartFlag == True:
            idxB = serialData.find('#', startIdx)
            if idxB != -1:
                self.serialData += serialData[startIdx: idxB]
                self.serialDataStartFlag = False
                serialData = (serialData[startIdx:idxB]).split(';')
                if len(serialData) == 3:
                    self.lat = float(serialData[0])
                    self.lon = float(serialData[1])
                    self.heading = float(serialData[2])
            elif idxA == -1:
                self.serialData += serialData

    def serialSend(self, message):
        if self.serialConnected: self.serialConn.write(message.encode)
        return -1
    
    def isReady(self):
        if self.lat is None or self.lon is None or self.heading is None: return False
        return True


if __name__ == "__main__":
    # world path = worldmap.npz
    # danau 8 path = danau8map.npz
    globe = Globe("danau8map.npz")
    boat = Boat(None, "192.168.1.8", 6969)
    # boat = Boat()
    control = Control([1,0,1,4], [1,0,1,4], 1.5)
    boatID = int(random.uniform(10,99))
    while True:
        # x = input("Start?\n")
        boat.lat = -7.287106 # random.uniform(-90.0, 90.0) # random.uniform(-7.287302, -7.286075)
        boat.lon = 112.796112 # random.uniform(-180.0, 180.0) # random.uniform(112.795609, 112.796427)
        boat.heading = random.uniform(-180.0, 180.0)
        while not boat.isReady(): sleep(0.01)
        destLat, destLon = globe.search_land(boat.lat, boat.lon, 1000)
        control.setControlPoint(boat.lat, boat.lon, destLat, destLon)
        while not control.isArrived():
            boat.lat = random.uniform(-7.287302, -7.286075) # random.uniform(-90.0, 90.0) # -7.287106
            boat.lon = random.uniform(112.795609, 112.796427) # random.uniform(-180.0, 180.0) # 112.796112
            message = "$BOAT{};{};{};0999".format(boatID, boat.lat, boat.lon)
            print(message)
            boat.tcpConn.send(message)
            controlOutput = control.control(boat.lat, boat.lon, boat.heading)
            message = "${}@".format(controlOutput)
            boat.serialSend(message)
            sleep(0.5)

    # message = "$BOAT01;-16.454522;75.908196;4999"
    # s = datetime.now()
    # r = globe.search_land(-39.811377, 20.061342, 1000000)
    # e = datetime.now()
    # print(r)
    # d = e-s
    # print(d.total_seconds())