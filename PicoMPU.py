"""
Class to read the Waveshare 9250 MPU orientation, velocities
and accelarations.  
Modified to separate phases of calibration, enabling
use of buttons to start and stop of the process.
Glen Langston, 2023 August 7
"""

from machine import I2C, Pin
import time
import math

## MPU9250 Default I2C slave address
SLAVE_ADDRESS        = 0x68
## AK8963 I2C slave address
AK8963_SLAVE_ADDRESS = 0x0C
## Device id
DEVICE_ID            = 0x71

''' MPU-9250 Register Addresses '''
## sample rate driver
SMPLRT_DIV     = 0x19
CONFIG         = 0x1A
GYRO_CONFIG    = 0x1B
ACCEL_CONFIG   = 0x1C
ACCEL_CONFIG_2 = 0x1D
LP_ACCEL_ODR   = 0x1E
WOM_THR        = 0x1F
FIFO_EN        = 0x23
I2C_MST_CTRL   = 0x24
I2C_MST_STATUS = 0x36
INT_PIN_CFG    = 0x37
INT_ENABLE     = 0x38
INT_STATUS     = 0x3A
ACCEL_OUT      = 0x3B
TEMP_OUT       = 0x41
GYRO_OUT       = 0x43

I2C_MST_DELAY_CTRL = 0x67
SIGNAL_PATH_RESET  = 0x68
MOT_DETECT_CTRL    = 0x69
USER_CTRL          = 0x6A
PWR_MGMT_1         = 0x6B
PWR_MGMT_2         = 0x6C
FIFO_R_W           = 0x74
WHO_AM_I           = 0x75

## Gyro Full Scale Select 250dps
GFS_250  = 0x00
## Gyro Full Scale Select 500dps
GFS_500  = 0x01
## Gyro Full Scale Select 1000dps
GFS_1000 = 0x02
## Gyro Full Scale Select 2000dps
GFS_2000 = 0x03
## Accel Full Scale Select 2G
AFS_2G   = 0x00
## Accel Full Scale Select 4G
AFS_4G   = 0x01
## Accel Full Scale Select 8G
AFS_8G   = 0x02
## Accel Full Scale Select 16G
AFS_16G  = 0x03

# AK8963 Register Addresses
AK8963_ST1        = 0x02
AK8963_MAGNET_OUT = 0x03
AK8963_CNTL1      = 0x0A
AK8963_CNTL2      = 0x0B
AK8963_ASAX       = 0x10

# CNTL1 Mode select
## Power down mode
AK8963_MODE_DOWN   = 0x00
## One shot data output
AK8963_MODE_ONE    = 0x01

## Continous data output 8Hz
AK8963_MODE_C8HZ   = 0x02
## Continous data output 100Hz
AK8963_MODE_C100HZ = 0x06

# Magneto Scale Select
## 14bit output
AK8963_BIT_14 = 0x00
## 16bit output
AK8963_BIT_16 = 0x01

bus = I2C(1,scl=Pin(7),sda=Pin(6),freq=400_000)

