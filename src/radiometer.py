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
# Last Modified Date  : September 9, 2020
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
from src.filemanager import Filemanager
from src.weather_sensors import WeatherSensors

DEGREE_SIGN = u'\N{DEGREE SIGN}'

class Radiometer:

    def __init__(self, sim7600, filemanager, args):
        
        self.sim7600 = sim7600
        self.filemanager = filemanager
        self.args = args
        
        # Is this the first time the script is running after power cycle
        self.initial_startup = True
        
        # There will be a cron.log file which needs to be deleted IF the cron ran successfully
        self.delete_cron_log = True
        
        # Should data be uploaded
        self.upload_data = False 

        # Should we get a GPS postion
        self.get_gps_position = True
        
        # Save the current time
        self.current_time = time.time()
        self.previous_time = self.current_time
        
        # Save today's date to check for 24-hour intervals
        self.today = datetime.now(timezone.utc).strftime('%Y%m%d')
        
        # Turn SIM7600 module on
        self.sim7600.power_on()
        
        # Get GPS Coordinates
        if self.get_gps_position:
            self.args['coordinates'] = self.sim7600.get_position()
        
        # Add variables for wind and rain meter
        self.args['anemometer'] = 0
        self.args['rainGauge'] = 0
        
        # Create an instance of the WeatherSensors object
        # This is a threaded object that measures wind speed and rain
        self.weather_sensors = WeatherSensors(self.args)
        
        # Turn off Pi-Plates status LED on each plate
        for i in range(0, 2):
            DAQC2.setLED(i,'off')
            
        # Counter to send initial upload for connectivity test
        self.test_counter = 0
        
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
            
        # The wind and rain sensors work on running averages of ticks per second,
        # as such they need to be read continuously
        self.weather_sensors.read_anemometer()
        self.weather_sensors.read_rain_gauge()
        
        self.current_time = time.time()
        
        elapsed_time = self.current_time - self.previous_time
            
        # Check if 1 second has passed, then take another set of samples
        if elapsed_time >= 1 and not self.upload_data:
            self.sample_data()
            self.test_counter += 1
        elif elapsed_time >= 1 and self.upload_data:
            self.previous_time = self.current_time
        
        # After collecting 10 samples, upload a test file to the server
        if self.test_counter == 10:
            self.upload_sample_test()


    # The startup procedure runs on system boot, and every time the date changes
    def startup_procedure(self):
        
        print("\n     --- Running startup configuration ---\n")
        
        # Turn the sim7600 module on if it is offline
        if self.sim7600.power_status == "offline":
            self.sim7600.power_on()
            
        # Connect to the internet
        self.sim7600.connect()

        # Only try to upload data if the device successfully connected to the internet
        if self.sim7600.connected:
            # If we need to upload a data file, upload it
            if self.upload_data:
                self.upload_to_server()
                self.upload_data = False
                
            # Update the current day from the internet
            self.set_clock()
        
        # If the device does not connect to internet, we need to disable the upload
        # sequence or the device will go into a loop by continually trying to connect
        else:
            self.upload_data = False
        
        # Set the filename for the new data file
        self.build_filename()

        # Test if a sample file for the specific date already exists
        data_files = self.filemanager.get_local_contents(self.args['preferences']['savePath'])
        create_headings = True
        
        for data_file in data_files:
            if data_file == self.args['filename']:
                create_headings = False
        
        # If there is no file for the specified date, create a new file and add headings
        if create_headings:
            # Write the headings to the new data file
            self.build_heading()
        
        self.initial_startup = False
        
        if self.sim7600.connected:
            # Disconnect from internet
            self.sim7600.disconnect()
        
        # Power off Sim7600
        self.sim7600.power_off()
        
        # Move stale files to toUpload directory
        self.check_stale_files()
        
        # Delete cron log after successful startup
        if self.delete_cron_log:
            self.delete_cron_log = False
            self.filemanager.delete_file("/home/pi/cron.log")

    
    # Upload the sample file to allow testing of data upload from remote location
    # while still on site.
    def upload_sample_test(self):
        
        self.upload_data = True
        self.initial_startup = True
        
        print("Copying {} to {} directory".format(
                os.path.join(self.args['preferences']['savePath'],self.args['filename']),
                os.path.join(self.args['preferences']['toUploadPath'], "sample_test.csv")
            )
        )
        
        # Create a copy of the current day file in the 'toUpload' directory
        self.filemanager.copy_file(
                os.path.join(self.args['preferences']['savePath'], self.args['filename']),
                os.path.join(self.args['preferences']['toUploadPath'], "sample_test.csv")
            )
    
    
    # Check if there are any files in the storage root directory that have become "stale"
    # (they are from previous days) and move them to the "toUpload" directory
    def check_stale_files(self):
        
        stale_files = self.filemanager.get_local_contents('/mnt/storage')
        
        for s_file in stale_files:
            if s_file[6:8] != "{}".format(datetime.now(timezone.utc).strftime('%d')):
                print("Moving {} to 'toUpload' directory".format(os.path.join(self.args['preferences']['savePath'], s_file)))

                self.filemanager.move_file(
                    os.path.join(self.args['preferences']['savePath'], s_file), 
                    self.args['preferences']['toUploadPath']
                )


    # The new day procedure runs every time the date changes
    def new_day_procedure(self):
        
        print("\n     --- Day has changed, updating configuration and creating new file ---\n")
        
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
        
        heading_indices = self.args['preferences']['headingString'].split(",")
        data_string = ""
                
        for idx in heading_indices:
            if idx[:2] == "ch":
                
                # Read the normal input pins
                if self.args['preferences']['headerIndices'][idx] == "Anemometer(km/h)": # 1 tick per second = 2.4km/h
                    data_string += "{:.1f},".format(
                        self.args['anemometer']
                    )
                elif self.args['preferences']['headerIndices'][idx] == "RainGauge(mm)": # 1 tick = 0.2794mm rain
                    data_string += "{:.4f},".format(
                        self.args['rainGauge']
                    )
                # Relative humidity is calculated using the formula:
                # RH = 0.0375 * Vout - 37.7
                # Vout needs to be in mV and RH in %
                elif self.args['preferences']['headerIndices'][idx] == "RelativeHumidity(%)": 
                    Vout = DAQC2.getADC(
                            int(idx[2]),
                            int(idx[3])
                        ) * 1000 # We have to convert voltage to mV as it is read in V
                        
                    RH = 0.0375 * Vout - 37.7
                    
                    data_string += "{:.4f},".format(RH)
                    
                elif self.args['preferences']['headerIndices'][idx] == "RainGauge(mm)": # 1 tick = 0.2794mm rain
                    data_string += "{:.4f},".format(
                        self.args['rainGauge']
                    )
                else:
                    data_string += "{:.5f},".format(
                        DAQC2.getADC(
                            int(idx[2]),
                            int(idx[3])
                        )
                    )
        
        data_string += "{},".format(datetime.now(timezone.utc).strftime('%Y'))
        data_string += "{},".format(datetime.now(timezone.utc).strftime('%m'))
        data_string += "{},".format(datetime.now(timezone.utc).strftime('%d'))
        data_string += "{},".format(datetime.now(timezone.utc).strftime('%H'))
        data_string += "{},".format(datetime.now(timezone.utc).strftime('%M'))
        data_string += "{}\n".format(datetime.now(timezone.utc).strftime('%S'))
        
        print(data_string, end = '')
        
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
            print("\n>> Zipping {}".format(csv_source_file))

            full_source_path = self.zip_file(
                                    self.args['preferences']['toUploadPath'],
                                    csv_source_file
                                )

            if csv_source_file == "sample_test.csv":
                full_destination_path = os.path.join(
                                            self.args['preferences']['protocol']['ssh']['remoteDestinationPath'],
                                            self.args['preferences']['siteName'],
                                            "sample_test.zip"
                                        )
                
                print("\n     --- Uploading SAMPLE_TEST.ZIP to server ---\n")

            else:
                full_destination_path = os.path.join(
                                            self.args['preferences']['protocol']['ssh']['remoteDestinationPath'],
                                            self.args['preferences']['siteName'],
                                            csv_source_file[:4],
                                            csv_source_file[4:6],
                                            full_source_path[full_source_path.rfind('/') + 1:]
                                        )

                print("\n     --- Uploading {} to server ---\n".format(full_source_path[full_source_path.rfind('/') + 1:].upper()))
            
            try:
                self.filemanager.upload_to_server(full_source_path, full_destination_path)
                print("{} uploaded successfully".format(csv_source_file))
                
            except:                
                e = sys.exc_info()[0]
                
                print("\n   !!! An Exception Occurred During Remote Transfer !!!")
                print("{}".format(e))
            
            print("\n     --- Moving old file ---\n")
                
            try:
                if csv_source_file != "sample_test.csv":
                    self.filemanager.move_file(full_source_path, self.args['preferences']['uploadedPath'])
                else:
                    self.filemanager.delete_file(os.path.join(
                            self.args['preferences']['toUploadPath'],
                            "sample_test.zip"
                        )
                    )
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
        
        print("\n\n    --- Building Filename --- \n")
        
        # Set the new filename
        self.args['filename'] = str(datetime.now(timezone.utc).strftime('%Y'))
        self.args['filename'] += str(datetime.now(timezone.utc).strftime('%m'))
        self.args['filename'] += str(datetime.now(timezone.utc).strftime('%d'))
        self.args['filename'] += ".csv"
        
    
    def build_heading(self):
        
        print("\n    --- Building Heading ---\n")
        
        self.write_title_string()
        
        if self.get_gps_position:
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
        
        print(coordinate_string, end = '')
        
        # Write the coordinates of the radiometer
        self.filemanager.save_to_file(
            self.args['preferences']['savePath'], 
            self.args['filename'], 
            coordinate_string
        )
        

    def write_heading_string(self):
        
        heading_indices = self.args['preferences']['headingString'].split(",")
        heading_string = ""
        
        for idx in heading_indices:
            if idx[:2] == "ch":
                heading_string += self.args['preferences']['headerIndices'][idx]
            else:
                heading_string += idx
                
            if idx != heading_indices[len(heading_indices) - 1]:
                heading_string += ","
            
        print(heading_string, end = '')
        
        # Write the title to the file
        self.filemanager.save_to_file(
            self.args['preferences']['savePath'], 
            self.args['filename'],
            heading_string
        )
        
        
    def __del__(self):
        
        # Power off Sim7600
        self.sim7600.power_off()


# Main entry to the Radiometer program
def main(args):
    
    # Create instance of filemanager class which does all file related actions
    filemanager = Filemanager(args)
    
    # Build the path to the configuration file
    cfg_file = os.path.join(args['project_root'], 'etc', 'radiometer.json')
    
    # Read the contents of the file into the global preferences file
    args['preferences'] = filemanager.load_file(cfg_file)
    
    # Create instances of base SIM7600X module
    sim7600 = Sim7600(args)

    try:
        Radiometer(sim7600, filemanager, args)
    except:
        # Power off Sim7600
        sim7600.power_off()
