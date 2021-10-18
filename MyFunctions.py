# -*- coding: utf-8 -*-
"""
Created on Mon Oct 18 16:24:33 2021

@author: Sandora
"""
import sys
import pyvisa
import numpy as np
import time
import pandas as pd
import datetime
import serial
import struct
import os
import PySpin

from serial.tools.list_ports import comports
from email.header import UTF8
from ctypes import *
from array import array
import subprocess
from pylablib.devices import Thorlabs
    

    
        
class CameraObject:
    def __init__(self, thresholdT, boundary):
        self.thresholdT = thresholdT
        self.system = PySpin.System.GetInstance()
        self.boundary = boundary
        
        # Retrieve list of cameras from the system
        cam_list = self.system.GetCameras()
        num_cameras = cam_list.GetSize()    

        # Finish if there are no cameras
        if num_cameras == 0:
            # Clear camera list before releasing system
            cam_list.Clear()
            # Release system instance
            self.system.ReleaseInstance()
            print('Not enough cameras!')  
            
            self = None
            raise DeviceNotConnectedError('Camera')
        else:
            self.cam = cam_list[0]
            print('Camera initialized')    

        
            
    def run(self, Shutter):
        """
        This function acts as the body of the example; please see NodeMapInfo example
        for more in-depth comments on setting up cameras.
    
        :param cam: Camera to run on.
        :type cam: CameraPtr
        :return: True if successful, False otherwise.
        :rtype: bool
        """
        # shutter 1 means open, 0 closed
        shutter_status = 1 
        
        try:
            # Initialize camera  
            self.cam.Init()              
            # Acquire images             
            self.cam.BeginAcquisition()
            
            
            Shutter.unblock()
            
            while True:                
                
                image_result = self.cam.GetNextImage()                  
                
    
                if image_result.IsIncomplete():
                    print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
    
                else:
    
                    image_converted = image_result.Convert(PySpin.PixelFormat_Mono16, PySpin.HQ_LINEAR)                  
                    
                    T = self.convert_to_temperature(image_converted)
                    M = np.amax(T)
                    # print(M)
                    
                    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
                    filename = f"{now}.tiff"                    
                    image_converted.Save(filename)
                    
           
                    if M>self.thresholdT:
                        # print(M)
                        if shutter_status == 1:                            
                            Shutter.block()                            
                            shutter_status = 0
    
                    else:
                        if shutter_status == 0:
                            Shutter.unblock()
                            shutter_status = 1
                                
                    image_result.Release()   
    
            
        except KeyboardInterrupt as e:
            print('!!!!!!!! How dare you cancelling me !!!!!!!!!!!')
    
            self.cam.EndAcquisition()
            self.cam.DeInit()
            self.close()
            raise e

        
        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex) 



    def convert_to_temperature(self,image):
        
        try:        
            y=image.GetWidth()
            x=image.GetHeight()
            image=image.GetData()
            
            IR=np.reshape(image,[x,y]);
            IR = IR[self.boundary[0]:self.boundary[1],self.boundary[2]:self.boundary[3]]
            x = np.shape(IR)[0]
            y = np.shape(IR)[1]
            
        
            # Adding calibration coefficients from software
            # Coefficients for Counts to Radiance
            Cr_0 = -3.42255e-03
            Cr_1 = 5.01980e-07
            I = np.ones([x,y]) # must coincide with desired size in x or y
            r1 = Cr_0*I
            # Coefficients for Radiance to Temperature
            Ct_0 = -6.32251e+01
            Ct_1 = 3.52488e+04
            Ct_2 = -4.55977e+06
            Ct_3 = 5.02369e+08
            Ct_4 = -3.55013e+10
            Ct_5 = 1.42222e+12
            Ct_6 = -2.45221e+13
        
        
            r2 = Cr_1*IR
            R = r1+r2; # Radiance 
            T = Ct_0*np.ones([x,y]) + Ct_1*R + Ct_2*R**2 + Ct_3*R**3 + Ct_4*R**4 + Ct_5*R**5 + Ct_6*R**6
            return T
        
        except KeyboardInterrupt as e:
            raise e
            
            
    def close(self):  
        del self.cam 
        self.system.ReleaseInstance() 
        print('Camera closed')
        
        
  
class ShutterObject:
    def __init__(self):
   
        devices = Thorlabs.list_kinesis_devices()    
        
        if len(devices) == 0:
            raise DeviceNotConnectedError('Shutter')
            
        else:
            for device in devices:
                serial_nr = device[0]
                if serial_nr.startswith("6"):
                    self.shutter = Thorlabs.kinesis.KinesisDevice(serial_nr)
                    self.shutter.open() 
                    self.shutter.set_operating_mode(mode=1)
                    
                else:
                    raise DeviceNotConnectedError('Shutter')
 
        
    def block(self):
        self.shutter.shutter_close()
        
    def unblock(self):        
        self.shutter.shutter_open()
        
    def close(self):
        self.block()
        self.shutter.close()
       
 
    
class DeviceNotConnectedError(Exception):
    def __init__(self, device):
        self.device = device
        self.message = f"{self.device} not connected"
        super().__init__(self.message)

    pass            
        
