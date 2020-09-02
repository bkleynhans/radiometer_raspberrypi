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
import zipfile

import piplates.DAQC2plate as DAQC2

# Project imports
from src.sim7600 import Sim7600
# ~ from src.sim7600_gps import Sim7600_Gps
from src.filemanager import Filemanager

DEGREE_SIGN = u'\N{DEGREE SIGN}'

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
        
        # Create instances of base SIM7600X module
        self.sim7600 = Sim7600(self.args)
        
        # Turn SIM7600 module on
        self.sim7600.power_on()
        
        # Get GPS Coordinates
        self.args['coordinates'] = self.sim7600.get_position()
        
        # Run program loop
        while True:
            self.program_loop()
        
    
    # The program loop runs continuously until Ctrl+C is pressed in the terminal
    def program_loop(self):
        
        # Check if this is the initial boot of the device, and set some values
        if self.initial_startup:
            self.startup_procedure()
        
        # Check if the date has changed, and if it has, upload the file and create a new one
        if datetime.now(timezone.utc).strftime('%Y%m%d') != self.today:
            self.new_day_procedure()
            
        self.current_time = time.time()
        
        elapsed_time = self.current_time - self.previous_time
            
        # Check if 1 second has passed, then take another set of samples
        if elapsed_time >= 1 and not self.upload_data:
            self.sample_data()
        elif elapsed_time >= 1 and self.upload_data:
            self.previous_time = self.current_time


    # The startup procedure runs on system boot, and every time the date changes
    def startup_procedure(self):
        
        print("     --- Running startup configuration ---\n", end = '')
        
        # Turn the sim7600 module on if it is offline
        if self.sim7600.power_status == "offline":
            self.sim7600.power_on()
            
        # Connect to the internet
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
        
        # Disconnect from internet
        self.sim7600.disconnect()
        
        # Power off Sim7600
        self.sim7600.power_off()


    # The new day procedure runs every time the date changes
    def new_day_procedure(self):
        
        print("     --- Day has changed, updating configuration and creating new file ---\n", end = '')
        
        # Update the current Day
        self.today = datetime.now(timezone.utc).strftime('%Y%m%d')
        
        # Move yesterdays file to toUpload directory
        full_source_path = os.path.join(self.args['preferences']['savePath'], self.args['filename'])
        self.filemanager.move_file(full_source_path, self.args['preferences']['toUploadPath'])
        
        # Give the system time to move the file
        time.sleep(1)
        
        # Upload data files to online storage
        self.upload_data = True
        
        # Set initial startup to ture, which will force a re-sync of the clock and create a new
        # file for the new day
        self.initial_startup = True
    
    
    def sample_data(self):
        
        data_string = ""
                
        for i in range(8):
            data_string += "{:.5f},".format(DAQC2.getADC(0,i))
            
            if i == 1:
                data_string += "I1,"
                
            if i == 3:
                data_string += "I2,"
                
            if i == 7:
                data_string += "I3,"
        
        data_string += "{},".format(datetime.now(timezone.utc).strftime('%Y'))
        data_string += "{},".format(datetime.now(timezone.utc).strftime('%m'))
        data_string += "{},".format(datetime.now(timezone.utc).strftime('%d'))
        data_string += "{},".format(datetime.now(timezone.utc).strftime('%H'))
        data_string += "{},".format(datetime.now(timezone.utc).strftime('%M'))
        data_string += "{}\n".format(datetime.now(timezone.utc).strftime('%S'))
        
        # ~ print(data_string, end = '')
        
        self.filemanager.save_to_file(
                            self.args['preferences']['savePath'], 
                            self.args['filename'], 
                            data_string
                        )

        self.previous_time = self.current_time


    def upload_to_server(self):
        
        self.filemanager.connect_sftp()
        
        files_to_upload = self.filemanager.get_local_contents(self.args['preferences']['toUploadPath'])

        self.filemanager.build_structure(self.args['preferences']['siteName'], self.args['filename'])
        
        for csv_source_file in files_to_upload:
            full_source_path = self.zip_file(
                                    self.args['preferences']['toUploadPath'],
                                    csv_source_file
                                )

            full_destination_path = os.path.join(
                                    self.args['preferences']['protocol']['ssh']['remoteDestinationPath'],
                                    self.args['preferences']['siteName'],
                                    csv_source_file[:4],
                                    csv_source_file[4:6],
                                    full_source_path[full_source_path.rfind('/') + 1:]
                                )
                                
            print("     --- Uploading DATA to server ---\n", end = '')
            
            try:                
                self.filemanager.upload_to_server(full_source_path, full_destination_path)
                
            except:                
                e = sys.exc_info()[0]
                
                print("\n   !!! An Exception Occurred During Remote Transfer !!!")
                print("{}".format(e))
            
            print("     --- Moving old file ---")
                
            try:
                self.filemanager.move_file(full_source_path, self.args['preferences']['uploadedPath'])
            except:                
                e = sys.exc_info()[0]
                
                print("\n   !!! An Exception Occurred During Local File Move !!!")
                print("{}".format(e))


    def zip_file(self, csv_source_path, filename):
        
        filename_no_extension = filename[:filename.find('.')]
        zipped_filename = filename_no_extension + '.zip'
        
        full_zipped_path = os.path.join(csv_source_path, zipped_filename)
        
        zipped_file = zipfile.ZipFile(full_zipped_path, 'w')
        zipped_file.write(
            os.path.join(
                csv_source_path,
                filename
            ),
            compress_type = zipfile.ZIP_DEFLATED
        )
        zipped_file.close()
        
        self.filemanager.delete_file(os.path.join(csv_source_path, filename))
        
        return full_zipped_path


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
        
        print("    --- Building Filename --n")
        
        # Set the new filename
        self.args['filename'] = str(datetime.now(timezone.utc).strftime('%Y'))
        self.args['filename'] += str(datetime.now(timezone.utc).strftime('%m'))
        self.args['filename'] += str(datetime.now(timezone.utc).strftime('%d'))
        self.args['filename'] += ".csv"
        
    
    def build_heading(self):
        
        print("    --- Building Heading ---")
        
        self.write_title_string()
        self.write_coordinate_string()
        self.write_heading_string()
        
        
    def write_title_string(self):
        
        # Clean the current title string
        self.args['titleString'] = None
        
        # Create the new title string
        self.args['titleString'] = "Site Name : {}\n".format(self.args['preferences']['siteName'])
        
        print(self.args['titleString'], end = '')
        
        # Write the title to the file
        self.filemanager.save_to_file(
            self.args['preferences']['savePath'], 
            self.args['filename'], 
            self.args['titleString']
        )
        
        
    def write_coordinate_string(self):
        
        # Build the coordinate string_at
        coordinate_string = 'Latitude : {}{}'.format(self.args['coordinates']['latitude']['degrees'], DEGREE_SIGN)
        coordinate_string += '{}\''.format(self.args['coordinates']['latitude']['minutes'])
        coordinate_string += '{:.3f}"'.format(self.args['coordinates']['latitude']['seconds'])
        coordinate_string += ' {}'.format(self.args['coordinates']['latitude']['direction'])
        
        coordinate_string += '      '
        
        coordinate_string += 'Longitude : {}{}'.format(self.args['coordinates']['longitude']['degrees'], DEGREE_SIGN)
        coordinate_string += '{}\''.format(self.args['coordinates']['longitude']['minutes'])
        coordinate_string += '{:.3f}"'.format(self.args['coordinates']['longitude']['seconds'])
        coordinate_string += ' {}\n'.format(self.args['coordinates']['longitude']['direction'])
        
        # Write the coordinates of the radiometer
        self.filemanager.save_to_file(
            self.args['preferences']['savePath'], 
            self.args['filename'], 
            coordinate_string
        )
        

    def write_heading_string(self):
        
        print(self.args['preferences']['headingString'], end = '')
        
        # Write the title to the file
        self.filemanager.save_to_file(
            self.args['preferences']['savePath'], 
            self.args['filename'],
            self.args['preferences']['headingString']
        )
        
        
        def __del__(self):
            
            # Power off Sim7600
            self.sim7600.power_off()


# Main entry to the Radiometer program
def main(args):

    try:
        Radiometer(args)
    except:
        # Power off Sim7600
        self.sim7600.power_off()
