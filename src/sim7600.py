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
import serial

class Sim7600():
    # Constructor
    def __init__(self, args): #radio, provider, power_key = 6):
        
        self.defined = {            
            'gsmProvider'           : args['preferences']['provider'],
            'gsmRadio'              : args['preferences']['sim7600']['radio'],
            'serial0'               : args['preferences']['sim7600']['serial0'],
            'powerKey'              : args['preferences']['sim7600']['powerKey'],
            'baudRate'              : args['preferences']['sim7600']['baudRate'],
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
        
        self.power_status = 'offline'
        
        self.serial0 = serial.Serial(self.defined['serial0'], self.defined['baudRate'])
        self.serial0.flushInput()
        
        
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

        temp_data = self.get_ip_address()
        temp_data += self.update_routing_table()        

        return temp_data


    def get_ip_address(self):
        
        print("get_ip_address")
        
        command_string = "sudo udhcpc -i " + self.defined['wwanInterface']        
        stream = os.popen(command_string)
        
        return stream.read()
        
    
    def update_routing_table(self):

        print("update_routing_table")

        command_string = "sudo ip a s " + self.defined['wwanInterface']
        stream = os.popen(command_string)

        temp_string = stream.read()

        command_string = "sudo ip r s"
        stream = os.popen(command_string)

        temp_string += stream.read()

        return temp_string
    

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
        
# PHYSICAL DEVICE MODULES
    def power_on(self):
        
        try:
            self._power_on()
        except:
            if self.serial0 != None:
                self.serial0.close()
                
            self.power_off()
            GPIO.cleanup()
            
            
    def power_off(self):
        
        try:
            self._power_off()
        except:
            if self.serial0 != None:
                self.serial0.close()
                
            self._power_off()
            GPIO.cleanup()
            
            
    def _power_on(self):
        print('Powering on SIM7600X')
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.defined['powerKey'], GPIO.OUT)
        time.sleep(0.1)
        GPIO.output(self.defined['powerKey'], GPIO.HIGH)
        time.sleep(2)
        GPIO.output(self.defined['powerKey'], GPIO.LOW)
        time.sleep(20)
        self.serial0.flushInput()
        
        self.power_status = "online"
        
        self.get_wwan_interface()
        print('SIM7600X is ready')
        
        
    def _power_off(self):
        print('Powering down SIM7600X')
        GPIO.output(self.defined['powerKey'], GPIO.HIGH)
        time.sleep(3)
        GPIO.output(self.defined['powerKey'], GPIO.LOW)
        time.sleep(18)
        self.power_status = "offline"
        print('SIM7600 has been powered off')
        
            
# GPS MODULES
    def get_position(self):
        
        try:
            return(self._get_position())
        except:
            if self.serial0 != None:
                self.serial0.close()
                
            self.power_off()
            GPIO.cleanup()
        
        
    def _get_position(self):
        receive_null = True
        answer = 0
        print('Starting GPS session...')
        receive_buffer = ''
        self._send_at_command('AT+CGPS=1,1', 'OK', 1)
        time.sleep(2)
        
        while receive_null:
            answer, receive_buffer = self._send_at_command('AT+CGPSINFO', '+CGPSINFO: ', 1)
            
            if answer == 1:
                answer = 0
                
                # ~ if ',,,,,,' in receive_buffer:
                    # ~ print('GPS is not ready')
                    # ~ receive_null = False
                    # ~ time.sleep(1)
            else:
                print('error %d' %answer)
                receive_buffer = ''
                self._send_at_command('AT+CGPS=0', 'OK', 1)
                return False
                
            time.sleep(1.5)
                        
            if '+CGPSINFO' in receive_buffer and ',,,,,,,,' not in receive_buffer:                
                gpgga_array = receive_buffer[receive_buffer.index(':') + 1:].split(',')
                
                self.coordinates = {
                    'latitude': {
                        'degrees': gpgga_array[0][:gpgga_array[0].find('.') - 2],
                        'minutes': gpgga_array[0][3:gpgga_array[0].find('.')],
                        'seconds': float(gpgga_array[0][gpgga_array[0].find('.'):]) * 60,
                        'direction': gpgga_array[1]
                    },
                    'longitude': {
                        'degrees': gpgga_array[2][:gpgga_array[2].find('.') - 2],
                        'minutes': gpgga_array[2][3:gpgga_array[2].find('.')],
                        'seconds': float(gpgga_array[2][gpgga_array[2].find('.'):]) * 60,
                        'direction': gpgga_array[3]
                    }
                }
        
                return self.coordinates
        
        
    def _send_at_command(self, command, return_value, timeout):
        receive_buffer = ''
        self.serial0.write((command+'\r\n').encode())
        time.sleep(timeout)
        
        if self.serial0.inWaiting():
            time.sleep(0.01)
            receive_buffer = self.serial0.read(self.serial0.inWaiting())
            
        if receive_buffer != '':
            if return_value not in receive_buffer.decode():
                print(command + ' ERROR')
                print(command + ' back:\t' + receive_buffer.decode())
            else:
                decoded_buffer = receive_buffer.decode()
                print(decoded_buffer)
                
                if return_value == '+CGPSINFO: ':
                    return 1, decoded_buffer
                else:
                    return 1
        else:
            print('GPS is not ready')
            return 0
        
# Destructor
    def __del__(self):
        if self.serial0 != None:
            self.serial0.close()
            GPIO.cleanup()
