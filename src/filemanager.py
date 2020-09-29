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
import paramiko
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
        
    
    def connect_sftp(self):
        
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        connected = False
        
        for host in self.preferences['protocol']['ssh']['servers']:
            if not connected:
                try:
                    self.ssh_client.connect(
                        hostname=host,
                        username=self.preferences['protocol']['ssh']['username'],
                        password=self.preferences['protocol']['ssh']['password']
                    )
                    
                    connected = True
                except:
                    continue
                    
    
    def build_structure(self, site_name, filename):
        
        # Extract the year and month from the filename
        year = filename[:4]
        month = filename[4:6]
        
        # Construct the path to get a directory listing for existing sites
        path_to_sites = self.preferences['protocol']['ssh']['remoteDestinationPath']
        sites = self.get_remote_contents(path_to_sites)
        path_to_years = os.path.join(path_to_sites, site_name)
        
        # If the site name does not exist, create it
        if not site_name in sites:            
            stdin, stdout, stderr = self.ssh_client.exec_command("mkdir {}".format(path_to_years))
        
        # Construct the path to get a directory listing for existing years
        years = self.get_remote_contents(path_to_years)
        path_to_months = os.path.join(path_to_years, str(year))
        
        # If the year does not exist, create it
        if not year in years:
            stdin, stdout, stderr = self.ssh_client.exec_command("mkdir {}".format(path_to_months))
        
        # Construct the path to get a directory listing for existing months
        months = self.get_remote_contents(path_to_months)
        path_to_days = os.path.join(path_to_months, str(month))
        
        # If the month does not exist, create it
        if not month in months:            
            stdin, stdout, stderr = self.ssh_client.exec_command("mkdir {}".format(path_to_days))
            
                                
    def get_remote_contents(self, path):
        
        stdin, stdout, stderr = self.ssh_client.exec_command("ls {}".format(path))
        
        unformatted_entries = stdout.readlines()
        formatted_entries = []
        
        for entry in unformatted_entries:
            formatted_entries.append(entry.rstrip('\n'))
            
        return formatted_entries
        
        
    def get_local_contents(self, path):
        
        return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    
    
    def upload_to_server(self, full_source_path, full_destination_path):
        
        sftp_client = self.ssh_client.open_sftp()
        sftp_client.put(full_source_path, full_destination_path)
        sftp_client.close()


    def move_file(self, full_source_path, local_destination_path):
        
        command_string = "sudo mv "
        command_string += full_source_path
        command_string += " "
        command_string += local_destination_path
                
        os.popen(command_string)
    
    
    def copy_file(self, full_source_path, local_destination_path):
        
        command_string = "sudo cp "
        command_string += full_source_path
        command_string += " "
        command_string += local_destination_path
                
        os.popen(command_string)
    
    
    def delete_file(self, full_file_path):
        
        command_string = "sudo rm "
        command_string += full_file_path
        
        os.popen(command_string)
