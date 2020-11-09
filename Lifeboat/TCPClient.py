from socket import socket, SHUT_RDWR
from time import sleep, time
from numpy import copy

class TCPClient():
    def __init__(self, ip=None, port=None):
        self.connected = False
        self.connecting = False
        if ip is not None and port is not None:
            self.connect(ip, port)

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
    
    def connect(self, ip, port):
        self.socket = socket()
        self.connecting = True
        self.socket.setblocking(True)
        self.socket.settimeout(3)
        try:
            self.socket.connect((ip, port))
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