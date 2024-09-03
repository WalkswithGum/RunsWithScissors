
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
  // Add comparision of old and new readings to avoid sending duplicate commands for no reason.
  toHUBlux();
  delay(500);  // Debug...
  toHUBk();
 // testOne();

  gotoSLEEP();
}


void testOne() {
mySerial.write("123456789012345.");
delay(1000);
}

void printToSerial() {  // Prints out the actual LUX and K data to Serial.
  Serial.print("Sensor: ");
  Serial.print(sensorK);
  Serial.print("K / ");
  Serial.print(sensorLUX);
  Serial.print("Lx      Skylight K: ");
  Serial.print(setK);
  Serial.print("  Level %: ");
  Serial.print(setLUX);
  Serial.print("      rndK: ");
  Serial.print(rndK);
  Serial.print("   rndLUX: ");
  Serial.println(rndLUX);
}

void toHUBlux() {  // Send LUX data to HUB.
  switch (rndLUX) {
    case 1:
      mySerial.write("L_1.");
      break;
    case 2:
      mySerial.write("L_2.");
      break;
    case 3:
      mySerial.write("L_3.");
      break;
    case 4:
      mySerial.write("L_4.");
      break;
    case 5:
      mySerial.write("L_5.");
      break;
    case 6:
      mySerial.write("L_6.");
      break;
    case 7:
      mySerial.write("L_7.");
      break;
    case 8:
      mySerial.write("L_8.");
      break;
    case 9:
      mySerial.write("L_9.");
      break;
    case 10:
      mySerial.write("L_10.");
      break;
    case 11:
      mySerial.write("L_11.");
      break;
    case 12:
      mySerial.write("L_12.");
      break;
    case 13:
      mySerial.write("L_13.");
      break;
    case 14:
      mySerial.write("L_14.");
      break;
    case 15:
      mySerial.write("L_15.");
      break;
    case 16:
      mySerial.write("L_16.");
      break;
    case 17:
      mySerial.write("L_17.");
      break;
    case 18:
      mySerial.write("L_18.");
      break;
    case 19:
      mySerial.write("L_19.");
      break;
    case 20:
      mySerial.write("L_20.");
      break;
    default:
      break;
  }
}

void toHUBk() {  // Send K data to HUB.
  switch (rndK) {
    case 1:
      mySerial.write("K_1.");
      break;
    case 2:
      mySerial.write("K_2.");
      break;
    case 3:
      mySerial.write("K_3.");
      break;
    case 4:
      mySerial.write("K_4.");
      break;
    case 5:
      mySerial.write("K_5.");
      break;
    case 6:
      mySerial.write("K_6.");
      break;
    case 7:
      mySerial.write("K_7.");
      break;
    case 8:
      mySerial.write("K_8.");
      break;
    case 9:
      mySerial.write("K_9.");
      break;
    case 10:
      mySerial.write("K_10.");
      break;
    case 11:
      mySerial.write("K_11.");
      break;
    case 12:
      mySerial.write("K_12.");
      break;
    case 13:
      mySerial.write("K_13.");
      break;
    case 14:
      mySerial.write("K_14.");
      break;
    case 15:
      mySerial.write("K_15.");
      break;
    case 16:
      mySerial.write("K_16.");
      break;
    case 17:
      mySerial.write("K_17.");
      break;
    case 18:
      mySerial.write("K_18.");
      break;
    case 19:
      mySerial.write("K_19.");
      break;
    case 20:
      mySerial.write("K_20.");
      break;
    default:
      break;
  }
}

void gotoSLEEP() {
  LowPower.powerDown(SLEEP_8S, ADC_OFF, BOD_OFF);  //  8s
  //LowPower.powerDown(SLEEP_8S, ADC_OFF, BOD_OFF);  //  16s
  // LowPower.powerDown(SLEEP_8S, ADC_OFF, BOD_OFF);  //  24s
  //LowPower.powerDown(SLEEP_8S, ADC_OFF, BOD_OFF);  //  32s
  //LowPower.powerDown(SLEEP_8S, ADC_OFF, BOD_OFF);   //  40s
  //LowPower.powerDown(SLEEP_8S, ADC_OFF, BOD_OFF);   //  48s
  //LowPower.powerDown(SLEEP_8S, ADC_OFF, BOD_OFF);   //  56s
}
