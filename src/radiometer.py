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

# System imports
from datetime import datetime, timezone

import os, sys
import json
import time
import pdb
import subprocess

import piplates.DAQC2plate as DAQC2

# Project imports
from src.sim7600 import Sim7600
from src.filemanager import Filemanager

class Radiometer:

    def __init__(self, args):

        self.args = args
        
        # Is this the first time the script is running after power cycle
        self.initial_startup = True
        
        # Should data be uploaded
        self.upload_data = False
        
        # Save the current time
        self.current_time = time.time()
        self.previous_time = self.current_time
        
        # Save today's date to check for 24-hour intervals
        self.today = datetime.now(timezone.utc).strftime('%Y%m%d')
        
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
                        
        while True:
            self.program_loop()
        
    
    def program_loop(self):
        
        # Check if this is the initial boot of the device, and set some values
        if self.initial_startup:
            self.startup_procedure()
        
        if datetime.now(timezone.utc).strftime('%Y%m%d') != self.today:
            self.new_day_procedure()
            
        self.current_time = time.time()
        
        elapsed_time = self.current_time - self.previous_time
        
        if elapsed_time >= 1:
            self.sample_data()
            self.previous_time = self.current_time
        
    
    def startup_procedure(self):
        
        print("     --- Running startup configuration ---\n", end = '')
        
        # If the radio is off        
        self.sim7600.connect()
        
        # If we need to upload a data file, upload it
        if self.upload_data:
            self.upload_to_server()
            self.upload_data = False
            
        # Update the current day from the internet
        self.set_clock()
        
        # Set the filename for the new data file
        self.build_filename()
        
        # Write the headings to the new data file
        self.build_heading()
        
        self.initial_startup = False
        
        # Disconnect from internet and turn off modem
        self.sim7600.disconnect()


    def new_day_procedure(self):
        
        print("     --- Day has changed, updating configuration and creating new file ---\n", end = '')
        
        # Update the current Day
        self.today = datetime.now(timezone.utc).strftime('%Y%m%d')
        
        # Upload data files to online storage
        self.upload_data = True
        
        # Set initial startup to ture, which will force a re-sync of the clock and create a new
        # file for the new day
        self.initial_startup = True
    
    
    def sample_data(self):
        
        data_string = ""
                
        for i in range(8):
            data_string += "{:.5f},".format(DAQC2.getADC(0,i))
        
        data_string += "{},".format(datetime.now(timezone.utc).strftime('%Y'))
        data_string += "{},".format(datetime.now(timezone.utc).strftime('%m'))
        data_string += "{},".format(datetime.now(timezone.utc).strftime('%d'))
        data_string += "{},".format(datetime.now(timezone.utc).strftime('%H'))
        data_string += "{},".format(datetime.now(timezone.utc).strftime('%M'))
        data_string += "{}\n".format(datetime.now(timezone.utc).strftime('%S'))
        
        print(data_string, end = '')
        
        self.filemanager.save_to_file(
                            self.args['preferences']['toUploadPath'], 
                            self.args['filename'], 
                            data_string
                        )
    
    def upload_to_server(self):
        
        self.filemanager.connect_sftp()
        
        files_to_upload = self.filemanager.get_local_contents(self.args['preferences']['sourcePath'])
        
        self.filemanager.build_structure(self.args['preferences']['siteName'], self.args['filename'])
        
        for source_file in files_to_upload:            
            full_source_path = os.path.join(
                                    self.args['preferences']['sourcePath'],
                                    source_file
                                )
                                
            full_destination_path = os.path.join(
                                    self.args['preferences']['protocol']['ssh']['remoteDestinationPath'],
                                    self.args['preferences']['siteName'],
                                    source_file[:4],
                                    source_file[4:6],
                                    source_file
                                )
            print("     --- Uploading DATA to server ---\n", end = '')
            
            try:
                self.filemanager.upload_to_server(full_source_path, full_destination_path)
                
            except:                
                e = sys.exc_info()[0]
                
                print("\n   !!! An Exception Occurred During Remote Transfer !!!")
                print("{}".format(e))
            
            print("     --- Moving old file ---\n", end = '')
                
            try:
                self.filemanager.move_to_uploaded(full_source_path, self.args['preferences']['localDestinationPath'])
            except:                
                e = sys.exc_info()[0]
                
                print("\n   !!! An Exception Occurred During Local File Move !!!")
                print("{}".format(e))
    
    
    def set_clock(self):
        
        stream = os.popen('timedatectl')
        print(stream.read())
        
        datetime_now = datetime.now(timezone.utc)
        
        self.args['date'] = {
            'today_local' : datetime.now(),
            'today_utc' : datetime.now(timezone.utc)
        }
        
        print("Current Date : ", self.args['date']['today_utc'], end = '')
        
        
    def build_filename(self):
        
        print("    --- Building Filename ---\n", end = '')
        
        # Set the new filename
        self.args['filename'] = str(datetime.now(timezone.utc).strftime('%Y'))
        self.args['filename'] += str(datetime.now(timezone.utc).strftime('%m'))
        self.args['filename'] += str(datetime.now(timezone.utc).strftime('%d'))
        self.args['filename'] += ".csv"
        
    
    def build_heading(self):
        
        print("    --- Building Heading ---", end = '')
        
        self.write_title_string()
        self.write_heading_string()
        
        
    def write_title_string(self):
        
        # Clean the current title string
        self.args['titleString'] = None
        
        # Create the new title string
        self.args['titleString'] = "Site Name : {}\n".format(self.args['preferences']['siteName'])
        
        print(self.args['titleString'], end = '')
        
        # Write the title to the file
        self.filemanager.save_to_file(
            self.args['preferences']['toUploadPath'], 
            self.args['filename'], 
            self.args['titleString']
        )
        
    
    def write_heading_string(self):
        
        print(self.args['preferences']['headingString'], end = '')
        
        # Write the title to the file
        self.filemanager.save_to_file(
            self.args['preferences']['toUploadPath'], 
            self.args['filename'],
            self.args['preferences']['headingString']
        )


# Main entry to the GUI program
def main(args):

    Radiometer(args)
