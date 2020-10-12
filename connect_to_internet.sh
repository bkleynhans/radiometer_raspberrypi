#!/bin/bash
###
#
# This script connects to the internet using the SIM7600 modem
#
# Program Description : 
# Created By          : Benjamin Kleynhans
# Creation Date       : October 12, 2020
# Authors             : Benjamin Kleynhans
#
# Last Modified By    : Benjamin Kleynhans
# Last Modified Date  : October 12, 2020
# Filename            : connect_to_internet.sh
#
###

# State changes can take a few moments to be executed, which
# is why they have sleep timers

# Reset the device to ensure it isn't in an unsupported state
sudo qmicli -d /dev/cdc-wdm0 --dms-set-operating-mode='reset'
sleep 60  # reset takes longer because it has to power cycle the radio array 

# Set device online
sudo qmicli -d /dev/cdc-wdm0 --dms-set-operating-mode='online'
sleep 5

# Bring the IP link down to update configuration
sudo ip link set wwan0 down
sleep 1

# Configure the device to use RAW IP
echo 'Y' | sudo tee /sys/class/net/wwan0/qmi/raw_ip

# Bring the IP link back up
sudo ip link set wwan0 up
sleep 1

# Initiate the connection
sudo qmicli -p -d /dev/cdc-wdm0 --device-open-net='net-raw-ip|net-no-qos-header' --wds-start-network="apn='hologram',ip-type=4" --client-no-release-cid
sleep 5

# Get DHCP address information
sudo udhcpc -i wwan0
sleep 60
