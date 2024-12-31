import time
import smbus2
import RPi.GPIO as GPIO

from LSM6DS3 import LSM6DS3

# # Define I2C bus
# bus = smbus2.SMBus(1)

# # Pin definitions
# pinSDA = 3 # P1 header pin 3
# pinSCL = 5 # P1 header pin 5

# # Set pin-numbering scheme to P1 Board Header 
# GPIO.setmode(GPIO.BOARD)

# # Set GPIO pins to I2C and activate internal pull-up resistances
# GPIO.setup(pinSDA , GPIO.I2C, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(pinSCL , GPIO.I2C, pull_up_down=GPIO.PUD_UP)



if __name__ == "__main__":
    
    print("Initializing LSM6DS3...")
    lsm6ds3 = LSM6DS3()

    acc_scaling_factor = 0.000061 # Sensitivity/Resolution for +-2g scale
    dps_scaling_factor = 0.0035  # Sensitivity/Resolution for +-1000dps scale


    try:

        while True:
            acc_x = lsm6ds3.read_acceleration_x() * acc_scaling_factor
            acc_y = lsm6ds3.read_acceleration_y() * acc_scaling_factor
            acc_z = lsm6ds3.read_acceleration_z() * acc_scaling_factor

            dps_x = lsm6ds3.read_gyroscope_x() * acc_scaling_factor
            dps_y = lsm6ds3.read_gyroscope_y() * acc_scaling_factor
            dps_z = lsm6ds3.read_gyroscope_z() * acc_scaling_factor

            print(f"Accel (g): X={acc_x:.3f}, Y={acc_y:.3f}, Z={acc_z:.3f}")
            print(f"Ang Rate (dps): X={dps_x:.3f}, Y={dps_y:.3f}, Z={dps_z:.3f}")
            print("\033[2A", end="")  # Move cursor up 2 lines
            
            time.sleep(0.1) #IMU Output rate at 12.5 hz or 0.08s

    except IOError as e:
        print("Unable to communicate with LSM6DS3. Check connections.")
        print(e)
    except KeyboardInterrupt:
        print("Terminating program.")
