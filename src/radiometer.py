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

# Imports
import json
import os
import pdb

from tools.load_file import Load_File

class Radiometer:

    def __init__(self, args):

        self.args = args
        
        # Create a dictionary that will contain all the preferences loaded from the config file        
        args['preferences'] = {}

        # Build the path to the configuration file
        source_file = os.path.join(args['project_root'], 'etc', 'radiometer.cfg')
        
        # Create an instance of a file loader/reader object
        loader = Load_File()
        
        # Read the contents of the file into the global preferences file
        self.args['preferences'] = loader.load(source_file)
        
        while True:
            self.program_loop()
        
    
    def program_loop(self):
        
        pass


# Main entry to the GUI program
def main(args):

    Radiometer(args)
