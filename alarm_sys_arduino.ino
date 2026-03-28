
const int LED_OK  = 6;
const int LED_ERR = 7;
const int BUZZER  = 8;

void setup() {
  Serial.begin(9600);
  pinMode(LED_OK,  OUTPUT);
  pinMode(LED_ERR, OUTPUT);
  pinMode(BUZZER,  OUTPUT);
  digitalWrite(LED_OK, HIGH);
}

void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "ALARM") {
      digitalWrite(LED_OK,  LOW);
      digitalWrite(LED_ERR, HIGH);
      tone(BUZZER, 1800, 500);
    } else if (cmd == "OK") {
      digitalWrite(LED_OK,  HIGH);
      digitalWrite(LED_ERR, LOW);
      noTone(BUZZER);
    }
  }
}