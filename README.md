# 🛡️ Smart AI Security System

![demo](presentation.gif)

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![OpenCV](https://img.shields.io/badge/opencv-%23white.svg?logo=opencv&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLO-v8-yellow.svg)
![Hardware](https://img.shields.io/badge/hardware-Arduino-00979D.svg)

An intelligent, Object-Oriented security camera system powered by Python, OpenCV, and Ultralytics YOLOv8. The system detects human presence in real-time, triggers external hardware alarms via Arduino, and automatically records video evidence. 

Built with performance in mind, it utilizes multithreading to ensure a lag-free camera feed while the AI performs heavy object detection in the background.

---

## 🚀 Key Features

* **Real-time AI Detection:** Uses the `yolov8n.pt` model for fast, lightweight, and highly accurate human detection.
* **Multithreading Architecture:** AI inference runs on a dedicated background daemon thread, preventing UI blockage and maintaining high FPS.
* **Hardware Integration:** Communicates seamlessly with Arduino via Serial port to trigger physical alarms (e.g., LEDs, buzzers, sirens).
* **Automated Evidence Collection:** Automatically starts recording `.avi` video clips and saves `.jpg` snapshots the moment an intrusion is detected.
* **Clean Code & OOP:** Modular codebase divided into single-responsibility classes for easy maintenance, readability, and scalability.

---

## 🏗️ Project Architecture

The project was designed from scratch using Object-Oriented Programming (OOP) principles. Here is the breakdown of the core components:

1. **`Configuration`** - The central hub for all magic numbers and settings (ports, cooldowns, AI confidence thresholds).
2. **`Arduino`** - Hardware controller responsible strictly for Serial communication. Handles connection initialization, sending signals, and safe disconnections.
3. **`Recorder`** - Media manager that creates necessary directories (`/recordings`, `/photos`) and handles the video writing stream and snapshot generation.
4. **`Yolo`** - Implements the **Producer-Consumer pattern**. Runs on a separate thread, constantly processing frames provided by the main thread without blocking the camera feed.
5. **`SecuritySystem`** - The main Orchestrator. Connects all modules, captures the webcam feed, processes the business logic, and draws the HUD on the screen.

---

## 📋 Requirements

### Hardware
* Standard Webcam (USB or built-in)
* Arduino board (Uno/Nano/Mega etc.) connected via USB

### Software
* Python 3.9 or higher
* Required Python packages:
  * `opencv-python`
  * `ultralytics`
  * `pyserial`



