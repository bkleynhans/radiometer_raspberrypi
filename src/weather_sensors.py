###
#
#
#
# Program Description :
# Created By          : Benjamin Kleynhans
# Creation Date       : September 24, 2020
# Authors             : Benjamin Kleynhans
#
# Last Modified By    : Benjamin Kleynhans
# Last Modified Date  : September 24, 2020
# Filename            : weather_sensors.py
#
###

# System imports
import sys, os, pdb
import threading, time
import piplates.DAQC2plate as DAQC2

class WeatherSensors:
    # Constructor
    def __init__(self, args, start=False):

        self.args = args
        
        self.initialize_variables()
        
        # Threading disable due to read limitation of PiPlates board,
        # (you can only read one plate at a time)
        # ~ self.sensor_thread = threading.Thread(target=self.read_sensors)
        
        # ~ if start:
            # ~ self.start()


    # Variable initialization was moved out of constructor to clean up code
    def initialize_variables(self):
        
        self.active = True
        
        self.gauges = {
            "anemometer": {
                "channel": "",
                "recordedTick": False,
                "previousTime": 0,
                "numberTicks": 0
            },
            "rainGauge": {
                "channel": "",
                "recordedTick": False,
                "previousTime": 0,
                "numberTicks": 0
            }
        }
        
        self.get_sensor_channels()
    
    
    # Get the Anemometer channel number from the json file
    def get_sensor_channels(self):
        
        heading_indices = self.args['preferences']['headingString'].split(",")
        
        # Find the index of the Anemometer
        for idx in heading_indices:
            if self.args['preferences']['headerIndices'][idx] == "Anemometer(km/h)":
                self.gauges['anemometer']['channel'] = idx
                break
        
        # Find the index of the Rain Gauge
        for idx in heading_indices:
            if self.args['preferences']['headerIndices'][idx] == "RainGauge(mm)":
                self.gauges['rainGauge']['channel'] = idx
                break
        
    
    def read_sensors(self):
        
        while self.active:
            self.read_anemometer()
            self.read_rain_gauge()
        
        
    # Start reading the Anemometer
    def read_rain_gauge(self):
        
        current_time = time.time()
        elapsed_time = current_time - self.gauges['rainGauge']['previousTime']
        
        if elapsed_time >= 1:
            # ~ print("Rain : {:.4f} mm".format(
                # ~ self.gauges['rainGauge']['numberTicks'] * self.args['preferences']['rainConstant']))
            self.args['rainGauge'] = (
                self.gauges['rainGauge']['numberTicks'] * self.args['preferences']['rainConstant'])
            self.gauges['rainGauge']['numberTicks'] = 0
            self.gauges['rainGauge']['previousTime'] = current_time
            
        temp_val = DAQC2.getADC(
                        int(self.gauges['rainGauge']['channel'][2]),
                        int(self.gauges['rainGauge']['channel'][3])
                    )
                    
        if temp_val > 4:
            if not self.gauges['rainGauge']['recordedTick']:
                self.gauges['rainGauge']['numberTicks'] += 1
                self.gauges['rainGauge']['recordedTick'] = True
        else:
            self.gauges['rainGauge']['recordedTick'] = False
            
            
    # Start reading the Anemometer
    def read_anemometer(self):
        
        current_time = time.time()
        elapsed_time = current_time - self.gauges['anemometer']['previousTime']
        
        if elapsed_time >= 1:
            # ~ print("Wind : {:.1f} km/h".format(
                # ~ self.gauges['anemometer']['numberTicks'] * self.args['preferences']['anemometerConstant']))
            self.args['anemometer'] = (
                self.gauges['anemometer']['numberTicks'] * self.args['preferences']['anemometerConstant'])
            self.gauges['anemometer']['numberTicks'] = 0
            self.gauges['anemometer']['previousTime'] = current_time
            
        temp_val = DAQC2.getADC(
                        int(self.gauges['anemometer']['channel'][2]),
                        int(self.gauges['anemometer']['channel'][3])
                    )
                    
        if temp_val > 4:
            if not self.gauges['anemometer']['recordedTick']:
                self.gauges['anemometer']['numberTicks'] += 1
                self.gauges['anemometer']['recordedTick'] = True
        else:
            self.gauges['anemometer']['recordedTick'] = False


    # Start monitoring the Anemometer
    def start(self):
        self.sensor_thread.start()
        
        
    # Stop monitoring the Anemometer
    def stop(self):
        self.active = False
        sys.stdout.flush()
