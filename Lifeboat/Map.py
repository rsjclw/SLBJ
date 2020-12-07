from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QBrush, QColor
from PyQt5.QtCore import pyqtSignal, QThread, QTimer
from utils import convertToQPixmap, getGreatCircleDistance, degree2rad
from cv2 import imread, IMREAD_UNCHANGED, cvtColor, COLOR_GRAY2BGR, resize
from copy import copy
import random

class Map(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.background = None
        self.outBackground = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.__update)
        self.timer.start(50)
        self.Lifejackets = {}
        self.lifeboat = (-10000, -10000)
        self.dest = (-10000, -10000)
        self.mapImgSize = (1, 1)
        self.zoomScale = 1
        self.zoomFactor = 0.1
        self.moveFactor = 0.1
        self.mapShape = (1, 1)
        self.mapRect = (0, 0, 0, 0)
        self.worldMapFLag = True
        self.oneKMLat = 0.008996
    
    def __update(self):
        self.update()
    
    def setMap(self, mask):
        self.background = mask
        print(self.background.shape)
        self.mapShape = (self.background.shape[0]-1, self.background.shape[1]-1)
        self.moveCenter()

    def setMapImgSize(self, size):
        self.mapImgSize = size
    
    def normalizePoint(self, x, y):
        return QPoint(int((x-self.mapRect[1])/(self.mapRect[3]-self.mapRect[1])*self.mapImgSize[0]),
        int((y-self.mapRect[0])/(self.mapRect[2]-self.mapRect[0])*self.mapImgSize[1]))
    
    def paintEvent(self, e):
        self.painter = QPainter(self)
        self.painter.drawPixmap(0,0,self.outBackground)
        self.painter.setPen(QColor("black"))
        self.painter.setBrush(QColor("light blue"))
        if self.worldMapFLag:
            self.painter.drawEllipse(self.normalizePoint(self.lifeboat[1], self.lifeboat[0]), 6, 6)
            self.painter.setBrush(QColor("green"))
            self.painter.drawEllipse(self.normalizePoint(self.dest[1], self.dest[0]), 5, 5)
            self.painter.setBrush(QColor("red"))
            for key in self.Lifejackets:
                self.painter.drawEllipse(self.normalizePoint(self.Lifejackets[key][1], self.Lifejackets[key][0]), 4, 4)

        else:
            xmid = int(self.mapImgSize[0]/2)
            ymid = int(self.mapImgSize[1]/2)
            self.painter.drawEllipse(QPoint(xmid, ymid), 6, 6)
            self.painter.setBrush(QColor("red"))
            # 0.008996 lat = 1km
            topLat = self.lifeboat[0] - self.oneKMLat
            botLat = self.lifeboat[0] + self.oneKMLat
            if topLat < -90: topLat = -topLat - 180
            if botLat > 90: botLat = -botLat + 180
            if abs(topLat) > abs(botLat): minAbsLat = degree2rad(botLat)
            else: minAbsLat = degree2rad(topLat)
            twoKMLon = 2/(getGreatCircleDistance(minAbsLat, 0, minAbsLat, 0.017453292519943295)/1000)
            for key in self.Lifejackets:
                dlat = self.lifeboat[0]-self.Lifejackets[key][0]
                dlon = self.Lifejackets[key][1]-self.lifeboat[1]
                y = ymid+int(dlat/self.oneKMLat*ymid)
                x = xmid+int(dlon/twoKMLon*xmid)
                self.painter.drawEllipse(QPoint(x, y), 4, 4) # edit here

        self.painter.drawEllipse(self.normalizePoint(random.uniform(0, 43200), random.uniform(0, 21600)), 2, 2)
        self.painter.end()
    
    def updatePos(self, Lifejackets):
        self.Lifejackets = copy(Lifejackets)
    
    def updateLifeboat(self, pos):
        self.lifeboat = pos
    
    def updateDest(self, pos):
        self.dest = pos
    
    def getLifejackets(self):
        return self.Lifejackets
    
    def setMapImage(self):
        self.outBackground = convertToQPixmap(cvtColor(resize(self.background[self.mapRect[0]:self.mapRect[2],
        self.mapRect[1]:self.mapRect[3]], self.mapImgSize), COLOR_GRAY2BGR)*255)
    
    def setBlankMapImage(self, img):
        self.blankMapImage = convertToQPixmap(img)

    def moveMapImg(self, moveRight, moveDown):
        if not self.worldMapFLag: return
        self.mapRect[0] += moveDown
        self.mapRect[1] += moveRight
        self.mapRect[2] += moveDown
        self.mapRect[3] += moveRight

        if self.mapRect[0] < 0:
            self.mapRect[2] -= self.mapRect[0]
            self.mapRect[0] -= self.mapRect[0]
        
        elif self.mapRect[2] > self.mapShape[0]:
            temp = self.mapShape[0]-self.mapRect[2]
            self.mapRect[2] += temp
            self.mapRect[0] += temp
        
        if self.mapRect[1] < 0:
            self.mapRect[3] -= self.mapRect[1]
            self.mapRect[1] -= self.mapRect[1]
        
        elif self.mapRect[3] > self.mapShape[1]:
            temp = self.mapShape[1]-self.mapRect[3]
            self.mapRect[3] += temp
            self.mapRect[1] += temp

        self.setMapImage()
    
    def zoom(self, factor):
        if not self.worldMapFLag: return
        newScale = self.zoomScale*factor
        if newScale >= 1: newScale = 1
        elif newScale <= 0.002: newScale = 0.002
        self.zoomScale = newScale
        r = self.mapRect[1]+int(self.mapShape[1]*self.zoomScale)
        d = self.mapRect[0]+int(self.mapShape[0]*self.zoomScale)
        moveR = int((self.mapRect[3]-r)/2)
        moveD = int((self.mapRect[2]-d)/2)
        self.mapRect[2] = d
        self.mapRect[3] = r
        self.moveMapImg(moveR, moveD)
    
    def zoomIn(self):
        self.zoom(1-self.zoomFactor)
    
    def zoomOut(self):
        self.zoom(1+self.zoomFactor)
    
    def moveLeft(self):
        self.moveMapImg(int(self.moveFactor*(self.mapRect[1]-self.mapRect[3])), 0)

    def moveRight(self):
        self.moveMapImg(int(self.moveFactor*(self.mapRect[3]-self.mapRect[1])), 0)

    def moveUp(self):
        self.moveMapImg(0, int(self.moveFactor*(self.mapRect[0]-self.mapRect[2])))

    def moveDown(self):
        self.moveMapImg(0, int(self.moveFactor*(self.mapRect[2]-self.mapRect[0])))
    
    def moveCenter(self):
        if not self.worldMapFLag: return
        self.mapRect = [0, 0, self.mapShape[0], self.mapShape[1]]
        self.zoomScale = 1.0
        self.setMapImage()
    
    def setWorldMap(self,flag):
        self.worldMapFLag = flag
        if self.worldMapFLag: self.setMapImage()
        else: self.outBackground = self.blankMapImage