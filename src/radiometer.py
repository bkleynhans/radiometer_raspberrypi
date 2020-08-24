###
#
#
#
# Program Description :
# Created By          : Benjamin Kleynhans
# Creation Date       : January 25, 2020
# Authors             : Benjamin Kleynhans
#
# Last Modified By    : Benjamin Kleynhans
# Last Modified Date  : August 20, 2020
# Filename            : radiometer.py
#
###

# System immports
from datetime import datetime, timezone

import json
import os
import pdb
import time

# Project imports
from src.sim7600 import Sim7600

class Radiometer:

    def __init__(self, args):

        self.args = args
        
        # Is this the first time the script is running after power cycle
        self.initial_startup = True
        
        # Has the clock been set since startup
        self.clock_set = False
        
        # Should data be uploaded
        self.upload_data = False
        
        # Create a dictionary that will contain all the preferences loaded from the config file        
        self.args['preferences'] = {}

        # Build the path to the configuration file
        cfg_file = os.path.join(args['project_root'], 'etc', 'radiometer.json')
        
        # Read the contents of the file into the global preferences file
        self.load_file(cfg_file)
        
        # Create instances of required class objects
        self.sim7600 = Sim7600(
                            self.args['preferences']['radio'],
                            self.args['preferences']['provider']
                        )
        
        # ~ while True:
            # ~ self.program_loop()
        self.program_loop()
        
    
    def program_loop(self):
        
        # Check if this is the initial boot of the device, and set some values
        if self.initial_startup:
            self.startup_procedure()
        
    
    def startup_procedure(self):
        
        # If the radio is off        
        self.sim7600.connect()
        
        # If we need to upload a data file, upload it
        if self.upload_data:
            pass
            
        # Update the current day from the internet
        self.set_clock()
        
        # Set the filename for the new data file
        
        # Write the headings to the new data file
        
        self.initial_startup = False
        
        # Disconnect from internet and turn off modem
        self.sim7600.disconnect()
    
    
    def set_clock(self):
        
        stream = os.popen('timedatectl')
        print(stream.read())
        
        datetime_now = datetime.now(timezone.utc)
        
        self.args['date'] = {
            'today_local' : datetime.now(),
            'today_utc' : datetime.now(timezone.utc)
        }
        
        print("Current Date : ", self.args['date']['today_utc'])
        
    
    def load_file(self, cfg_file):
        
        try:
            with open(cfg_file) as json_file:
                self.args['preferences'] = json.load(json_file)
                self.args['preferences']['status'] = "success"
        except IOError: 
            print("The preferences file, radiometer.cfg, could not be found.")
            self.args['cfg']['status'] = "failed"
        
    
    def save_to_file(self, path, filename, data_string):
        
        save_location = os.path.join(path, filename)

        filehandle = open(save_location, 'a+')
        filehandle.writelines(data_string)
        filehandle.close()


# Main entry to the GUI program
def main(args):

    Radiometer(args)
