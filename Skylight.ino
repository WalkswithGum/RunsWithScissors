
#include "SparkFun_OPT4048.h"  // Light sensor.
#include "SoftwareSerial.h"    // MonLisa.
#include "Wire.h"
#include "LowPower.h"  // For sleepy time.

SparkFun_OPT4048 myColor;       // Sensor.
SoftwareSerial mySerial(3, 2);  // RX , TX for MonaLisa.

int sensorK;          // Actual (Color Temp) measured by Arduino sensor.
int sensorLUX;        // Actual (Brightness) measured by Arduino sensor.
int factorK = 1;      // If measured K needs to be tweeked.
int factorLUX = 125;  // Convert actual LUX to Skylight's 0 - 100+ scale.
int setK;             // Color Temp (K) to set Skylight to ( 0K - 6535K+ ).
int setLUX;           // 1 - 100 Scale: 1 - aprx. 13,000 LUX output.
int oldLUX;           // Old value for comparision.
int oldK;             // Old value for comparision.
int rndK;             // Rounds so there can be fewer Cases.
int rndLUX;           // Rounds so there can be fewer Cases.
int TT = 1;           // Time (seconds) for transition to Skylight's new K/Lux output.

void setup() {
  Serial.begin(38400);
  mySerial.begin(38400);  // MonaLisa.
  Wire.begin();

  if (!myColor.begin()) {
    Serial.println("   OPT4048 Sensor not detected");
    while (1)
      ;
  }
  myColor.setBasicSetup();
  Serial.println("   Ready to go!");
}

void loop() {
  // Get readings from sensor.
  sensorLUX = myColor.getLux();
  sensorK = round(myColor.getCCT());

  setLUX = (sensorLUX / factorLUX) + 1;  // Minimum = 1 = NIGHT.
  setK = sensorK;                        // For possible tweeking needed in future...

  // Light can only output 2000 - 6500K right now.
  if (setK <= 2000) {
    setK = 2000;
  } else if (setK >= 6500) {
    setK = 6500;
  }

  //Serial.println(setK); // Debuging...

  if (setLUX >= 100) {  // Can only ask for so much...
    setLUX = 100;
  } else if (setLUX <= 0) {  // For oddball negative LUX read output errors. Flip the - to +.
    setLUX = (sensorLUX * -1);
  } else if (setLUX == 1) {  //  1 = NIGHT = Anything < 125 actual lux reading.
    setK = 6500;             // Night should be high K.
  }

  rndK = round((setK - 1999) / 225);  //  Should produce a number from 0 to 20. Expand gradiant later.
  rndLUX = round((setLUX / 5));       //  Should produce a number from 0 to 20. Or figure a way to send variables.

  if (rndLUX <= 1) {  // Always have LUX on to at least '1' for now.
    rndLUX = 1;
  }

  if (rndK <= 1) {  // Always have K on to at least '1'. 2000K.
    rndK = 1;
  }

  printToSerial();
  Serial.flush();  // Complete the serial print before going to sleep.
  // 
toHUBlux();Serial()){}