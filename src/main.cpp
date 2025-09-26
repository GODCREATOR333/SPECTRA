#include <Arduino.h>

// Pins
const int X_RPWM_PIN = 25, X_LPWM_PIN = 26;
const int Y_RPWM_PIN = 27, Y_LPWM_PIN = 23;

// PWM
const int PWM_FREQ = 25000;
const int PWM_RESOLUTION = 8;
const int X_RPWM_CHANNEL = 0, X_LPWM_CHANNEL = 1;
const int Y_RPWM_CHANNEL = 2, Y_LPWM_CHANNEL = 3;

// State
enum Axis { AXIS_X, AXIS_Y };
Axis currentAxis = AXIS_X;
int power = 0;   // -255..255

// Helpers
void moveX(int p) {
  p = constrain(p, -255, 255);
  if (p > 0) { ledcWrite(X_LPWM_CHANNEL, 0); ledcWrite(X_RPWM_CHANNEL, p); }
  else       { ledcWrite(X_RPWM_CHANNEL, 0); ledcWrite(X_LPWM_CHANNEL, -p); }
}
void moveY(int p) {
  p = constrain(p, -255, 255);
  if (p > 0) { ledcWrite(Y_LPWM_CHANNEL, 0); ledcWrite(Y_RPWM_CHANNEL, p); }
  else       { ledcWrite(Y_RPWM_CHANNEL, 0); ledcWrite(Y_LPWM_CHANNEL, -p); }
}

void applyPower() {
  if (currentAxis == AXIS_X) { moveX(power); moveY(0); }
  else                       { moveY(power); moveX(0); }
  Serial.printf("Axis=%s Power=%d\n", currentAxis==AXIS_X?"X":"Y", power);
}

void setup() {
  Serial.begin(115200);
  ledcSetup(X_RPWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
  ledcSetup(X_LPWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
  ledcSetup(Y_RPWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
  ledcSetup(Y_LPWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
  ledcAttachPin(X_RPWM_PIN, X_RPWM_CHANNEL);
  ledcAttachPin(X_LPWM_PIN, X_LPWM_CHANNEL);
  ledcAttachPin(Y_RPWM_PIN, Y_RPWM_CHANNEL);
  ledcAttachPin(Y_LPWM_PIN, Y_LPWM_CHANNEL);
  Serial.println("Controls: x=select X | y=select Y | a=power-1 | d=power+1 | space=stop");
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    switch (c) {
      case 'x': currentAxis = AXIS_X; power = 0; applyPower(); break;
      case 'y': currentAxis = AXIS_Y; power = 0; applyPower(); break;
      case 'a': power--; applyPower(); break;
      case 'd': power++; applyPower(); break;
      case ' ': power = 0; applyPower(); break;
    }
    power = constrain(power, -255, 255);
  }
}
