# # import os

# # # Set the revision to the new-style revision code for the board (800013 for revision 000F) to work with rpi-lgpio module
# # os.environ['RPI_LGPIO_REVISION'] = '800013'

# import RPi.GPIO as GPIO
# import time

# buttonPin = 27

# GPIO.setmode(GPIO.BCM)
# GPIO.setup(buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# def callback_button():
#     if GPIO.input(buttonPin) == GPIO.HIGH:
#         print("Button Pressed!")
#     else:
#         print("Button Not Pressed!")


# if __name__ == "__main__":
    
#     GPIO.add_event_detect(buttonPin, GPIO.BOTH, callback=callback_button, bouncetime=150)
#     while True:

#         time.sleep(0.5)

from gpiozero import Button
from signal import pause

# Define a button attached to GPIO pin 17
button = Button(17)

# Define the callback function
def on_button_pressed():
    print("Button was pressed!")

# Attach the callback function to the button press event
button.when_pressed = on_button_pressed

# Keep the program running to listen for events
pause()
