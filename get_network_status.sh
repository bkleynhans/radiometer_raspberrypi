#!/bin/bash

# State changes can take a few moments to be executed, which
# is why they have sleep timers

# Reset the device to ensure it isn't in an unsupported state
sudo qmicli -d /dev/cdc-wdm0 --dms-set-operating-mode='reset'
sleep 20  # reset takes longer because it has to power cycle the radio array 

# Set device online
sudo qmicli -d /dev/cdc-wdm0 --dms-set-operating-mode='online'
sleep 10

# Get current provider information
sudo qmicli -d /dev/cdc-wdm0 --nas-get-home-network

# Get the signal strength
sudo qmicli -d /dev/cdc-wdm0 --nas-get-signal-strength

# Set device offline
sudo qmicli -d /dev/cdc-wdm0 --dms-set-operating-mode='offline'
sleep 10
