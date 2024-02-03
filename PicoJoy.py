# revamped Lcd1_14driver to separate Joystick from other parts.
# Glen Langstion, National Science Foundation,  2024 February 3
#
from machine import Pin,SPI,PWM
import framebuf
import time

BL = 13

class PicoJoy():

    def __init__(self):
        self.keyAA = Pin(15,Pin.IN,Pin.PULL_UP)
        self.keyBB = Pin(17,Pin.IN,Pin.PULL_UP)
    
        self.key2 = Pin(2 ,Pin.IN,Pin.PULL_UP) #上
        self.key3 = Pin(3 ,Pin.IN,Pin.PULL_UP)#中
        self.key4 = Pin(16 ,Pin.IN,Pin.PULL_UP)#左
        self.key5 = Pin(18 ,Pin.IN,Pin.PULL_UP)#下
        self.key6 = Pin(20 ,Pin.IN,Pin.PULL_UP)#右
        self.verbose = True
        self.pwm = PWM(Pin(BL))
        self.pwm.freq(1000)
        self.pwm.duty_u16(32768)   #max 65535
        
    def keyA(self):

        #  print(self.keyAA)
               
        if (self.keyAA.value() == 0):
            if self.verbose:
                print("A    ", end = "\r")
            return True
        else:		
            return False

    def keyB(self):
        if (self.keyBB.value() == 0):
            if self.verbose:
                print("B    ", end = "\r")
            return True
        else :
            return False

    def keyUp(self):
        if (self.key2.value() == 0):#上
            if self.verbose:
                print("Up    ", end = "\r")
            return True
        else :
            return False

    def keyCenter(self):
        if (self.key3.value() == 0):#中
            if self.verbose:
                print("Center    ", end = "\r")
            return True
        else :
            return False

    def keyLeft(self):
        if(self.key4.value() == 0):#左
            if self.verbose:
                print("Left    ", end = "\r")
            return True
        else :
            return False
            
    def keyDown(self):
        if(self.key5.value() == 0):#左
            if self.verbose:
                print("Down    ", end = "\r")
            return True
        else :
            return False
            
    def keyRight(self):
        if(self.key6.value() == 0):#右
            if self.verbose:
                print("Right    ", end = "\r")
            return True
        else :
            return False
        
    def wait(self,n=10.):
        """
        Wait n milliseconds for input
        """
        time.sleep( n/1000.)
        return
    
    def joystick(self):
        if self.keyA():
            return True, "A"
        if self.keyB():
            return True, "B"
        if self.keyUp():
            return True, "U"
        if self.keyDown():
            return True, "D"
        if self.keyCenter():
            return True, "C"
        if self.keyRight():
            return True, "R"
        if self.keyLeft():
            return True, "L"
        return False, " "
    
if __name__ == '__main__':
    
    print("Testing Joystick functions")
    print("Click Joystick B button to Exit")
    print(".... Waiting on Joystick input ! ....")
    joy = PicoJoy()
        
    while True:
        keyPushed, key = joy.joystick()
#        if keyPushed:
#             print("Key pushed: %s  " % (key), end="\r")
        time.sleep(.5)
        print("                                 ", end="\r")
        time.sleep(.5)
        if key=="B":
            print("B button pushed, Exiting!")
            break
            
        
