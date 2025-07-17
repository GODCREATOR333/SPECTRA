#include <Arduino.h>

#define L_EN_PIN 22
#define R_EN_PIN 23
#define LPWM_PIN 19
#define RPWM_PIN 18

#define MAX_PWM_LIMIT 255
#define STEP_SIZE 1

int sweep_min = -20;
int sweep_max = 20;
int current = sweep_min;
int frameDelay = 40;

bool isRunning = false;
bool reverse = false;
bool isAnimating = false;
unsigned long animStart = 0;

enum WaveformType { LINEAR, SINE, TRIANGLE, SQUARE };
WaveformType mode = LINEAR;

void driveVCM(int power);

void setup() {
  Serial.begin(115200);

  pinMode(L_EN_PIN, OUTPUT);
  pinMode(R_EN_PIN, OUTPUT);
  pinMode(LPWM_PIN, OUTPUT);
  pinMode(RPWM_PIN, OUTPUT);

  digitalWrite(L_EN_PIN, HIGH);
  digitalWrite(R_EN_PIN, HIGH);

  analogWrite(LPWM_PIN, 0);
  analogWrite(RPWM_PIN, 0);

  Serial.println("--- VCM Sweep + Animation Control ---");
  Serial.println("Keys: s=start, x=stop, r=reverse, m=waveform, a=animate");
  Serial.println("      u/d=sweep size, [/]=shift, +/-=speed");
}

void loop() {
  // --- Serial Input ---
  if (Serial.available()) {
    char cmd = Serial.read();
    switch (cmd) {
      case 's':
        isRunning = true;
        isAnimating = false;
        Serial.println("Sweep started.");
        break;
      case 'x':
        isRunning = false;
        isAnimating = false;
        analogWrite(LPWM_PIN, 0);
        analogWrite(RPWM_PIN, 0);
        Serial.println("Sweep stopped.");
        break;
      case 'r':
        reverse = !reverse;
        Serial.println(reverse ? "Direction: REVERSED" : "Direction: NORMAL");
        break;
      case 'u':
        if (sweep_max - sweep_min < 200) {
          sweep_max += 1;
          sweep_min -= 1;
        }
        Serial.printf("Sweep range: [%d, %d]\n", sweep_min, sweep_max);
        break;
      case 'd':
        if (sweep_max - sweep_min > 4) {
          sweep_max -= 1;
          sweep_min += 1;
        }
        Serial.printf("Sweep range: [%d, %d]\n", sweep_min, sweep_max);
        break;
      case '[':
        sweep_max -= 1;
        sweep_min -= 1;
        Serial.printf("Sweep shifted left: [%d, %d]\n", sweep_min, sweep_max);
        break;
      case ']':
        sweep_max += 1;
        sweep_min += 1;
        Serial.printf("Sweep shifted right: [%d, %d]\n", sweep_min, sweep_max);
        break;
      case '+':
        if (frameDelay > 5) frameDelay -= 5;
        Serial.printf("Sweep speed increased. Delay: %dms\n", frameDelay);
        break;
      case '-':
        if (frameDelay < 200) frameDelay += 5;
        Serial.printf("Sweep speed decreased. Delay: %dms\n", frameDelay);
        break;
      case 'm':
        mode = static_cast<WaveformType>((mode + 1) % 4);
        Serial.print("Waveform mode: ");
        switch (mode) {
          case LINEAR: Serial.println("LINEAR"); break;
          case SINE: Serial.println("SINE"); break;
          case TRIANGLE: Serial.println("TRIANGLE"); break;
          case SQUARE: Serial.println("SQUARE"); break;
        }
        break;
      case 'a':
        isAnimating = true;
        isRunning = false;
        animStart = millis();
        Serial.println("Animation started.");
        break;
    }
  }

  // --- Animation Mode ---
     if (isAnimating) {
    static unsigned long t0 = micros();
    unsigned long nowMicros = micros();
    float t = (nowMicros - t0) / 1e6; // seconds

    // End after 10 seconds
    if (t > 10.0) {
      isAnimating = false;
      driveVCM(0);
      Serial.println("Animation ended.");
      return;
    }

    float freq = 50.0;  // Hz — try 50, 60, 100 for different effects
    float theta = 2 * PI * freq * t;

    int center = (sweep_min + sweep_max) / 2;
    int amp = (sweep_max - sweep_min) / 2;
    int pwmOut = center + amp * sin(theta);

    driveVCM(pwmOut);
    return;
  }




  // --- Normal Sweep Modes ---
  if (!isRunning) return;

  int pwmOut = 0;

  switch (mode) {
    case LINEAR:
      driveVCM(current);
      delay(frameDelay);
      if (!reverse) {
        current += STEP_SIZE;
        if (current > sweep_max) current = sweep_min;
      } else {
        current -= STEP_SIZE;
        if (current < sweep_min) current = sweep_max;
      }
      return;

    case SINE: {
      static unsigned long t0 = millis();
      float theta = 2 * PI * ((millis() - t0) % 10000) / 10000.0;
      int center = (sweep_min + sweep_max) / 2;
      int amp = (sweep_max - sweep_min) / 2;
      pwmOut = center + amp * sin(theta);
      break;
    }

    case TRIANGLE: {
      static int val = sweep_min;
      static bool rising = true;
      if (rising) {
        val += STEP_SIZE;
        if (val >= sweep_max) rising = false;
      } else {
        val -= STEP_SIZE;
        if (val <= sweep_min) rising = true;
      }
      pwmOut = val;
      break;
    }

    case SQUARE: {
      static bool high = false;
      static unsigned long lastToggle = 0;
      if (millis() - lastToggle > frameDelay * 2) {
        high = !high;
        lastToggle = millis();
      }
      pwmOut = high ? sweep_max : sweep_min;
      break;
    }
  }

  driveVCM(pwmOut);
  delay(frameDelay);
}

void driveVCM(int power) {
  power = constrain(power, -MAX_PWM_LIMIT, MAX_PWM_LIMIT);
  if (power > 0) {
    analogWrite(LPWM_PIN, 0);
    analogWrite(RPWM_PIN, power);
  } else {
    analogWrite(RPWM_PIN, 0);
    analogWrite(LPWM_PIN, -power);
  }
}
