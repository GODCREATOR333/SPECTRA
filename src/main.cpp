#include <Arduino.h>

// Nano to ULN2003 IN1–IN4
const int motorPins[4] = {8, 10, 9, 11};  // IN1, IN2, IN3, IN4

// Half-step sequence (8 steps)
const byte halfStep[8][4] = {
  {1, 0, 0, 0},
  {1, 1, 0, 0},
  {0, 1, 0, 0},
  {0, 1, 1, 0},
  {0, 0, 1, 0},
  {0, 0, 1, 1},
  {0, 0, 0, 1},
  {1, 0, 0, 1}
};

const int stepDelay = 1;     // ms delay per step
const int stepsPerRev = 4096;  // 1 revolution = 4096 half-steps (for 64:1 gear reduction)

void stepMotor(int stepIndex);  // ← Add this above setup()
 
// === Setup ===
void setup() {
  for (int i = 0; i < 4; i++) {
    pinMode(motorPins[i], OUTPUT);
    digitalWrite(motorPins[i], LOW);
  }

  delay(1000);
}

// === Loop ===
void loop() {
  // Rotate forward
  for (int i = 0; i < stepsPerRev; i++) {
    stepMotor(i % 8);
    delay(stepDelay);
  }

  delay(2000);

  // Rotate backward
  for (int i = 0; i < stepsPerRev; i++) {
    stepMotor(7 - (i % 8));
    delay(stepDelay);
  }

  delay(2000);
}

// === Step Control ===
void stepMotor(int stepIndex) {
  for (int i = 0; i < 4; i++) {
    digitalWrite(motorPins[i], halfStep[stepIndex][i]);
  }
}
