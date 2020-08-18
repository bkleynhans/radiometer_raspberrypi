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
# Filename            : save_file.py
#
###

# Imports
import json
import os
import pdb

class Save_File:

    def __init__(self, args, data_type, data_dictionary=None):
        
        self.data = data_dictionary

        self.build_path(data_type)
        self.save()


    def build_path(self, data_type):

        returnValue = None

        project_root = self.root.preferences['project_root']

        if (data_type == 'config'):
            self.data = self.root.preferences
            self.save_location = os.path.join(project_root, 'etc', 'radiometer.cfg')
        elif (data_type == 'user'):
            self.save_location = filedialog.askopenfilename(
                initialdir = os.path.join(project_root, 'user_settings'),
                title = "Select file",
                filetypes = (("jpeg files","*.jpg"),("all files","*.*"))
            )

        return returnValue


    def save(self):

        json_data = json.dumps(self.data, sort_keys=True, indent=4)

        filehandle = open(self.save_location, 'w')
        filehandle.writelines(json_data)
        filehandle.close()

