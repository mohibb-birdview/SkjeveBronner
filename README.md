# SkjeveBronner
Software to connect UAV to GCS for visualization of measured angles

## Wellhead
Modbus Slave simulator, to simulate the sensor during development.

## UAV
Module to run on the UAV onboard computer. Periodically pulls data from Modbus sensor, and sends to GCS

## GCS
Ground Control Station Module. Receives sensor data, with logging and visualization.

## Functions
Common funtions for all modules.
