# -*- coding: utf-8 -*-
#!/usr/bin/env python3
###
#
# Python Monochrometer Interface
#
# Program Description : GUI master for the Landsat Buoy Calibration program
# Created By          : Benjamin Kleynhans
# Creation Date       : February 22, 2019
# Authors             : Benjamin Kleynhans
#
# Last Modified By    : Benjamin Kleynhans
# Last Modified Date  : August 18, 2019
# Filename            : load_file.py
#
###

### Usage ###
# source_file = os.path.join(args['project_root'], 'etc', 'radiometer.cfg')
# loader = Load_File(self.root, master)
# my_data = loader.load(source_file)
###

# Imports
import json
import os
import pdb

class Load_File:

    def __init__(self):

        pass


    def load(self, cfg_file):

        self.data = {}

        try:
            with open(cfg_file) as json_file:
                self.data = json.load(json_file)
                self.data['status'] = "success"
        except IOError: 
            print("The preferences file, radiometer.cfg, could not be found.  A new file will be created from this session.")
            self.data['status'] = "failed"

        return self.data
