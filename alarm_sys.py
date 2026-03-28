import cv2
import serial
import time
import os
import threading
from ultralytics import YOLO

PORT_ARDUINO = 'COM3'
COOLDOWN     = 8 #time set for cooldown between alarms
FADEOUT      = 2 #time that is needed for person to disappear for alarm to go away
CONF         = 0.6 # ai confidence in detecting humans
DETECT_EVERY = 3 # frames that yolo detects(efficients)

os.makedirs('recordings', exist_ok=True)
os.makedirs('snapshots',  exist_ok=True)

klatka_do_sprawdzenia = None
wykryte_boxy          = []
nowe_wyniki           = False

def watek_yolo():
    global klatka_do_sprawdzenia, wykryte_boxy, nowe_wyniki
    print("Loading YOLO")
    model = YOLO('yolov8n.pt')
    print("YOLO ready")

    while True:
        if klatka_do_sprawdzenia is not None:
            maly   = cv2.resize(klatka_do_sprawdzenia, (320, 240)) #szybciej dziala YOLO niz na 640x480
            wyniki = model(maly, verbose=False, conf=CONF, classes=[0])[0]
            klatka_do_sprawdzenia = None

            nowe_boxy = []
            for box in wyniki.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                nowe_boxy.append((x1 * 2, y1 * 2, x2 * 2, y2 * 2))

            wykryte_boxy = nowe_boxy
            nowe_wyniki  = True
        else:
            time.sleep(0.01)

nagrywarka    = None
licznik_plikow = 0

def start_nagrywania():
    global nagrywarka, licznik_plikow
    licznik_plikow += 1
    nazwa  = f"recordings/alarm_{licznik_plikow}.avi"
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    nagrywarka = cv2.VideoWriter(nazwa, fourcc, 20.0, (640, 480))
    print(f"[REC] {nazwa}")

def stop_nagrywania():
    global nagrywarka
    if nagrywarka is not None:
        nagrywarka.release()
        nagrywarka = None
        print("[REC] stopped")

def zrob_zdjecie(frame, nr):
    cv2.imwrite(f"snapshots/snap_{nr}.jpg", frame)
    print(f"[SNAP] snap_{nr}.jpg")

try:
    ard = serial.Serial(PORT_ARDUINO, 9600, timeout=1)
    time.sleep(2)
    print("Arduino OK")
except serial.SerialException:
    ard = None
    print("no Arduino")

threading.Thread(target=watek_yolo, daemon=True).start()

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

alarm_aktywny       = False
ostatni_alarm       = 0.0
ostatnio_widziany   = 0.0
czlowiek_na_ekranie = False
licznik_alarmow     = 0
nr_klatki           = 0
aktualne_ramki      = []

print("press Q to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame     = cv2.flip(frame, 1)
    nr_klatki += 1
    teraz     = time.time()

    if nr_klatki % DETECT_EVERY == 0:
        klatka_do_sprawdzenia = frame.copy()

    if nowe_wyniki:
        boxy        = wykryte_boxy.copy()
        nowe_wyniki = False
    else:
        boxy = None

    if boxy is not None:
        if boxy:
            czlowiek_na_ekranie = True
            ostatnio_widziany   = teraz
            aktualne_ramki      = boxy
        else:
            if teraz - ostatnio_widziany > FADEOUT:
                czlowiek_na_ekranie = False
                aktualne_ramki      = []

    if czlowiek_na_ekranie and not alarm_aktywny and teraz - ostatni_alarm > COOLDOWN:
        alarm_aktywny   = True
        ostatni_alarm   = teraz
        licznik_alarmow += 1
        if ard: ard.write(b"ALARM\n")
        start_nagrywania()
        zrob_zdjecie(frame, licznik_alarmow)
        print(f"ALARM #{licznik_alarmow}")

    elif alarm_aktywny and not czlowiek_na_ekranie:
        alarm_aktywny = False
        if ard: ard.write(b"OK\n")
        stop_nagrywania()
        print("OK - cleared")

    if nagrywarka is not None:
        nagrywarka.write(frame)

    if alarm_aktywny:
        cv2.putText(frame, "!! ALARM !!", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
    else:
        cv2.putText(frame, "OK", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

    cv2.putText(frame, f"Alarms: {licznik_alarmow}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

    for (x1, y1, x2, y2) in aktualne_ramki:
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(frame, "Person", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    cv2.imshow("Alarm", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

stop_nagrywania()
cap.release()
cv2.destroyAllWindows()
if ard:
    ard.write(b"OK\n")
    ard.close()
