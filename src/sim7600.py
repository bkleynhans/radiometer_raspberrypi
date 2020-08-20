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

class Sim7600():
    # Constructor
    def __init__(self, modem, provider):

        self.defined = {
            'command': 'sudo qmicli -d ',                       # Note the spare AFTER the string
            'modem': modem,
            'wwanInterface': '',
            'setMode': ' --dms-set-operating-mode=',            # Note the space BEFORE the string
            'getMode': ' --dms-get-operating-mode',             # Note the space BEFORE the string
            'getSignalStrength': ' --nas-get-signal-strength',  # Note the space BEFORE the string
            'getHomeNetwork': ' --nas-get-home-network',        # Note the space BEFORE the string
            'getInterface': ' -w',                              # Note the space BEFORE the string
            'stop': ' stop',                                    # Note the space BEFORE the string
            'online': 'online',
            'offline': 'low-power',            
        }
        
        self.provider = provider
        
        self.status = None
        self.signal_strength = None
        self.home_network = None
        
        self.update_protocol()
                
    
    def radio_on(self):
        
        time.sleep(1)
        
        stream = os.popen(self.build_command('setMode', 'online'))        
        radio_status = stream.read()
        
        self.return_status(radio_status)
    
    
    def radio_off(self):
        
        time.sleep(1)
        
        stream = os.popen(self.build_command('setMode', 'offline'))
        radio_status = stream.read()
        
        self.return_status(radio_status)
        
        
    def get_signal_strength(self):
        
        time.sleep(1)
        
        stream = os.popen(self.build_command('getSignalStrength'))
        self.signal_strength = stream.read()
        
        
    def get_home_network(self):
        
        time.sleep(1)
        
        stream = os.popen(self.build_command('getHomeNetwork'))
        self.home_network = stream.read()


    def update_status(self):
        
        self.get_status()

    
    def get_status(self):

        time.sleep(1)
        
        # Get the operating mode -> Is the radio on or off
        stream = os.popen(self.build_command('getMode'))        
        operating_mode = stream.read()
        
        start_index = operating_mode.index('Mode: ') + len('Mode: ') + 1
        remainder = operating_mode[start_index:]
        
        self.status = remainder[:remainder.index('\n\t') -1]
        
        if self.status == "online":
            self.get_signal_strength()
            self.get_home_network()
            
    
    def get_wwan_interface(self):
        
        time.sleep(1)
        
        # Get the wwan interface name
        stream = os.popen(self.build_command('getInterface'))
        self.defined['wwanInterface'] = stream.read().rstrip('\n')
                
    
    def update_protocol(self):
        
        time.sleep(1)
                
        self.get_wwan_interface()
        
        # Bring the interface down
        command_string = 'sudo ip link set ' + self.defined['wwanInterface'] + ' down'
        stream = os.popen(command_string)
        print(stream.read())
        
        # Change protocol to RAW
        command_string = 'echo \'Y\' | sudo tee /sys/class/net/'
        command_string += self.defined['wwanInterface']
        command_string += '/qmi/raw_ip'
        
        stream = os.popen(command_string)
        print(stream.read())
        
        # Bring the interface up
        command_string = 'sudo ip link set ' + self.defined['wwanInterface'] + ' up'
        stream = os.popen(command_string)
        print(stream.read())
        
        
    def connect(self):
        
        time.sleep(1)
        
        command_string = "sudo qmicli -p -d "
        command_string += self.defined['modem']
        command_string += " --device-open-net='net-raw-ip|net-no-qos-header' --wds-start-network=\"apn='"        
        command_string += self.provider['apn']
        command_string += "'"
        
        if self.provider['name'] != 'hologram':            
            command_string += ",username='"
            command_string += self.provider['username']
            command_string += "',password='"
            command_string += self.provider['password']
            command_string += "'"
            
        command_string += ",ip-type=4\" --client-no-release-cid"
        
        stream = os.popen(command_string)
        print(stream.read())
        
        command_string = 'sudo udhcpc -i ' + self.defined['wwanInterface']
        
        stream = os.popen(command_string)
        print(stream.read())
        
        
    def disconnect(self):
        
        time.sleep(1)
        
        stream = os.popen(self.build_command('stop'))
        self.signal_strength = stream.read()
                
        
    def build_command(self, cmd, status=None):
        
        command = self.defined['command']
        command += self.defined['modem']
        command += self.defined[cmd]
        
        if status is not None:
            command += '\''
            command += self.defined[status]
            command += '\''
        
        return command
        
        
    def return_status(self, value):
        
        returnValue = False
        
        test_value = '[' + self.defined['modem'] + '] Operating mode set successfully\n'
        
        if value == test_value:
            returnValue =  True
            
        self.update_status()
            
        return returnValue
