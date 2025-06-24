# Raspberry Pi Chess Robot

The Raspberry Pi Chess Robot is a DIY robotic arm project built using Arduino and Raspberry Pi. It plays chess autonomously by combining robotics, computer vision, and chess engine logic.

## Table of Contents

- [Requirements](#requirements)
- [Modules List](#modules-list)
- [Getting Started](#getting-started)
- [Install](#install)
- [Run](#run)
- [Authors](#authors)
- [License](#license)
- [Resources](#resources)

## Requirements

### Hardware

- Raspberry Pi (tested on Raspberry Pi 4)
- Arduino Uno (or compatible board)
- 5 DOF Robotic Arm with servo motors
- USB Camera or Raspberry Pi Camera Module
- Jumper wires, breadboard, and power supply
- Chessboard with standard pieces
- Display, keyboard, mouse (for interface)

### Software

- OpenCV (for board detection)
- Stockfish (chess engine)
- python-chess (interface with engine)
- PySimpleGUI or FreeSimpleGUI (interface)
- Arduino IDE (for uploading code to Arduino)
- picamera[array] (if using Raspberry Pi camera)

## Modules List

- Vision Module
- Chess Logic
- Arm Control
- Interface

## Getting Started

Clone the repository:

```bash
cd <your_workspace>
git clone https://github.com/<your_username>/Chess-Robot.git
```

## Install

### On Raspberry Pi

1. Create a virtual environment:

```bash
python3 -m venv env
source env/bin/activate
```

2. Install dependencies:

```bash
pip3 install -r requirements.txt
```

3. For Raspberry Pi Camera Module:

```bash
pip3 install "picamera[array]"
```

4. If OpenCV causes issues:

```bash
sudo apt-get install libatlas-base-dev libjasper-dev libqtgui4 libqt4-test libhdf5-dev libhdf5-serial-dev python3-pyqt5 stockfish
sudo pip3 install opencv-python==4.5.5.64 opencv-contrib-python
```

## Run

```bash
cd <project_directory>
python Interface.py
```

## Authors

- Mohamed Ramzy

## License

This project is open source and available under the MIT License.

## Limitations

- The chessboard must be within the reach of the robotic arm.
- The system is designed for a DIY robotic arm controlled via Arduino, so you may need to adapt inverse kinematics and servo control logic if your arm is different.


## Resources

- [DIY Arduino Robot Arm with Smartphone Control – HowToMechatronics](https://howtomechatronics.com/tutorials/arduino/diy-arduino-robot-arm-with-smartphone-control/)\
  A complete tutorial on building and controlling a 5 DOF robotic arm using Arduino and servo motors. Useful for understanding servo control and robotic arm mechanics in custom setups.

- [Python Chess Library Documentation](https://python-chess.readthedocs.io/en/latest/)\
  Official documentation for the Python Chess library used for chess logic and engine interaction.

- [Stockfish Chess Engine](https://stockfishchess.org/)\
  Open-source chess engine used to analyze and play chess moves.

- [OpenCV](https://opencv.org/)\
  Computer vision library used for image processing and board recognition.

- [FreeSimpleGUI](https://github.com/spyoungtech/FreeSimpleGUI)\
  GUI framework used to build the user interface for the chess robot.

- [Arduino Official Website](https://www.arduino.cc/)\
  For learning more about Arduino boards, programming, and libraries.

- [Servo Motor Basics – SparkFun Guide](https://learn.sparkfun.com/tutorials/hobby-servo-tutorial/all)\
  Helpful for understanding how servo motors work and how to control them with Arduino.

- [Raspberry Pi Camera Module Documentation](https://www.raspberrypi.com/documentation/accessories/camera.html)\
  Official guide on using the Raspberry Pi Camera


