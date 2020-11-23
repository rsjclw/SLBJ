from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import pyqtSignal, QThread, Qt
from time import sleep
from datetime import datetime
from TCPClient import TCPClient
from copy import copy
from Boat import Boat
import random
from utils import convertToQPixmap, CameraCapture
import numpy as np
from time import time
from multiprocessing import Process
import os
import sys

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__()
        uic.loadUi("MainWindow.ui", self)
        # self.p = Process(target=self.runServer)
        # self.p.daemon = True
        # self.p.start()
        f = open("lifeboat.cfg", "r")
        self.boatThread = QThread()
        boatID = int((f.readline()).replace("\n", ""))
        # boatID = int(random.uniform(10,99))
        globeMapPath = (f.readline()).replace("\n", "")
        serialName = (f.readline()).replace("\n", "")
        cameraName = int((f.readline()).replace("\n", ""))
        serverIP = (f.readline()).replace("\n", "")
        serverPort = int((f.readline()).replace("\n", ""))
        serverJktIP = (f.readline()).replace("\n", "")
        serverJktPort = int((f.readline()).replace("\n", ""))
        f.close()

        self.boat = Boat(boatID, globeMapPath, serialName, serverIP, serverPort, serverJktIP, serverJktPort)
        self.boat.moveToThread(self.boatThread)
        self.boatpaused = False

        self.mapSize = (1296, 648) # (416, 632)
        self.widget_Map.setMapImgSize(self.mapSize)
        self.widget_Map.setMap(self.boat.globe.mask)

        self.cap = CameraCapture(cameraName, 20)
        self.cameraOn = False
        self.label_camera.setVisible(False)

        self.initUIConnection()

        self.boatThread.start()
    
    def initUIConnection(self):
        self.pushButton_ZoomIn.clicked.connect(self.widget_Map.zoomIn)
        self.pushButton_ZoomOut.clicked.connect(self.widget_Map.zoomOut)
        self.pushButton_MoveUp.clicked.connect(self.widget_Map.moveUp)
        self.pushButton_MoveRight.clicked.connect(self.widget_Map.moveRight)
        self.pushButton_MoveDown.clicked.connect(self.widget_Map.moveDown)
        self.pushButton_MoveLeft.clicked.connect(self.widget_Map.moveLeft)
        self.pushButton_MoveCenter.clicked.connect(self.widget_Map.moveCenter)

        self.pushButton_pickLifejackets.clicked.connect(self.boat.setNewStatusPickupJacket, Qt.DirectConnection)
        self.pushButton_gotoLand.clicked.connect(self.boat.setNewStatusGotoLand, Qt.DirectConnection)
        self.pushButton_gotoShip.clicked.connect(self.boat.setNewStatusGotoShip, Qt.DirectConnection)
        self.pushButton_requestShip.clicked.connect(self.boat.setNewStatusRequestShip, Qt.DirectConnection)
        self.pushButton_gotoHere.clicked.connect(self.handleCustomPos, Qt.DirectConnection)

        self.pushButton_stop.clicked.connect(self.pauseresume)

        self.pushButton_camSwitch.clicked.connect(self.switchCamera)

        self.cap.newImg.connect(self.updateCamFrame, Qt.QueuedConnection)

        self.boatThread.started.connect(self.boat.main_)

        self.boat.updateJkt.connect(self.widget_Map.updatePos)
        self.boat.updateBoat.connect(self.widget_Map.updateLifeboat)
        self.boat.updateDest.connect(self.widget_Map.updateDest)
        self.boat.updateStatus.connect(self.lineEdit_status.setText)
        
    
    def handleCustomPos(self):
        try:
            pos = ((self.lineEdit_customInputPos.text()).replace(" ", "")).split(',')
            pos = (float(pos[0]), float(pos[1]))
        except: return
        self.boat.setNewStatusGotoCustom(pos[0], pos[1])
    
    def closeEvent(self, e):
        self.boat.stop()
        self.cap.stop()

    
    def switchCamera(self):
        if self.cameraOn:
            self.pushButton_camSwitch.setText("Turn on the camera")
            self.cap.stop()
            self.cameraOn = False
            self.label_camera.setVisible(False)
        else:
            self.pushButton_camSwitch.setText("Turn off the camera")
            self.cap.start()
            self.label_camera.setVisible(True)
            self.cameraOn = True
    
    def updateCamFrame(self, img):
        self.label_camera.setPixmap(convertToQPixmap(img))
    
    def pauseresume(self):
        if self.boatpaused:
            self.pushButton_stop.setText("STOP")
            self.boatpaused = False
            self.boat.resume()
        else:
            self.pushButton_stop.setText("START")
            self.boatpaused = True
            self.boat.pause()
    
    def resizeEvent(self, e):
        self.scrollArea.resize(self.frameGeometry().width(), self.frameGeometry().height()-30)