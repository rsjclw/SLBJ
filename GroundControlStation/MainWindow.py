from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import pyqtSignal, QThread
from time import sleep
from utils import convertToQPixmap
from datetime import datetime
from TCPClient import TCPClient

class MainWindow(QMainWindow):
    startTCP = pyqtSignal()
    stopTCP = pyqtSignal()
    def __init__(self, parent=None):
        super(MainWindow, self).__init__()
        uic.loadUi("MainWindow.ui", self)
        self.tcpThread = QThread()
        self.tcp = TCPClient("GCSt00", "192.168.1.8", 6969)
        self.tcp.moveToThread(self.tcpThread)
        self.tcpThread.start()

        self.initUIConnection()
    
    def switchTCP(self):
        if self.tcp.isConnected():
            self.pushButton_switchConnection.setText("Connect")
            self.tcp.stopConnection()
        else:
            self.pushButton_switchConnection.setText("Disconnect")
            self.startTCP.emit()
    
    def __updatePos(self, boatID, lat, lon, saverLat, saverLon):
        self.widget_Map.updatePos(boatID, lat, lon, saverLat, saverLon)

    def initUIConnection(self):
        self.pushButton_switchConnection.clicked.connect(self.switchTCP)

        self.startTCP.connect(self.tcp.startConnection)

        self.tcp.setPos.connect(self.__updatePos)
    #     self.pushButton_CaptureAllCamera.clicked.connect(self.saveImageBot)
    #     self.pushButton_CaptureAllCamera.clicked.connect(self.saveImageFront)

    #     self.pushButton_RecordAllCamera.clicked.connect(self.v.recordCamSwitch)
    #     self.v.recordCamStartSignal.connect(self.pushButton_RecordAllCamera.setText)
    #     self.v.recordCamStartSignal.connect(self.control.startRecordCam)
    #     self.v.recordCamStopSignal.connect(self.pushButton_RecordAllCamera.setText)
    #     self.v.recordCamStopSignal.connect(self.control.stopRecordCam)
        
    #     self.pushButton_SwitchBotCamera.clicked.connect(self.v.botCamSwitch)
    #     self.v.botCam.imgSignal.connect(self.drawBotImg)
    #     self.v.botCamStartSignal.connect(self.pushButton_SwitchBotCamera.setText)
    #     self.v.botCamStartSignal.connect(self.control.startBotCam)
    #     self.v.botCamStopSignal.connect(self.pushButton_SwitchBotCamera.setText)
    #     self.v.botCamStopSignal.connect(self.control.stopBotCam)
        
    #     self.pushButton_SwitchFrontCamera.clicked.connect(self.v.frontCamSwitch)
    #     self.v.frontCam.imgSignal.connect(self.drawFrontImg)
    #     self.v.frontCamStartSignal.connect(self.pushButton_SwitchFrontCamera.setText)
    #     self.v.frontCamStartSignal.connect(self.control.startFrontCam)
    #     self.v.frontCamStopSignal.connect(self.pushButton_SwitchFrontCamera.setText)
    #     self.v.frontCamStopSignal.connect(self.control.stopFrontCam)

    #     self.pushButton_SwitchDrone.clicked.connect(self.control.tcp.switchConnection)
    #     self.control.tcp.tcpConnectSignal.connect(self.pushButton_SwitchDrone.setText)
    #     self.control.tcp.tcpDisconnectSignal.connect(self.pushButton_SwitchDrone.setText)
    #     self.control.tcp.tcpDisconnectSignal.connect(self.disconnectUIFromTCP)
        
    #     self.pushButton_saveControlParam.clicked.connect(self.control.saveControlParam)
    #     self.control.tcp.setUIParameter.connect(self.initUIParameter)
    #     self.control.setLatUI.connect(self.lineEdit_CurrentLatitude.setText)
    #     self.control.setLonUI.connect(self.lineEdit_CurrentLongitude.setText)

    #     self.pushButton_showControl.clicked.connect(self.control.showControl)
    
    # def disconnectUIFromTCP(self):
    #     self.doubleSpinBox_Alt_P.valueChanged.disconnect(self.control.setAltP)
    #     self.doubleSpinBox_Alt_I.valueChanged.disconnect(self.control.setAltI)
    #     self.doubleSpinBox_Alt_D.valueChanged.disconnect(self.control.setAltD)
    #     self.doubleSpinBox_Pos_P.valueChanged.disconnect(self.control.setPosP)
    #     self.doubleSpinBox_Pos_I.valueChanged.disconnect(self.control.setPosI)
    #     self.doubleSpinBox_Pos_D.valueChanged.disconnect(self.control.setPosD)
    #     self.doubleSpinBox_Yaw_P.valueChanged.disconnect(self.control.setYawP)
    #     self.doubleSpinBox_Yaw_I.valueChanged.disconnect(self.control.setYawI)
    #     self.doubleSpinBox_Yaw_D.valueChanged.disconnect(self.control.setYawD)
    #     self.doubleSpinBox_LocalAltitude.valueChanged.disconnect(self.control.setLocalAlt)
    
    # def drawBotImg(self, img):
    #     self.label_BotCam.setPixmap(convertToQPixmap(img))

    # def drawFrontImg(self, img):
    #     self.label_FrontCam.setPixmap(convertToQPixmap(img))
    
    # def initUIParameter(self, data):
    #     data = data[1:-1].split(',')
    #     self.doubleSpinBox_Alt_P.setValue(float(data[0])); self.doubleSpinBox_Alt_I.setValue(float(data[1])); self.doubleSpinBox_Alt_D.setValue(float(data[2]))
    #     self.doubleSpinBox_Pos_P.setValue(float(data[3])); self.doubleSpinBox_Pos_I.setValue(float(data[4])); self.doubleSpinBox_Pos_D.setValue(float(data[5]))
    #     self.doubleSpinBox_Yaw_P.setValue(float(data[6])); self.doubleSpinBox_Yaw_I.setValue(float(data[7])); self.doubleSpinBox_Yaw_D.setValue(float(data[8]))
    #     self.doubleSpinBox_LocalAltitude.setValue(float(data[9]))

    #     self.doubleSpinBox_Alt_P.valueChanged.connect(self.control.setAltP)
    #     self.doubleSpinBox_Alt_I.valueChanged.connect(self.control.setAltI)
    #     self.doubleSpinBox_Alt_D.valueChanged.connect(self.control.setAltD)
    #     self.doubleSpinBox_Pos_P.valueChanged.connect(self.control.setPosP)
    #     self.doubleSpinBox_Pos_I.valueChanged.connect(self.control.setPosI)
    #     self.doubleSpinBox_Pos_D.valueChanged.connect(self.control.setPosD)
    #     self.doubleSpinBox_Yaw_P.valueChanged.connect(self.control.setYawP)
    #     self.doubleSpinBox_Yaw_I.valueChanged.connect(self.control.setYawI)
    #     self.doubleSpinBox_Yaw_D.valueChanged.connect(self.control.setYawD)
    #     self.doubleSpinBox_LocalAltitude.valueChanged.connect(self.control.setLocalAlt)