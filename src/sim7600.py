###
#
#
#
# Program Description : 
# Created By          : Benjamin Kleynhans
# Creation Date       : August 19, 2020
# Authors             : Benjamin Kleynhans
#
# Last Modified By    : Benjamin Kleynhans
# Last Modified Date  : August 19, 2020
# Filename            : sim7600.py
#
###

# Imports
import os, subprocess
import time
import pdb

# Raspberry Pi Specific imports
import RPi.GPIO as GPIO

class Sim7600():
    # Constructor
    def __init__(self, radio, provider):
        
        self.defined = {
            'gsmProvider'           : provider,
            'gsmRadio'              : radio,
            'gsmRadioCommand'       : "sudo qmicli -d ",            # Note the space AFTER the string            
            'setRadioMode'          : " --dms-set-operating-mode=", # Note the space BEFORE the string
            'getRadioMode'          : " --dms-get-operating-mode",  # Note the space BEFORE the string
            'getSignalStrength'     : " --nas-get-signal-strength", # Note the space BEFORE the string
            'getHomeNetwork'        : " --nas-get-home-network",    # Note the space BEFORE the string
            'wwanInterface'         : '',
            'wwanInterfaceCommand'  : "sudo ip link set ",          # Note the space AFTER the string
            'getWwanInterface'      : " -w",                        # Note the space BEFORE the string
            'stop'                  : " stop",                      # Note the space BEFORE the string
            'online'                : "online",
            'lowPower'              : "low-power",
            'reset'                 : "reset",
            'offline'               : "offline"
        }
        
        self.get_wwan_interface()
        
        
    def connect(self):        
        
        print("connect")
        
        self.turn_gsm_radio_on()        
        self.update_wwan_protocol()
        self.connect_wwan_network()        
        
        
    def disconnect(self):
        
        print("disconnect")
        
        self.turn_gsm_radio_off()
        
        
    def turn_gsm_radio_on(self):
        
        print("turn_gsm_radio_on")

        # If the sim7600 module is still online, we need to place it offline before continuing
        if self.get_gsm_radio_status() == 'online':
            print("GSM Radio Status : Online        --> Resetting...")
            self.reset_gsm_radio()
            
        time.sleep(30)

        # If the sim7600 module is in offline mode, it needs to be reset before it can be
        # made online
        if self.get_gsm_radio_status() == 'offline':
            print("GSM Radio Status : Offline       --> Resetting...")
            self.reset_gsm_radio()

        time.sleep(30)

        # Turn the GSM radio on        
        stream = os.popen(self.build_command('setRadioMode', 'online'))        
        radio_status = stream.read()

        if self.return_status(radio_status):
            print("GSM Radio Status : Online")
        
    
    def update_wwan_protocol(self):
        
        print("update_wwan_protocol")
        
        time.sleep(10)
        
        # Bring the interface down
        command_string = 'sudo ip link set ' + self.defined['wwanInterface'] + ' down'
        
        print(command_string)
        os.popen(command_string)        

        time.sleep(5)

        # Change protocol to RAW
        filepath = os.path.join('/sys/class/net', self.defined['wwanInterface'], 'qmi/raw_ip')
        command_string = 'sudo bash -c \'echo "Y" >> {}\''.format(filepath)
        
        os.popen(command_string)
        
        time.sleep(5)
    
        # Bring the interface up
        command_string = 'sudo ip link set ' + self.defined['wwanInterface'] + ' up'
        
        print(command_string)
        os.popen(command_string)
        
    
    def connect_wwan_network(self):
        
        print("connect_wwan_network")

        command_string = "sudo qmicli -p -d "
        command_string += self.defined['gsmRadio']
        command_string += " --device-open-net='net-raw-ip|net-no-qos-header' --wds-start-network=\"apn='"        
        command_string += self.defined['gsmProvider']['apn']
        command_string += "'"

        if self.defined['gsmProvider']['name'] != 'hologram':
            command_string += ",username='"
            command_string += self.defined['gsmProvider']['username']
            command_string += "',password='"
            command_string += self.defined['gsmProvider']['password']
            command_string += "'"

        command_string += ",ip-type=4\" --client-no-release-cid"

        stream = os.popen(command_string)
        print(stream.read())

        command_string = 'sudo udhcpc -i ' + self.defined['wwanInterface']

        stream = os.popen(command_string)
        temp_data = stream.read()
        
        temp_data += self.get_ip_address()
        
        return temp_data


    def get_ip_address(self):
        
        print("get_ip_address")
        
        command_string = "sudo udhcpc -i " + self.defined['wwanInterface']        
        stream = os.popen(command_string)
        
        return stream.read()
        
    
    def reset_gsm_radio(self):
        
        print("reset_gsm_radio")

        time.sleep(10)

        stream = os.popen(self.build_command('setRadioMode', 'reset'))        
        radio_status = stream.read()
        
        if self.return_status(radio_status):
            print("GSM Radio Status : low-power")
        
    
    def turn_gsm_radio_off(self):
        
        print("turn_gsm_radio_off")

        stream = os.popen(self.build_command('setRadioMode', 'offline'))
        radio_status = stream.read()

        self.return_status(radio_status)
        
        
    def get_gsm_radio_status(self):
        
        print("get_gsm_radio_status")

        # Get the operating mode -> Is the GSM radio on or off
        stream = os.popen(self.build_command('getRadioMode'))
        operating_mode = stream.read()

        start_index = operating_mode.index('Mode: ') + len('Mode: ') + 1
        remainder = operating_mode[start_index:]

        return remainder[:remainder.index('\n\t') -1]               # returns 'online', 'offline', or 'low-power'
    

    def get_gsm_signal_strength(self):
        
        print("get_gsm_signal_strength")

        stream = os.popen(self.build_command('getSignalStrength'))
        return stream.read()


    def get_gsm_home_network(self):
        
        print("get_gsm_home_network")

        stream = os.popen(self.build_command('getHomeNetwork'))
        return stream.read()


    def get_wwan_interface(self):
        
        print("get_wwan_interface")

        # Get the wwan interface name
        stream = os.popen(self.build_command('getWwanInterface'))        
        self.defined['wwanInterface'] =  stream.read().rstrip('\n')
    
    
    def build_command(self, cmd, status=None):
        
        command = self.defined['gsmRadioCommand']
        command += self.defined['gsmRadio']
        command += self.defined[cmd]
    
        if status is not None:
            command += "'"
            command += self.defined[status]
            command += "'"

        print("build_command : {}".format(command))

        return command


    def return_status(self, value):

        returnValue = False

        test_value = '[' + self.defined['gsmRadio'] + '] Operating mode set successfully\n'

        if value == test_value:
            returnValue =  True

        return returnValue
