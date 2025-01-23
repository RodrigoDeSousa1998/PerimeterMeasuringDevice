# import os

# # Set the revision to the new-style revision code for the board (800013 for revision 000F) to work with rpi-lgpio module
# os.environ['RPI_LGPIO_REVISION'] = '800013'

import RPi.GPIO as GPIO
import time

buttonPin = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def callback_button(channel):
    if GPIO.input(buttonPin) == GPIO.HIGH:
        print("Button Pressed!")
    else:
        print("Button Not Pressed!")


if __name__ == "__main__":
    
    GPIO.add_event_detect(buttonPin, GPIO.BOTH, callback=callback_button, bouncetime=150)
    try:    
        while True:

            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Terminating program.")    
    finally:
        GPIO.cleanup()  # Ensure GPIO resources are released
