import Adafruit_SSD1306
from PIL import Image, ImageDraw, ImageFont

# Display setup (128x64 resolution)
WIDTH = 128
HEIGHT = 64

class SSD1306:
    
    def __init__(self):
        try:
            # I2C setup
            oled = Adafruit_SSD1306.SSD1306_128_64(rst=None, i2c_bus=1)
            self.oled = oled

            # Initialize the display
            oled.begin()
            oled.clear()
            oled.display()
        except Exception as e:
            print(f"Error initializing SSD1306: {e}")
            self.oled = None

    def clear_display(self):
        
        # Clear the display and update it
        self.oled.clear()
        self.oled.display()

    def show_image(self, image):

        # Check the image matches the display resolution
        if image.size != (WIDTH, HEIGHT):
            raise ValueError(f"Image size must be {WIDTH}x{HEIGHT}, but got {image.size}")       
    
        # Set and show image
        self.oled.image(image)
        self.oled.display()
