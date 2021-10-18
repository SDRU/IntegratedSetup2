# -*- coding: utf-8 -*-
"""
Created on Mon Oct 18 15:43:14 2021

@author: Sandora
"""

######## USER PARAMETERS


# CAMERA SETTINGS
thresholdT = 30
# boundary = [row_low, row_high, col_low, col_high]
boundary = [0,400,0,400]

from MyFunctions import *






try:
    
    Camera, Shutter = [None, None]    
    
    # Water = IrrigationObject()
    # Water.set_setpoint(water_jet_setpoint_high)
    
    
  
    Shutter = ShutterObject()
    
    Camera = CameraObject(thresholdT, boundary)
    Camera.run(Shutter) 
    
   

except DeviceNotConnectedError as ex:
    print('Error: %s' % ex)
    
    for var in [Camera, Shutter]:
        if var != None:
            var.close()    
    
except KeyboardInterrupt:
    print('Program ended')
    
    Shutter.close()          

    
except:
    print('Random error, check your code!')
    
    for var in [Camera, Shutter]:
        if var != None:
            var.close() 