//---------------------------------------------------
//  INCLUDES & GLOBALS
//---------------------------------------------------
#include <Wire.h>
#include <QMC5883LCompass.h>

QMC5883LCompass compass;

// --- MPU6050 ADDR & REGISTERS ---
#define MPU6050_ADDR           0x68
#define MPU6050_REG_PWR_MGMT_1 0x6B
#define MPU6050_REG_ACCEL_XOUT_H 0x3B
#define MPU6050_REG_GYRO_XOUT_H  0x43

// --- IMU SCALES ---
#define ACCEL_SCALE 16384.0    // ±2g
#define GYRO_SCALE   131.0     // ±250°/s

// --- ENCODER PINS ---
const uint8_t ENC_L = 2;
const uint8_t ENC_R = 3;

volatile long leftCount  = 0;
volatile long rightCount = 0;

void encL_ISR() { leftCount++; }
void encR_ISR() { rightCount++; }

// --- MOTOR PINS (L298N) ---
const uint8_t ENA = 11, IN1 = 13, IN2 = 12;  // Left motor
const uint8_t ENB = 10, IN3 = 9,  IN4 = 8;   // Right motor

// --- LOOP TIMING ---
unsigned long lastTime;
double dt = 0.02;

// --- ORIENTATION STATE ---
double pitch = 0, roll = 0, yaw = 0;

//---------------------------------------------------
//  SETUP
//---------------------------------------------------
void setup() {
  Serial.begin(115200);
  Wire.begin();

  // MPU6050 init (wake up)
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(MPU6050_REG_PWR_MGMT_1);
  Wire.write(0);
  Wire.endTransmission(true);

  // Compass init
  compass.init();

  // Encoders
  pinMode(ENC_L, INPUT_PULLUP);
  pinMode(ENC_R, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_L), encL_ISR, RISING);
  attachInterrupt(digitalPinToInterrupt(ENC_R), encR_ISR, RISING);

  // Motor pins
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // Start stopped
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);

  lastTime = millis();
  delay(500);

  Serial.println("UNO READY: SENSORS + MOTOR CONTROL ACTIVE");
}

//---------------------------------------------------
//  READ MPU6050 (raw accel + gyro)
//---------------------------------------------------
void read_MPU6050(double &ax, double &ay, double &az,
                  double &gx, double &gy, double &gz) {

  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(MPU6050_REG_ACCEL_XOUT_H);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU6050_ADDR, 14, true);

  ax = (Wire.read() << 8 | Wire.read()) / ACCEL_SCALE;
  ay = (Wire.read() << 8 | Wire.read()) / ACCEL_SCALE;
  az = (Wire.read() << 8 | Wire.read()) / ACCEL_SCALE;

  gx = (Wire.read() << 8 | Wire.read()) / GYRO_SCALE;
  gy = (Wire.read() << 8 | Wire.read()) / GYRO_SCALE;
  gz = (Wire.read() << 8 | Wire.read()) / GYRO_SCALE;
}

//---------------------------------------------------
//  SET MOTORS (L298N, PWM + DIR)
//  leftPWM / rightPWM in range [-255, 255]
//---------------------------------------------------
void setMotors(int leftPWM, int rightPWM) {
  // ---- LEFT MOTOR ----
  if (leftPWM >= 0) {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
  } else {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    leftPWM = -leftPWM;
  }
  analogWrite(ENA, constrain(leftPWM, 0, 255));

  // ---- RIGHT MOTOR ----
  if (rightPWM >= 0) {
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  } else {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
    rightPWM = -rightPWM;
  }
  analogWrite(ENB, constrain(rightPWM, 0, 255));
}

//---------------------------------------------------
//  PARSE MOTOR COMMAND FROM RPI: "L:150 R:120"
//---------------------------------------------------
void handleMotorCommand(const String &line) {
  // Expecting format:  L:<int> R:<int>
  int idxL = line.indexOf("L:");
  int idxR = line.indexOf("R:");

  if (idxL == -1 || idxR == -1) return;

  int spaceAfterL = line.indexOf(' ', idxL);
  if (spaceAfterL == -1) return;

  int left  = line.substring(idxL + 2, spaceAfterL).toInt();
  int right = line.substring(idxR + 2).toInt();

  setMotors(left, right);
}

//---------------------------------------------------
// MAIN LOOP
//---------------------------------------------------
void loop() {
  //-------------------------------------------------
  // 1. READ MOTOR COMMANDS FROM RPi (NON-BLOCKING)
  //-------------------------------------------------
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("L:")) {
      handleMotorCommand(line);
    }
  }

  //-------------------------------------------------
  // 2. TIME STEP
  //-------------------------------------------------
  unsigned long now = millis();
  dt = (now - lastTime) / 1000.0;
  if (dt <= 0) dt = 0.02;
  lastTime = now;

  //-------------------------------------------------
  // 3. READ IMU: MPU6050
  //-------------------------------------------------
  double ax, ay, az, gx, gy, gz;
  read_MPU6050(ax, ay, az, gx, gy, gz);

  //-------------------------------------------------
  // 4. READ COMPASS: QMC5883L
  //-------------------------------------------------
  compass.read();
  float mx = compass.getX();
  float my = compass.getY();
  float mz = compass.getZ();

  //-------------------------------------------------
  // 5. READ ENCODERS ATOMICALLY
  //-------------------------------------------------
  noInterrupts();
  long encL = leftCount;
  long encR = rightCount;
  interrupts();

  //-------------------------------------------------
  // 6. SIMPLE COMPLEMENTARY FILTER (PITCH/ROLL/YAW)
  //-------------------------------------------------
  double pitchAcc = atan2(ay, sqrt(ax*ax + az*az)) * 180.0 / PI;
  double rollAcc  = atan2(-ax, sqrt(ay*ay + az*az)) * 180.0 / PI;

  pitch = 0.98 * (pitch + gx * dt) + 0.02 * pitchAcc;
  roll  = 0.98 * (roll  + gy * dt) + 0.02 * rollAcc;

  double pitchRad = pitch * PI / 180.0;
  double rollRad  = roll  * PI / 180.0;

  float Xh = mx * cos(pitchRad) + mz * sin(pitchRad);
  float Yh = mx * sin(rollRad)*sin(pitchRad) + my*cos(rollRad)
             - mz*sin(rollRad)*cos(pitchRad);

  yaw = atan2(Yh, Xh) * 180.0 / PI;
  if (yaw < 0) yaw += 360;

// -------------------------------------------------
// SEND SINGLE CLEAN CSV LINE
// -------------------------------------------------

Serial.print(encL); Serial.print(",");
Serial.print(encR); Serial.print(",");

Serial.print(ax, 4); Serial.print(",");
Serial.print(ay, 4); Serial.print(",");
Serial.print(az, 4); Serial.print(",");

Serial.print(gx, 4); Serial.print(",");
Serial.print(gy, 4); Serial.print(",");
Serial.print(gz, 4); Serial.print(",");

Serial.print(yaw, 2); Serial.print(",");
Serial.print(pitch, 2); Serial.print(",");
Serial.print(roll, 2); Serial.print(",");

Serial.print(mx); Serial.print(",");
Serial.print(my); Serial.print(",");
Serial.println(mz);
  
  // ---- RESET ENCODERS FOR NEXT DELTA ----
  noInterrupts();
  leftCount = 0;
  rightCount = 0;
  interrupts();
  
  delay(20);  // ~50 Hz
}