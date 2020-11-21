from PyQt5.QtCore import QObject, pyqtSignal
from socket import socket, SHUT_RDWR
from time import sleep, time
from numpy import copy

class TCPClient(QObject):
    setPos = pyqtSignal(str, float, float, float, float, str)
    def __init__(self, ID, ip=None, port=None, parent=None):
        super(TCPClient, self).__init__()
        self.connected = False
        self.connecting = False
        self.on = False
        self.running = False
        self.ip = ip
        self.port = port
        self.ID = "$"+ID

    def startConnection(self):
        self.connect()
        if self.connected is False: return
        self.run()
    
    def stopConnection(self):
        self.on = False
        while self.running: sleep(0.001)
        self.disconnect()

    def run(self):
        self.on = True
        self.running = True
        msg0 = (self.ID+";0").encode('utf-8')
        t = time()
        while self.on:
            try:
                data = self.read()
                # if data != None: print(data)
                if data == "$!!": t = time()-0.8
                else:
                    data = data.split(";")
                    if len(data) == 6: self.setPos.emit(data[0], float(data[1]), float(data[2]), float(data[3]), float(data[4]), data[5])
            except: pass
            if (time()-t) >= 1:
                t = time()
                try: self.socket.send(msg0)
                except: pass
                self.setPos.emit('$!!', 0, 0, 0, 0, "0")
        self.running = False

    def read(self):
        if not self.connected: return None
        try:
            data = self.socket.recv(1024).decode('utf-8')
        except:
            return None
        return data

    def send(self, data):
        if self.connected:
            try: ret = self.socket.send(data.encode('utf-8'))
            except: return -1
            return ret
        return -1
    
    def connect(self):
        self.socket = socket()
        self.connecting = True
        self.socket.setblocking(True)
        self.socket.settimeout(3)
        try:
            self.socket.connect((self.ip, self.port))
        except:
            return False
        self.socket.send(("Hello!").encode('utf-8'))
        # self.socket.setblocking(False)
        self.socket.settimeout(0.002)
        self.connected = True
        self.connecting = False
        return True
    
    def disconnect(self):
        self.connected = False
        try:
            self.socket.shutdown(SHUT_RDWR)
            self.socket.close()
        except Exception:
            return False
        return True
    
    def isConnected(self):
        return self.connected