## MPU9250 I2C Controll class
class MPU9250:

    ## Constructor
    #  @param [in] address MPU-9250 I2C slave address default:0x68
    def __init__(self, address=SLAVE_ADDRESS):
        self.address = address
        # the configure command sets the sensitivity of the device.
        # the values below sets for high sensitivity, but smaller range
        self.configMPU9250(GFS_250, AFS_2G)
        self.configAK8963(AK8963_MODE_C8HZ, AK8963_BIT_16)
        self.gyroOffset = [0,0,0]
        self.magOffset = [0,0,0]
        # assume not calibrated
        self.isCalibrated = False
        self.magCalibrated = False
        self.gyroCalibrated = False
        # read the initiial gyroOffsets
        self.readGyroOffset()
        self.magTemp = [0,0,0,0,0,0,0,0,0]
        self.Ki = 1.0
        self.Kp = 4.50
        # keep track of the quaternion
        self.q0 = 1.0
        self.q1 = 0.0
        self.q2 = 0.0
        self.q3 = 0.0

    ## Search Device
    #  @param [in] self The object pointer.
    #  @retval true device connected
    #  @retval false device error
    def searchDevice(self):
        who_am_i = bus.readfrom_mem(int(self.address), int(WHO_AM_I),1)
        if(who_am_i == DEVICE_ID):
            return true
        else:
            return false

    ## Configure MPU-9250
    #  @param [in] self The object pointer.
    #  @param [in] gfs Gyro Full Scale Select(default:GFS_250[+250dps])
    #  @param [in] afs Accel Full Scale Select(default:AFS_2G[2g])
    def configMPU9250(self, gfs, afs):
        if gfs == GFS_250:
            self.gres = 250.0/32768.0
        elif gfs == GFS_500:
            self.gres = 500.0/32768.0
        elif gfs == GFS_1000:
            self.gres = 1000.0/32768.0
        else:  # gfs == GFS_2000
            self.gres = 2000.0/32768.0

        if afs == AFS_2G:
            self.ares = 2.0/32768.0
        elif afs == AFS_4G:
            self.ares = 4.0/32768.0
        elif afs == AFS_8G:
            self.ares = 8.0/32768.0
        else: # afs == AFS_16G:
            self.ares = 16.0/32768.0

        # sleep off
        bus.writeto_mem(int(self.address), int(PWR_MGMT_1), b'\x00')
        time.sleep(0.1)
        # auto select clock source
        bus.writeto_mem(int(self.address), int(PWR_MGMT_1), b'\x01')
        time.sleep(0.1)
        # DLPF_CFG
        bus.writeto_mem(int(self.address), int(CONFIG), b'\x03')
        # sample rate divider
        bus.writeto_mem(int(self.address), int(SMPLRT_DIV), b'\x04')
        # gyro full scale select
        bus.writeto_mem(int(self.address), int(GYRO_CONFIG), bytes([gfs << 3]) )
        # accel full scale select
        bus.writeto_mem(int(self.address), int(ACCEL_CONFIG), bytes([afs << 3]) )
        # A_DLPFCFG
        bus.writeto_mem(int(self.address), int(ACCEL_CONFIG_2), b'\x03')
        # BYPASS_EN
        bus.writeto_mem(int(self.address), int(INT_PIN_CFG), b'\x02')
        time.sleep(0.1)

    ## Configure AK8963
    #  @param [in] self The object pointer.
    #  @param [in] mode Magneto Mode Select(default:AK8963_MODE_C8HZ[Continous 8Hz])
    #  @param [in] mfs Magneto Scale Select(default:AK8963_BIT_16[16bit])
    def configAK8963(self, mode, mfs):
        if mfs == AK8963_BIT_14:
            self.mres = 4912.0/8190.0
        else: #  mfs == AK8963_BIT_16:
            self.mres = 4912.0/32760.0

        bus.writeto_mem(int(AK8963_SLAVE_ADDRESS), int(AK8963_CNTL1), b'\x00')
        time.sleep(0.01)

        # set read FuseROM mode
        bus.writeto_mem(int(AK8963_SLAVE_ADDRESS), int(AK8963_CNTL1), b'\x0F')
        time.sleep(0.01)

        # read coef data
        data = bus.readfrom_mem(int(AK8963_SLAVE_ADDRESS), int(AK8963_ASAX), 3)

        self.magXcoef = (data[0] - 128) / 256.0 + 1.0
        self.magYcoef = (data[1] - 128) / 256.0 + 1.0
        self.magZcoef = (data[2] - 128) / 256.0 + 1.0

        # set power down mode
        bus.writeto_mem(int(AK8963_SLAVE_ADDRESS), int(AK8963_CNTL1), b'\x00')
        time.sleep(0.01)

        # set scale&continous mode
        bus.writeto_mem(int(AK8963_SLAVE_ADDRESS), int(AK8963_CNTL1), bytes([mfs<<4|mode]) )
        time.sleep(0.01)

    ## brief Check data ready
    #  @param [in] self The object pointer.
    #  @retval true data is ready
    #  @retval false data is not ready
    def checkDataReady(self):
        drdy = bus.readfrom_mem( int(self.address), int(INT_STATUS), 1 )
        if drdy[0] & 0x01:
            return True
        else:
            return False

    ## Read accelerometer
    #  @param [in] self The object pointer.
    #  @retval x : x-axis data
    #  @retval y : y-axis data
    #  @retval z : z-axis data
    def readAccel(self):
        data = bus.readfrom_mem( int(self.address), int(ACCEL_OUT), 6)
        Accel = [0,0,0]
        Accel[0] = self.dataConv(data[1], data[0])
        Accel[1] = self.dataConv(data[3], data[2])
        Accel[2] = self.dataConv(data[5], data[4])
        return Accel

    ## Read gyro
    #  @param [in] self The object pointer.
    #  @retval x : x-gyro data
    #  @retval y : y-gyro data
    #  @retval z : z-gyro data
    def readGyro(self):
        Gyro  = [0,0,0]

        data = bus.readfrom_mem(int(self.address), int(GYRO_OUT), 6)
        Gyro[0] = self.dataConv(data[1], data[0]) - self.gyroOffset[0]
        Gyro[1] = self.dataConv(data[3], data[2]) - self.gyroOffset[1]
        Gyro[2] = self.dataConv(data[5], data[4]) - self.gyroOffset[2]

        return Gyro

    ## Read magneto
    #  @param [in] self The object pointer.
    #  @retval x : X-magneto data
    #  @retval y : y-magneto data
    #  @retval z : Z-magneto data
    def readMagnet(self):
        # check data ready
        Mag   = [0,0,0]
        drdy = bus.readfrom_mem( int(AK8963_SLAVE_ADDRESS), int(AK8963_ST1), 1 )
        if drdy[0] & 0x01 :
            data = bus.readfrom_mem( int(AK8963_SLAVE_ADDRESS), int(AK8963_MAGNET_OUT) , 7 )
            # check overflow
            if (data[6] & 0x08)!=0x08:
                Mag[0] = self.dataConv(data[0], data[1]) - self.magOffset[0]
                Mag[1] = self.dataConv(data[2], data[3]) - self.magOffset[1]
                Mag[2] = self.dataConv(data[4], data[5]) - self.magOffset[2]
        return Mag
                
    def readGyroOffset(self, verbose=False):
        s32TempGx = 0
        s32TempGy = 0
        s32TempGz = 0
        nRead = 32
        if verbose:
            print("Starting Gyro Offset measurement                   ")
        for j in range(3):
            self.gyroOffset[j] = 0.
        # now start average    
        for i in range(nRead):
            Gyro = self.readGyro()
            s32TempGx += Gyro[0]
            s32TempGy += Gyro[1]
            s32TempGz += Gyro[2]
            time.sleep(0.1)
        self.gyroOffset[0] = s32TempGx / float(nRead)
        self.gyroOffset[1] = s32TempGy / float(nRead)
        self.gyroOffset[2] = s32TempGz / float(nRead)
        if verbose:
            print("Gyro offset calibrated: %7.2f, %7.2f, %7.2f" % \
                  (self.gyroOffset[0], self.gyroOffset[1], self.gyroOffset[2]))
        self.gyroCalibrated = True
        return
    
    ## Read temperature
    #  @param [out] temperature temperature(degrees C)
    def readTemperature(self):
        data = bus.readfrom_mem( int(self.address), int(TEMP_OUT), 2 )
        temp = self.dataConv(data[1], data[0])

        temp = round((temp / 333.87 + 21.0), 3)
        return temp

    ## Data Convert
    # @param [in] self The object pointer.
    # @param [in] data1 LSB
    # @param [in] data2 MSB
    # @retval Value MSB+LSB(int 16bit)
    def dataConv(self, data1, data2):
        value = data1 | (data2 << 8)
        if(value & (1 << 16 - 1)):
            value -= (1<<16)
        return value
    
    def magCalibI(self, verbose=False):
        """
        Magnetic Calibration requires rotating the device,
        done in three steps.
        """
        if verbose:
            print("\nkeep 10dof-imu device horizontal")
            print("Reading x y z axis offset value after 4 seconds\n")
        time.sleep(4)
        if verbose:
            print("start read all axises offset value \n")
        # initialize the offsets back to zeero
        for iii in range(3):
            self.magOffset[iii] = 0.
        nRead = 32
        for i in range(nRead):        
            Mag = self.readMagnet()
            for j in range(3):
                self.magTemp[j] = self.magTemp[j] + Mag[j]
            time.sleep(0.1)
        # now normalize average
        for j in range(3):
            self.magTemp[j] = self.magTemp[j]/float(nRead)
        return
    
    def magCalibII(self, verbose=False):
        """
        Second of three magnet calibration steps
        """
        if verbose:
            print("Z axis should be roated 180 degrees")
            print("Reading all axises offset values after 4 seconds\n")
        time.sleep(4)
        if verbose:
            print("starting read of all axises offset values\n")
        nRead = 32
        for i in range(nRead):
            Mag = self.readMagnet()
            for j in range(3):
                self.magTemp[j+3] = self.magTemp[j+3] + Mag[j]
            time.sleep(0.1)
        # now normalize average
        for j in range(3):
            self.magTemp[j+3] = self.magTemp[j+3]/float(nRead)
        return

    
    def magCalibIII(self, verbose=False):
        """
        Second of three magnet calibration steps
        """
        if verbose:
            print("\nFlip 10dof-imu device; Do not rotate!")
            print("Keep imu horizontal")
            print("Read all axises offset value after 4 seconds\n")
        time.sleep(4)
        if verbose:
            print("Starting read all axises offset value\n")
        nRead = 32
        for i in range(nRead):
            Mag = self.readMagnet()
            for j in range(3):
                self.magTemp[j+6] = self.magTemp[j+6] + Mag[j]
            time.sleep(0.1)
        # now normalize average
        for j in range(3):
            self.magTemp[j+6] = self.magTemp[j+6]/float(nRead)
        
        self.magOffset[0] = (self.magTemp[0]+self.magTemp[3])/2
        self.magOffset[1] = (self.magTemp[1]+self.magTemp[4])/2
        self.magOffset[2] = (self.magTemp[5]+self.magTemp[8])/2
        if verbose:
            print("Magnet Offset X: %7.2f" % (self.magOffset[0]))
            print("Magnet Offset Y: %7.2f" % (self.magOffset[1]))
            print("Magnet Offset Z: %7.2f" % (self.magOffset[2]))
        self.magCalibrated = True
        return
    
    def magCalib(self, verbose=False):
        """
        magnet sensor calibration requires moving the sensor.
        This process is divided into 3 sub-steps
        """
        self.magCalibI(verbose=verbose)
        self.magCalibII(verbose=verbose)
        self.magCalibIII(verbose=verbose)
        return

    def imuAHRSupdate(self,gx, gy,gz,ax,ay,az,mx,my,mz):
        """
        this module computes the role pitch and yaw based
        on input values.
        """
        norm=0.0    # define normaization 
        hx = hy = hz = bx = bz = 0.0
        vx = vy = vz = wx = wy = wz = 0.0
        exInt = eyInt = ezInt = 0.0
        ex=ey=ez=0.0 
        halfT = 0.024
        
        q0q0 = self.q0 * self.q0
        q0q1 = self.q0 * self.q1
        q0q2 = self.q0 * self.q2
        q0q3 = self.q0 * self.q3
        q1q1 = self.q1 * self.q1
        q1q2 = self.q1 * self.q2
        q1q3 = self.q1 * self.q3
        q2q2 = self.q2 * self.q2   
        q2q3 = self.q2 * self.q3
        q3q3 = self.q3 * self.q3          

        a = math.sqrt(ax * ax + ay * ay + az * az)
        # on first run this script may encouter a zero
        if a > 0.:
            norm = float(1./a)
        else:
            norm = 1.0        
        ax = ax * norm
        ay = ay * norm
        az = az * norm

        m = math.sqrt(mx * mx + my * my + mz * mz)
        if m > 0.:
            norm = float(1./m)
        else:
            norm = 1.0
        mx = mx * norm
        my = my * norm
        mz = mz * norm

        # compute reference direction of flux
        hx = 2 * mx * (0.5 - q2q2 - q3q3) + 2 * my * (q1q2 - q0q3) + 2 * mz * (q1q3 + q0q2)
        hy = 2 * mx * (q1q2 + q0q3) + 2 * my * (0.5 - q1q1 - q3q3) + 2 * mz * (q2q3 - q0q1)
        hz = 2 * mx * (q1q3 - q0q2) + 2 * my * (q2q3 + q0q1) + 2 * mz * (0.5 - q1q1 - q2q2)         
        bx = math.sqrt((hx * hx) + (hy * hy))
        bz = hz     

        # estimated direction of gravity and flux (v and w)
        vx = 2 * (q1q3 - q0q2)
        vy = 2 * (q0q1 + q2q3)
        vz = q0q0 - q1q1 - q2q2 + q3q3
        wx = 2 * bx * (0.5 - q2q2 - q3q3) + 2 * bz * (q1q3 - q0q2)
        wy = 2 * bx * (q1q2 - q0q3) + 2 * bz * (q0q1 + q2q3)
        wz = 2 * bx * (q0q2 + q1q3) + 2 * bz * (0.5 - q1q1 - q2q2)  

        # error is sum of cross product between reference direction of fields and direction measured by sensors
        ex = (ay * vz - az * vy) + (my * wz - mz * wy)
        ey = (az * vx - ax * vz) + (mz * wx - mx * wz)
        ez = (ax * vy - ay * vx) + (mx * wy - my * wx)

        if (ex != 0.0 and ey != 0.0 and ez != 0.0):
            exInt = exInt + ex * self.Ki * halfT
            eyInt = eyInt + ey * self.Ki * halfT  
            ezInt = ezInt + ez * self.Ki * halfT

            gx = gx + self.Kp * ex + exInt
            gy = gy + self.Kp * ey + eyInt
            gz = gz + self.Kp * ez + ezInt

        # the quaternion is updated iteratively
        self.q0 = self.q0 + (-self.q1 * gx - self.q2 * gy - self.q3 * gz) * halfT
        self.q1 = self.q1 + (self.q0 * gx + self.q2 * gz - self.q3 * gy) * halfT
        self.q2 = self.q2 + (self.q0 * gy - self.q1 * gz + self.q3 * gx) * halfT
        self.q3 = self.q3 + (self.q0 * gz + self.q1 * gy - self.q2 * gx) * halfT  
        #now normalize the quaternion 
        q = math.sqrt(self.q0 * self.q0 + self.q1 * self.q1 + self.q2 * self.q2 + self.q3 * self.q3)
        if q > 0.:
            norm = 1.0/ float(q)
        else:
            q = 1.0
        # keep track of the quaternion
        self.q0 = self.q0 * norm
        self.q1 = self.q1 * norm
        self.q2 = self.q2 * norm
        self.q3 = self.q3 * norm
        return self.q0, self.q1, self.q2, self.q3
        # end of imuAHRSupdate()
        
    def readRollPitchYaw(self):
        Gyro = self.readGyro()
        Accel = self.readAccel()
