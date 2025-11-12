#include <Arduino.h>

void setup() {
  Serial.begin(115200); 
}

void loop() {

  const int samples = 10; // take 10 readings and average
  int accumulator = 0;

  for(int i = 0; i < samples; i++) {
    accumulator += analogRead(34);
    delay(2); // tiny delay so ADC settles a bit
  }

  int rawValue = accumulator / samples; // integer average

  float voltage = rawValue * (3.3 / 4095.0);

  Serial.print("Raw ADC Avg: ");
  Serial.print(rawValue);
  Serial.print("\t | \tVoltage: ");
  Serial.println(voltage, 4);

  delay(200); 
}
