"""
Main program to read MPU 9250 orientation parameters and display 
them on the Waveshare Pico 1.14 inch Screen.
Modified to move the Joystic, MPU and LCD classes into separate files
"""
from machine import Pin,SPI
import PicoMPU
import PicoLCD
import PicoJoy
import time
import math

pitch = 0.0
roll  = 0.0
yaw   = 0.0

if __name__ == '__main__':

    # prepare to display on the oled screen
    oled = PicoLCD.PicoLCD()
    oled.fill(0xFFFF)
    oled.show()
    
    # now define joystick class for OLED hat buttons
    joy = PicoJoy.PicoJoy()
    
    print("\nSense HAT Test Program ...\n")
    print("Use Joystick to show Pressure and Temperature")
    print("Use the A button to calibrate the magnetic sensor")
    print("Use the B button to re measure the gyro offsets")
    print("Glen Langston, National Science Foundation, December 30, 2023")
    #initialize temporary variables
    PRESS_DATA = 0.0
    TEMP_DATA = 0.0
    u8Buf=[0,0,0]
    # these arrays hold the individual measurements
    # they are not used to compute Roll pitch and Yaw, however
    Gyro = [0,0,0]
    Accel = [0,0,0]
    Mag   = [0,0,0]
    # connect to sensors
    mpu9250 = PicoMPU.MPU9250()
    lps22hb = PicoMPU.LPS22HB()
    # setup Buttons

    while True:
        
        # deterime whether to calibrate the magnet.
        if joy.keyA():
            oled.fill_rect(208,12,20,20,oled.red)
            oled.show()

            print("Get ready to read magnetic field in one direction")
            mpu9250.magCalibI(verbose=True)
            print("Rotate 180 degrees around Z axis")
            print("Click the Joystick when ready for the next Step")
            joy.wait()
            mpu9250.magCalibII(verbose=True)
            print("Flip MPU and Click the Joystick when ready for the final Step")
            joy.wait()
            mpu9250.magCalibIII(verbose=True)
            mpu9250.magCalibrated = True 
        else :
            oled.fill_rect(208,12,20,20,oled.white)
            oled.rect(208,12,20,20,oled.red)
            
            
        if joy.keyB():
            oled.fill_rect(208,103,20,20,oled.red)
            # re-read the gyro offsets
            offsets = mpu9250.readGyroOffset(verbose=True)            
        else:
            oled.fill_rect(208,103,20,20,oled.white)
            oled.rect(208,103,20,20,oled.red)
        
        PRESS_DATA = lps22hb.read_pres()  
        TEMP_DATA = lps22hb.read_temp()
        keyPushed, keys = joy.joystick()
        if keyPushed:
            oled.fill_rect(12,12,20,20,oled.red)
            # a new pressure data is generated

            print('Pressure = %6.2f hPa , Temperature = %6.2f °C' % \
                (PRESS_DATA,TEMP_DATA), end='\r')
        else:
            oled.fill_rect(12,12,20,20,oled.white)
            oled.rect(12,12,20,20,oled.red)
         
        Accel = mpu9250.readAccel()
        Gyro = mpu9250.readGyro()
        Mag = mpu9250.readMagnet()
        lps22hb.LPS22HB_START_ONESHOT()
#        time.sleep(0.1)
        roll, pitch, yaw = mpu9250.readRollPitchYaw()
#     print("\r\n /-------------------------------------------------------------/ \r\n")
        if not keyPushed:   # if printing temperature and pressure
            print('RPY = %.2f %.2f %.2f   ' % (roll,pitch,yaw), end='\r')
#     print('\r\nAcceleration:  X = %d , Y = %d , Z = %d\r\n'%(Accel[0],Accel[1],Accel[2]))  
#     print('\r\nGyroscope:     X = %d , Y = %d , Z = %d\r\n'%(Gyro[0],Gyro[1],Gyro[2]))
#     print('\r\nMagnetic:      X = %d , Y = %d , Z = %d'%((Mag[0]),Mag[1],Mag[2]))
        oled.text("Waveshare (NSF)",65,7,0XFF00)
        oled.text("Pico-10DOF-IMU ",65,27,0x001F)
        oled.text("roll: ",25,47,0XFFE0)
        strRoll = "%6.1f" % roll
        oled.text(strRoll,130,47,0XFFE0)
        oled.text(" Deg",180,47,0XFFE0)
        oled.text("pitch: ",25,57,0X07FF)
        strPitch = "%6.1f" % pitch
        oled.text(strPitch,130,57,0X07FF)
        oled.text(" Deg",180,57,0X07FF)
        oled.text("yaw: ",25,67,0x07E0)
        strYaw = "%6.1f" % yaw
        oled.text(strYaw,130,67,0x07E0)
        oled.text(" Deg",180,67,0x07E0)
        oled.text("Pressure: ",25,77,0XBC40)
        strP = "%5.1f" % PRESS_DATA
        oled.text(strP,130,77,0XBC40)
        oled.text(" hPa",180,77,0XBC40)
        oled.text("Temperature: ",25,87,0X8430)
    # convert to Farenheit
        T = (TEMP_DATA * 9. / 5.) + 32
        strT = "%5.1f" % T
        oled.text(strT,130,87,0X8430)
        oled.text(" F",180,87,0X8430)
        oled.text("Mag  Cal.: ",25,97,0XFF00)
        if mpu9250.magCalibrated:
            oled.text("True",130,97,0XFF00)
        else:
            oled.text("False",130,97,0X00FF)
        oled.text("Gyro Cal.: ",25,107,0XFF00)
        if mpu9250.gyroCalibrated:
            oled.text("True",130,107,0XFF00)
        else:
            oled.text("False",130,107,0X00FF)

        oled.text
        oled.show()
        oled.fill(0xFFFF)                                                                    
