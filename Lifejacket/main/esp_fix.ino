 #include <TinyGPS++.h>
#include <HardwareSerial.h>
#include <Wire.h>               

float latitude , longitude;
char lat_str[16], lon_str[16];
bool startFlag=0;
int serialIdx;
char serialData[100];
char serialTemp;
const uint16_t port = 6900;
const char *suicideFlag = "$!!";
char message[256];
unsigned long t;
int i, b;
//double lat = -9.726921, lon = 114.563657;

//TinyGPSPlus gps;
//HardwareSerial SerialGPS(2);
//
//HardwareSerial SendData(1);



void assignDouble(char *buff, double value, int places) {
  memset(buff, 0, sizeof(buff));
  // this is used to cast digits 
  int digit;
  int idx = 0;
  double tens = 0.1;
  int tenscount = 0;
  int i;
  double tempDouble = value;

  double d = 0.5;
  if (value < 0)
    d *= -1.0;
  // divide by ten for each decimal place
  for (i = 0; i < places; i++)
    d/= 10.0;    
  // this small addition, combined with truncation will round our values properly 
  tempDouble +=  d;

  if (value < 0)
    tempDouble *= -1.0;
  while ((tens * 10.0) <= tempDouble) {
    tens *= 10.0;
    tenscount += 1;
  }
  // write out the negative if needed
  if (value < 0){
    buff[idx] = '-';
    ++idx;
//    Serial.print('-');
  }
  if (tenscount == 0){
    buff[idx] = '0';
    ++idx;
//    Serial.print(0, DEC);
  }
  
  for (i=0; i< tenscount; i++) {
    digit = (int) (tempDouble/tens);
    //Serial.print(digit, DEC);
    buff[idx] = digit+48;
    ++idx;
    tempDouble = tempDouble - ((double)digit * tens);
    tens /= 10.0;
  }

  // if no places after decimal, stop now and return
  if (places <= 0)
    return;
  // otherwise, write the point and continue on
  //Serial.print('.');
  buff[idx] = '.';
  ++idx;

  // now write out each decimal place by shifting digits one by one into the ones place and writing the truncated value
  for (i = 0; i < places; i++) {
    tempDouble *= 10.0; 
    digit = (int) tempDouble;
    //Serial.print(digit,DEC);
    buff[idx] = digit+48;
    ++idx;
    // once written, subtract off that digit
    tempDouble = tempDouble - (double) digit; 
  }
}

void setup()
{
  Serial.begin(115200);
//  SerialGPS.begin(9600, SERIAL_8N1, 16, 17);
//  SendData.begin(115200, SERIAL_8N1, 9, 10);
}

void loop()
{
//  while (SerialGPS.available() > 0) {
//    gps.encode(SerialGPS.read());
//  } 
//  if (gps.location.isValid()){
//    assignDouble(lat_str, gps.location.lat(), 8);
//    assignDouble(lon_str, gps.location.lng(), 8);
//  }
  sprintf(message, "$JCKT;%s;%s", lat_str, lon_str);
//  SendData.print(message);
  Serial.print(message);
//  lat += 0.01;
//  lon += 0.01;
  delay(500);

  }
