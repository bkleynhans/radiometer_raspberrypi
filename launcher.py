#!/usr/bin/env python3

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
# Filename            : launcher.py
#
###

# System Imports
import sys, os, inspect
import subprocess as sp
import pdb

# Module Imports
from src import radiometer

# Definitions
ERASE_LINE = '\x1b[2k'      # defines ASCII code to clear a Linux terminal
__PROJECT_ROOT = ''           # defines the root directory of the project for portability


# Calculate fully qualified path to location of program execution
def get_module_path():

    filename = inspect.getfile(inspect.currentframe())
    path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

    return path, filename


# Set environment variables to locate current execution path
def set_path_variables():

    path, filename = get_module_path()

    sys.path.append(path)

    op_sys = None
    delimeter = None

    # Automatically build the path
    for element in os.walk(path):
        if ('/' in element[0]):
            if (op_sys == None):
                op_sys = 'ux'
                delimeter = '/'


            ind = element[0].rindex('/')
            index_value = element[0][ind + 1]

            # If the directory does not start with a '_' or a '.' append it to the path
            if (index_value != '_') and (index_value != '.'):
                sys.path.append(element[0])

        elif ('\\' in element[0]):
            if (op_sys == None):
                op_sys = 'win'
                delimeter = '\\'

            ind = element[0].rindex('\\')
            index_value = element[0][ind + 1]

            # If the directory does not start with a '_' or a '.' append it to the path
            if (index_value != '_') and (index_value != '.'):
                sys.path.append(element[0])

    return op_sys, delimeter


def main(args):

    global __PROJECT_ROOT

    __PROJECT_ROOT = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

    op_sys, delimeter = set_path_variables()

    args = {
        'project_root': __PROJECT_ROOT,
        'os': op_sys,
        'delimeter': delimeter,
        'preferences': {}
    }

    radiometer.main(args)

    # sp.call('clear', shell = True)


if __name__ == '__main__':
    args = main(sys.argv[1:])
