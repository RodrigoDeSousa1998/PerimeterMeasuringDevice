import Adafruit_SSD1306
from PIL import Image, ImageDraw, ImageFont

# Display setup (128x64 resolution)
WIDTH = 128
HEIGHT = 64

class SSD1306:
    
    def __init__(self):
        
        # I2C setup
        oled = Adafruit_SSD1306.SSD1306_128_64(rst=None, i2c_bus=1)
        self.oled = oled

        # Initialize the display
        oled.begin()
        oled.clear()
        oled.display()

    def clear_display(self):
        
        # Clear the display
        self.oled.clear()

    def show_image(self, image):
        
        # Set and show image
        self.oled.image(image)
        self.oled.display()
