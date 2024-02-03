from machine import Pin,SPI,PWM
import framebuf
import time

DC = 8
RST = 12
MOSI = 11
SCK = 10
CS = 9


class Lcd1_14(framebuf.FrameBuffer):
    def __init__(self):
        self.width = 240
        self.height = 135
        
        self.cs = Pin(CS,Pin.OUT)
        self.rst = Pin(RST,Pin.OUT)
        
        self.cs(1)
        self.spi = SPI(1)
        self.spi = SPI(1,1000_000)
        self.spi = SPI(1,10000_000,polarity=0, phase=0,sck=Pin(SCK),mosi=Pin(MOSI),miso=None)
        self.dc = Pin(DC,Pin.OUT)
        self.dc(1)
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)  #Red Green Blue (16-bit, 5+6+5) color format
        self.lcd_init_display()
        
        self.red   =   0x07E0
        self.green =   0x001f
        self.blue  =   0xf800
        self.white =   0xffff
        
    def lcd_write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def lcd_write_data(self, buf):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)

    def lcd_init_display(self):
        """Initialize dispaly"""  
        self.rst(1)
        self.rst(0)
        self.rst(1)
        
        self.lcd_write_cmd(0x36)
        self.lcd_write_data(0x70)

        self.lcd_write_cmd(0x3A) 
        self.lcd_write_data(0x05)

        self.lcd_write_cmd(0xB2)
        self.lcd_write_data(0x0C)
        self.lcd_write_data(0x0C)
        self.lcd_write_data(0x00)
        self.lcd_write_data(0x33)
        self.lcd_write_data(0x33)

        self.lcd_write_cmd(0xB7)
        self.lcd_write_data(0x35) 

        self.lcd_write_cmd(0xBB)
        self.lcd_write_data(0x19)

        self.lcd_write_cmd(0xC0)
        self.lcd_write_data(0x2C)

        self.lcd_write_cmd(0xC2)
        self.lcd_write_data(0x01)

        self.lcd_write_cmd(0xC3)
        self.lcd_write_data(0x12)   

        self.lcd_write_cmd(0xC4)
        self.lcd_write_data(0x20)

        self.lcd_write_cmd(0xC6)
        self.lcd_write_data(0x0F) 

        self.lcd_write_cmd(0xD0)
        self.lcd_write_data(0xA4)
        self.lcd_write_data(0xA1)

        self.lcd_write_cmd(0xE0)
        self.lcd_write_data(0xD0)
        self.lcd_write_data(0x04)
        self.lcd_write_data(0x0D)
        self.lcd_write_data(0x11)
        self.lcd_write_data(0x13)
        self.lcd_write_data(0x2B)
        self.lcd_write_data(0x3F)
        self.lcd_write_data(0x54)
        self.lcd_write_data(0x4C)
        self.lcd_write_data(0x18)
        self.lcd_write_data(0x0D)
        self.lcd_write_data(0x0B)
        self.lcd_write_data(0x1F)
        self.lcd_write_data(0x23)

        self.lcd_write_cmd(0xE1)
        self.lcd_write_data(0xD0)
        self.lcd_write_data(0x04)
        self.lcd_write_data(0x0C)
        self.lcd_write_data(0x11)
        self.lcd_write_data(0x13)
        self.lcd_write_data(0x2C)
        self.lcd_write_data(0x3F)
        self.lcd_write_data(0x44)
        self.lcd_write_data(0x51)
        self.lcd_write_data(0x2F)
        self.lcd_write_data(0x1F)
        self.lcd_write_data(0x1F)
        self.lcd_write_data(0x20)
        self.lcd_write_data(0x23)
        
        self.lcd_write_cmd(0x21)

        self.lcd_write_cmd(0x11)

        self.lcd_write_cmd(0x29)

    def lcd_show(self):
        self.lcd_write_cmd(0x2A)
        self.lcd_write_data(0x00)
        self.lcd_write_data(0x28)
        self.lcd_write_data(0x01)
        self.lcd_write_data(0x17)
        
        self.lcd_write_cmd(0x2B)
        self.lcd_write_data(0x00)
        self.lcd_write_data(0x35)
        self.lcd_write_data(0x00)
        self.lcd_write_data(0xBB)
        
        self.lcd_write_cmd(0x2C)
        
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)
        
print("LCD Driver Loaded")


if __name__=='__main__':
    from machine import Pin,PWM
    import time
    LCD = Lcd1_14()

#------joystck pin declaration----- 
    joyRight = Pin(17,Pin.IN)
    joyDown  = Pin(18,Pin.IN)
    joySel   = Pin(19,Pin.IN)
    joyLeft  = Pin(20,Pin.IN)
    joyUp    = Pin(21,Pin.IN)


    BL = 13   # lcd back light pin declaration

    pwm = PWM(Pin(BL))
    pwm.freq(100)
    pwm.duty_u16(32768)    #max value is 65535
    LCD.fill(LCD.white)
 
    LCD.lcd_show()
    LCD.text("SB-COMPONENTS",60,40,LCD.red)
    LCD.text("Pico WIFI",60,60,LCD.red)
    LCD.text("Pico-LCD-1.14",60,80,LCD.red)
    
    
    
    LCD.hline(10,10,220,LCD.blue)
    LCD.hline(10,125,220,LCD.blue)
    LCD.vline(10,10,115,LCD.blue)
    LCD.vline(230,10,115,LCD.blue)
        
    LCD.lcd_show()
    
    while(1):
        
        if(joyRight.value() == 1):
            print("joyRight press")
            LCD.fill(0x00f0)     #0x00ff for red color 
            LCD.lcd_show()
                  
        elif(joyDown.value() == 1):
            print("joyDown press")
            LCD.fill(0x0f00)     #0x00ff for blue color 
            LCD.lcd_show()

        elif(joySel.value() == 1):
            print("joySel press")
            LCD.fill(0x000f)      #0x00ff for green color 
            LCD.lcd_show()
            
        elif(joyLeft.value() == 1):
            print("joyLeft press")
            LCD.fill(0x00ff)      #0x00ff for yellow color 
            LCD.lcd_show()
       
        elif(joyUp.value() == 1):
            print("joyUp press")
            LCD.fill(0xfff0)      #0x00ff for pink color 
            LCD.lcd_show()
        
            
            
    LCD.lcd_show()
    time.sleep(1)
    #LCD.fill(0xFFFF)


