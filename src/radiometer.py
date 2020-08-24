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

import os
import json
import time
import pdb
import subprocess

# Project imports
from src.sim7600 import Sim7600
from src.filemanager import Filemanager

class Radiometer:

    def __init__(self, args):

        self.args = args
        
        # Is this the first time the script is running after power cycle
        self.initial_startup = True
        
        # Has the clock been set since startup
        self.clock_set = False
        
        # Should data be uploaded
        self.upload_data = False
        
        # Create instance of filemanager class which does all file related actions
        self.filemanager = Filemanager(args)

        # Build the path to the configuration file
        cfg_file = os.path.join(args['project_root'], 'etc', 'radiometer.json')
        
        # Read the contents of the file into the global preferences file
        self.args['preferences'] = self.filemanager.load_file(cfg_file)
        
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
        self.build_filename()
        
        # Write the headings to the new data file
        self.build_heading()
        
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
        
        
    def build_filename(self):
        
        print("    --- Building Filename ---")
        
        # Clean the filename variable
        self.args['filename'] = None
        
        # Set the new filename
        self.args['filename'] = self.args['preferences']['siteName']
        self.args['filename'] += "_"
        self.args['filename'] += str(datetime.now(timezone.utc).strftime('%y'))
        self.args['filename'] += str(datetime.now(timezone.utc).strftime('%m'))
        self.args['filename'] += str(datetime.now(timezone.utc).strftime('%d'))
        
    
    def build_heading(self):
        
        print("    --- Building Heading ---")
        
        self.write_title_string()
        self.write_heading_string()
        
        
    def write_title_string(self):
        
        print("    --- Building Title String ---")
        
        # Clean the current title string
        self.args['titleString'] = None
        
        # Create the new title string
        self.args['titleString'] = "Site Name : {}\n".format(self.args['preferences']['siteName'])
        
        # Write the title to the file
        self.filemanager.save_to_file(
            self.args['preferences']['toUploadPath'], 
            self.args['filename'], 
            self.args['titleString']
        )
        
    
    def write_heading_string(self):
        
        print("    --- Building Heading String ---")
        
        # Clean the current title string
        self.args['headingString'] = None
        
        # Write the title to the file
        self.filemanager.save_to_file(
            self.args['preferences']['toUploadPath'], 
            self.args['filename'],
            self.args['preferences']['headingString']
        )


# Main entry to the GUI program
def main(args):

    Radiometer(args)
