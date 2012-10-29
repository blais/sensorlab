#!/usr/bin/env 

DATAROOT=$(HOME)/SensorLab

all:						\
	Temperature.csv Temperature.png		\
	Humidity.csv Humidity.png		\
	Mic.csv Mic.png				\
	Motion.csv Motion.png			\
	PIR.csv PIR.png

Temperature.csv Temperature.png:
	python sensorlab.py $(DATAROOT)/Temperature $(DATAROOT)/output/Temperature

Humidity.csv Humidity.png:
	python sensorlab.py $(DATAROOT)/Humidity $(DATAROOT)/output/Humidity

Mic.csv Mic.png:
	python sensorlab.py $(DATAROOT)/Mic $(DATAROOT)/output/Mic

Motion.csv Motion.png:
	python sensorlab.py $(DATAROOT)/Motion $(DATAROOT)/output/Motion

PIR.csv PIR.png:
	python sensorlab.py $(DATAROOT)/PIR $(DATAROOT)/output/PIR
