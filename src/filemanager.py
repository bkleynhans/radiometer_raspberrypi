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
# Filename            : filemanager.py
#
###

# Imports
import os, subprocess
import json
import time
import pdb

class Filemanager():
    # Constructor
    def __init__(self, args):
        
        self.args = args
        
        self.preferences = {}
        self.preferences['status'] = None
        
        
    def load_file(self, cfg_file):
        
        try:
            with open(cfg_file) as json_file:
                self.preferences = json.load(json_file)
                self.preferences['status'] = "success"
        except IOError: 
            print("The preferences file, radiometer.cfg, could not be found.")
            self.preferences['status'] = "failed"
            
        return self.preferences
        
    
    def save_to_file(self, path, filename, data_string):
        
        save_location = os.path.join(path, filename)

        filehandle = open(save_location, 'a+')
        filehandle.writelines(data_string)
        filehandle.close()
        
    def upload_to_server(self, filename, protocol):
        
        pass
