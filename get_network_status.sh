#!/bin/bash

# Set device online
sudo qmicli -d /dev/cdc-wdm0 --dms-set-operating-mode='online'

# Get current provider information
sudo qmicli -d /dev/cdc-wdm0 --nas-get-home-network

# Get the signal strength
sudo qmicli -d /dev/cdc-wdm0 --nas-get-signal-strength

# Set device offline
sudo qmicli -d /dev/cdc-wdm0 --dms-set-operating-mode='offline'