# disable magnetic computation
#        Mag = self.readMagnet()
        Mag = [0., 0., 1.]
        q0, q1, q2, q3 = self.imuAHRSupdate(Gyro[0]/32.8*0.0175, \
                              Gyro[1]/32.8*0.0175,Gyro[2]/32.8*0.0175, \
                              Accel[0],Accel[1],Accel[2], \
                              Mag[0], Mag[0], Mag[2])
        # based on the quaternion return the roll pitch and yaw
        # in degrees
        pitch = - math.asin((2. * (q1*q3) - (q0*q2)))* 57.3
        roll  = math.atan2(2. * ((q2 * q3) + (q0 * q1)), \
                           (q0*q0) - (q1*q1) - (q2* q2) + (q3*q3))* 57.3
        yaw   = math.atan2(2. * ((q1*q2) + (q0*q3)), \
                           ((q0*q0) + (q1*q1)) - ((q2*q2) + q3*q3)) * 57.3
        return roll, pitch, yaw
        # end of readRollPitchYaw()

import time
from machine import I2C
#i2c address
LPS22HB_I2C_ADDRESS   =  0x5C
#
LPS_ID                =  0xB1
#Register 
LPS_INT_CFG           =  0x0B        #Interrupt register
LPS_THS_P_L           =  0x0C        #Pressure threshold registers 
LPS_THS_P_H           =  0x0D        
LPS_WHO_AM_I          =  0x0F        #Who am I        
LPS_CTRL_REG1         =  0x10        #Control registers
LPS_CTRL_REG2         =  0x11
LPS_CTRL_REG3         =  0x12
LPS_FIFO_CTRL         =  0x14        #FIFO configuration register 
LPS_REF_P_XL          =  0x15        #Reference pressure registers
LPS_REF_P_L           =  0x16
LPS_REF_P_H           =  0x17
LPS_RPDS_L            =  0x18        #Pressure offset registers
LPS_RPDS_H            =  0x19        
LPS_RES_CONF          =  0x1A        #Resolution register
LPS_INT_SOURCE        =  0x25        #Interrupt register
LPS_FIFO_STATUS       =  0x26        #FIFO status register
LPS_STATUS            =  0x27        #Status register
LPS_PRESS_OUT_XL      =  0x28        #Pressure output registers
LPS_PRESS_OUT_L       =  0x29
LPS_PRESS_OUT_H       =  0x2A
LPS_TEMP_OUT_L        =  0x2B        #Temperature output registers
LPS_TEMP_OUT_H        =  0x2C
LPS_RES               =  0x33        #Filter reset register
class LPS22HB(object):
    def __init__(self,address=LPS22HB_I2C_ADDRESS):
        self._address = address
        self._bus = I2C(1)
        self.LPS22HB_RESET()                         #Wait for reset to complete
        self._write_byte(LPS_CTRL_REG1 ,0x02)        #Low-pass filter disabled , output registers not updated until MSB and LSB have been read , Enable Block Data Update , Set Output Data Rate to 0 
        # keep track of last temperature and pressure in case the read fails
        self.lastTemp = 0.0
        self.lastPress = 0.0
        
    def LPS22HB_RESET(self):
        Buf=self._read_u16(LPS_CTRL_REG2)
        Buf|=0x04                                         
        self._write_byte(LPS_CTRL_REG2,Buf)               #SWRESET Set 1
        while Buf:
            Buf=self._read_u16(LPS_CTRL_REG2)
            Buf&=0x04
            
    def LPS22HB_START_ONESHOT(self):
        Buf=self._read_u16(LPS_CTRL_REG2)
        Buf|=0x01                                         #ONE_SHOT Set 1
        self._write_byte(LPS_CTRL_REG2,Buf)
    def _read_byte(self,cmd):
        rec=self._bus.readfrom_mem(int(self._address),int(cmd),1)
        return rec[0]
    def _read_u16(self,cmd):
        LSB = self._bus.readfrom_mem(int(self._address),int(cmd),1)
        MSB = self._bus.readfrom_mem(int(self._address),int(cmd)+1,1)
        return (MSB[0] << 8) + LSB[0]
    def _write_byte(self,cmd,val):
        self._bus.writeto_mem(int(self._address),int(cmd),bytes([int(val)]))
    def read_pres(self):
        """
        Read the pressure, checking for data availlable
        """
        PRESS_DATA = 0.
        u8Buf=[0,0,0]
            # a new pressure data is generated
        if (self._read_byte(LPS_STATUS)&0x01)==0x01:  
            u8Buf[0] = self._read_byte(LPS_PRESS_OUT_XL)
            u8Buf[1] = self._read_byte(LPS_PRESS_OUT_L)
            u8Buf[2] = self._read_byte(LPS_PRESS_OUT_H)
            PRESS_DATA=((u8Buf[2]<<16)+(u8Buf[1]<<8)+u8Buf[0])/4096.0
            self.lastPress = PRESS_DATA
        else:
            PRESS_DATA = self.lastPress
        return PRESS_DATA
    
    def read_temp(self):
        TEMP_DATA = 0.
        u8Buf=[0,0,0]
            # a new pressure data is generated
        if (self._read_byte(LPS_STATUS)&0x02)==0x02:   # a new pressure data is generated
            u8Buf[0] = self._read_byte(LPS_TEMP_OUT_L)
            u8Buf[1] = self._read_byte(LPS_TEMP_OUT_H)
            TEMP_DATA=((u8Buf[1]<<8)+u8Buf[0])/100.0
            self.lastTemp = TEMP_DATA
        else:
            TEMP_DATA = self.lastPress

        return TEMP_DATA

    

