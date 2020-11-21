#include <WiFi.h>

int LED_BUILTIN = 2;
//const char *ssid = "Anonymous";
//const char *password = "whatthefuck1";
//const char *ssid = "lantai2";
//const char *password = "passwordbaru";
const char *ssid = "sClient";
const char *password = "gukgukmeong";
//const char *ssid = "SmartLifeboat";
//const char *password = "gukgukmeong";
WiFiClient clientSocket;
const char *serverIP = "10.181.15.202";
const uint16_t port = 6900;
const char *suicideFlag = "$!!";
char message[256];
unsigned long t;
int i, b;
double lat = -9.726921, lon = 114.563657;

void setupWiFi(){
  WiFi.begin(ssid, password);
  unsigned long st = millis();
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
  unsigned long st = millis();
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
  if(strstr(buffer, suicideFlag) != NULL){
    suicide();
  }
}

void setup() {
  pinMode (LED_BUILTIN, OUTPUT);
  Serial.begin(115200);
  setupWiFi();
  Serial.println(WiFi.localIP());
  setupSocket();
}

void suicide(){
  WiFi.disconnect();
  digitalWrite(LED_BUILTIN, LOW);
  while(true){
    // dead
  }
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
  sprintf(message, "$JCKT;%lf;%lf", lat, lon);
  lat += 0.01;
  lon += 0.01;
  delay(500);
  if (clientSocket.connected()) {
    clientSocket.print(message);
  }
  readSocket(message);
  t = millis();
  while(millis()-t < 500){
    delay(5);
  }
}
