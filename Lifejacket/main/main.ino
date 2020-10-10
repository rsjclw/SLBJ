#include "WiFi.h"

int LED_BUILTIN = 2;
const char *ssid = "Anonymous";
const char *password =  "whatthefuck1";
//const char *ssid = "lantai2";
//const char *password =  "passwordbaru";
WiFiClient clientSocket;
const char *serverIP = "192.168.43.247";
const uint16_t port = 6969;
unsigned long st;
char message[256];
int i, b;

void setupWiFi(){
  WiFi.begin(ssid, password);
  st = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if(millis()-st < 50){
      digitalWrite(LED_BUILTIN, HIGH);
    }
    else{
      digitalWrite(LED_BUILTIN, LOW);
    }
    if(millis()-st > 1000){
      st = millis();
      WiFi.begin(ssid, password);
    }
  }
}

void setupSocket(){
  digitalWrite(LED_BUILTIN, LOW);
  while(!clientSocket.connected()){
    if(WiFi.status() != WL_CONNECTED){ setupWiFi();}
    clientSocket.connect(serverIP, port);
  }
  digitalWrite(LED_BUILTIN, HIGH);
}

void readSocket(char *buffer){
  st = millis();
  while (clientSocket.available() == 0) {
    if (millis() - st > 5000) { // timeout in milisecond
      return;
    }
  }
  b=0;
  memset(buffer, 0, sizeof(buffer));
  while (clientSocket.available()) {
    buffer[b++] = clientSocket.read();
  }
}

void setup() {
  pinMode (LED_BUILTIN, OUTPUT);
  Serial.begin(115200);
  setupWiFi();
  Serial.println(WiFi.localIP());
  setupSocket();
}

void loop() {
  if(WiFi.status() != WL_CONNECTED){
    Serial.println("wifi dc");
    setupWiFi();
  }
  if(!clientSocket.connected()){
    Serial.println("socket dc");
    setupSocket();
  }
  sprintf(message, "$SHIP01%d", i++);
  i %= 1000;
  delay(500);
  if (clientSocket.connected()) {
    clientSocket.print(message);
  }
  readSocket(message);
}
