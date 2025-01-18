#TODO: Organize thse sections of the code
import os

# Set the revision to the new-style revision code for the board (800013 for revision 000F) to work with rpi-lgpio module
os.environ['RPI_LGPIO_REVISION'] = '800013'

import time
import math
from enum import Enum

import smbus2
import RPi.GPIO as GPIO

from LSM6DS3 import LSM6DS3

# Define I2C bus
bus = smbus2.SMBus(1)

# # Pin definitions
# pinSDA = 3 # P1 header pin 3
# pinSCL = 5 # P1 header pin 5
pushButton = 11 # P1 header pin 11

# Set pin-numbering scheme to P1 Board Header 
GPIO.setmode(GPIO.BOARD)

# # Set GPIO pins to I2C and activate internal pull-up resistances
# GPIO.setup(pinSDA , GPIO.I2C, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(pinSCL , GPIO.I2C, pull_up_down=GPIO.PUD_UP)

# Set GPIO pins to I/O and activate internal pull-up resistances
GPIO.setup(pushButton, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def button_pressed_callback(channel):
    global current_state
    current_state = state(current_state.value + 1)
    print("Button pressed!")
    if current_state == state.CREDITS:
        current_state = state.MAIN_MENU


def calculate_perimeter(accelerations, sampling_interval):
    start_time = time.time()  # Start the timer
    total_distance = 0
    for acc in accelerations:
        # Assume `acc` is a tuple with (ax, ay, az)
        vector_magnitude = math.sqrt(sum(a ** 2 for a in acc))  # Vector magnitude
        total_distance += vector_magnitude * sampling_interval  # Simple integration
        time.sleep(sampling_interval)  # Simulate real-time sampling
    elapsed_time = time.time() - start_time  # End the timer
    return total_distance, elapsed_time

# States Definition
class state(Enum):
    MAIN_MENU = 1
    MEASURING_MODE = 2
    SETTINGS_MENU = 3
    CREDITS = 4

# Global Variables Definition
current_state = state.MAIN_MENU

#!############################## --- EXECUTIVE CYCLE --- ###############################

if __name__ == "__main__":
    
    print("Initializing LSM6DS3...")
    lsm6ds3 = LSM6DS3(bus)

    #TODO: Create inital menu to select resulution and sampling time
    acc_scaling_factor = 0.000061 # Sensitivity/Resolution for +-2g scale
    dps_scaling_factor = 0.0035  # Sensitivity/Resolution for +-1000dps scale

    GPIO.add_event_detect(pushButton, GPIO.RISING, callback=button_pressed_callback, bouncetime=150)

    try:

        while True:

            match current_state:

                case state.MAIN_MENU:
                    print("Press to start measurement...")

                    while current_state == state.MAIN_MENU:
                        time.sleep(0.1)

                case state.MEASURING_MODE:
                    acc_x = lsm6ds3.read_acceleration_x() * acc_scaling_factor
                    acc_y = lsm6ds3.read_acceleration_y() * acc_scaling_factor
                    acc_z = lsm6ds3.read_acceleration_z() * acc_scaling_factor

                    dps_x = lsm6ds3.read_gyroscope_x() * acc_scaling_factor
                    dps_y = lsm6ds3.read_gyroscope_y() * acc_scaling_factor
                    dps_z = lsm6ds3.read_gyroscope_z() * acc_scaling_factor

                    print(f"Accel (g): X={acc_x:.3f}, Y={acc_y:.3f}, Z={acc_z:.3f}")
                    print(f"Ang Rate (dps): X={dps_x:.3f}, Y={dps_y:.3f}, Z={dps_z:.3f}")
                    print("\033[2A", end="")  # Move cursor up 2 lines
                    
                    time.sleep(0.1) #Because IMU Output rate at 12.5 hz or 0.08s

                case _:
                    print("Default case")

    except IOError as e:
        print("Unable to communicate with LSM6DS3. Check connections.")
        print(e)
    except KeyboardInterrupt:
        print("Terminating program.")
    finally:
        GPIO.cleanup()  # Ensure GPIO resources are released
