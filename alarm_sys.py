""" Author : Maciej Drajewski """
import cv2
import serial
import time
import os
import threading
from ultralytics import YOLO

class Configuration:
    PORT_ARDUINO = 'COM3'
    COOLDOWN     = 6     # time between alarms
    FADEOUT      = 2     # time alarm fades away after not seeing human
    CONFIDENCE   = 0.65   # Ai confidence
    DETECT_EVERY = 3     # every frame that YOLO active

class Arduino:
    def __init__(self, port, baudrate=9600):
        self.ard = None
        try:
            self.ard = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)
            print("ARDUINO works")
        except serial.SerialException:
            print("ARDUINO disconected")

    def send(self,message:str):
        if self.ard:
            self.ard.write(f"{message}\n".encode()) #sending message to arduino changing msg to numbers with \n     

    def close(self):
        if self.ard:
            self.send("OK")
            self.ard.close()

class Recorder:
    def __init__(self):
        self.rec_dir = 'recordings'
        self.snap_dir = 'photos'
        self.writer = None
        self.file_counter = 0
        os.makedirs(self.rec_dir, exist_ok=True)
        os.makedirs(self.snap_dir, exist_ok=True)
#start recording
    def start(self):
        self.file_counter += 1
        path = f"{self.rec_dir}/alarm_{self.file_counter}.avi"
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.writer = cv2.VideoWriter(path, fourcc, 30.0, (640, 480)) #fps and resolution
        print(f"Recording - {path}")
#stop curent recording
    def stop(self):
        if self.writer:
            self.writer.release()
            self.writer = None
            print("Stoped Recording")

    def write_frame(self, frame):
        if self.writer:
            self.writer.write(frame)
#photo
    def snapshot(self, frame, alarm_num):
        path = f"{self.snap_dir}/snap_{alarm_num}.jpg"
        cv2.imwrite(path, frame)
        print(f"Took photo  - {path}")

class Yolo:
    #class responsible for running model in background so there is no issue blockage etc
    def __init__(self, model_name='yolov8n.pt'):
        print("Loading yolo model")
        self.model = YOLO(model_name) #yolov8n.pt
        print("YOLO is ready")
        
        self.frame_to_check = None
        self.detected_boxes = []
        self.new_results = False
        self.running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()

    def set_frame(self, frame):
        self.frame_to_check = frame.copy()

    def get_results(self):
        if self.new_results:
            self.new_results = False
            return self.detected_boxes.copy()
        return None

    def _process_loop(self):
        while self.running:
            if self.frame_to_check is not None:
                small_frame = cv2.resize(self.frame_to_check, (320, 240)) #lower resolution so it runs way faster than on 640x480
                results = self.model(small_frame, verbose=False, conf=Configuration.CONFIDENCE, classes=[0])[0] #only class 0 with is human
                self.frame_to_check = None

                new_boxes = []
                for box in results.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    new_boxes.append((x1 * 2, y1 * 2, x2 * 2, y2 * 2))

                self.detected_boxes = new_boxes
                self.new_results = True
            else:
                time.sleep(0.01)

    def stop(self):
        self.running = False

class SecuritySystem:
    def __init__(self):
        self.arduino = Arduino(Configuration.PORT_ARDUINO)
        self.recorder = Recorder()
        self.detector = Yolo()
        
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.alarm_active = False
        self.last_alarm_time = 0.0
        self.last_seen_time = 0.0
        self.human_on_screen = False
        self.alarm_count = 0
        self.frame_count = 0
        self.current_boxes = []

    def run(self):
        print("\n Press Q to quit")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1) # mirror flip camera 
            self.frame_count += 1
            now = time.time()

            if self.frame_count % Configuration.DETECT_EVERY == 0:
                self.detector.set_frame(frame)

            boxes = self.detector.get_results()
            if boxes is not None:
                if boxes:
                    self.human_on_screen = True
                    self.last_seen_time = now
                    self.current_boxes = boxes
                else:
                    if now - self.last_seen_time > Configuration.FADEOUT:
                        self.human_on_screen = False
                        self.current_boxes = []

            self._handle_alarm(now, frame)

            self._draw_hud(frame)

            cv2.imshow("Smart Security", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        self.cleanup()

    def _handle_alarm(self, now, frame):
        if self.human_on_screen and not self.alarm_active and (now - self.last_alarm_time > Configuration.COOLDOWN):
            self.alarm_active = True
            self.last_alarm_time = now
            self.alarm_count += 1
            
            self.arduino.send("ALARM")
            self.recorder.start()
            self.recorder.snapshot(frame, self.alarm_count)
            print(f"Alarm #{self.alarm_count} activated!!")

        elif self.alarm_active and not self.human_on_screen:
            self.alarm_active = False
            self.arduino.send("OK")
            self.recorder.stop()
            print("Alarm off")

        self.recorder.write_frame(frame)

    def _draw_hud(self, frame):
        if self.alarm_active:
            cv2.putText(frame, "!! ALARM !!", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
        else:
            cv2.putText(frame, "OK", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

        cv2.putText(frame, f"Alarms: {self.alarm_count}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

        for (x1, y1, x2, y2) in self.current_boxes:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, "Person", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    def cleanup(self):
        print("Turning off . ..")
        self.recorder.stop()
        self.detector.stop()
        self.cap.release()
        cv2.destroyAllWindows()
        self.arduino.close()

if __name__ == "__main__":
    app = SecuritySystem()
    app.run()
