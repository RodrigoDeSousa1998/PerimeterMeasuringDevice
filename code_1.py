
#TODO: Create script to initialize after turning RPi on and to turn the RPi off after pressing for more than 4 seconds
#TODO: Implement buzer to play for the time the button is being pushed
#TODO: Create menus for the OLED SS1306

# Python Standard Libraries 
import time
import math
from enum import Enum

# Modules to interact with the Raspberry Pi hardware
import smbus2
import RPi.GPIO as GPIO

# Modules to interact with the connected components
from LSM6DS3 import LSM6DS3
import Adafruit_SSD1306
from PIL import Image, ImageDraw, ImageFont

# GPIO Configuration
SHORT_PRESS_THRESHOLD = 1.0  # seconds - short press duration
PUSH_BUTTON_PIN = 17 # BCM GPIO 17 = Pin 11 in P1 Header
GPIO.setmode(GPIO.BCM) # Set pin-numbering scheme to BCM Pinout 
GPIO.setup(PUSH_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set GPIO pins to I/O and activate internal pull-up resistances

# I2C Bus Definition
bus = smbus2.SMBus(1)

# IMU Initialization
print("Initializing LSM6DS3...")
lsm6ds3 = LSM6DS3(bus)

# Display Initialization
print("Initializing SSD1306...")
oled = Adafruit_SSD1306.SSD1306_128_64(rst=24, i2c_address=0x3C)
oled.begin()
oled.clear()
oled.display()

# Machine States Definition
class option(Enum):
    MAIN_MENU      = 1
    MEASURING_MODE = 2
    DIAG_MODE      = 3
    SETTINGS_MENU  = 4

# Measument Modes Definition
class measure(Enum):
    ANGLE    = 1
    DISTANCE = 2
    START    = 3
    STOP     = 4
    IDLE     = 5

# Global Variables Definition
current_menu            = option.MAIN_MENU # State variable for mode selection
menu_selector           = option.MEASURING_MODE
button_press_start_time = 0                # Variable to track press time
measurement             = measure.IDLE     # Flag to dectect begining of measurement
measure_mode            = measure.DISTANCE # Alternating variable to change types of measurement

acc_y             = 0    # Variable to store accelaration on the Y axis
vel_y             = 0    # Variable to store velocity on the Y axis
dist_y            = 0    # Variable to store distance on the Y axis
dps_y             = 0    # Variable to store angular speed on the Y axis
deg_y             = 0    # Variable to store rotation on the Y axis
sampling_interval = 0.1  # Sampling interval because IMU Output rate at 12.5 hz or 0.08s

distances = []  # List of distances measured 
rotations = [0] # List of rotations measured

x_coords = []         # List to store X coordinates
y_coords = []         # List to store Y coordinates
resulting_vector = [] # List to store X,Y coordinates of resulting vector

# Callback function for button press/release
def button_press_callback(channel):
    global button_press_start_time, current_menu

    if GPIO.input(channel) == GPIO.HIGH:  # Button pressed (rising edge)
            #print("Button pressed!")
            button_press_start_time = time.time()  # Record the start time of the press

    if GPIO.input(channel) == GPIO.LOW:  # Button released (falling edge)
            press_duration = time.time() - button_press_start_time  # Calculate how long the button was pressed
           
            if press_duration < SHORT_PRESS_THRESHOLD:
                #print("Short press detected!")
                handle_short_press()
            else:
                #print("Long press detected!")
                handle_long_press()
        
def handle_short_press():
    
    global current_menu, menu_selector, measurement
    
    if current_menu == option.MAIN_MENU:
        if menu_selector == option.MAIN_MENU or menu_selector == option.SETTINGS_MENU:
            menu_selector = option.MEASURING_MODE
        else:
            menu_selector = option(menu_selector.value + 1)

    elif current_menu == option.MEASURING_MODE: 
        if measurement == measure.STOP or measurement == measure.IDLE:
            print("Measurement started!")
            measurement = measure.START
        elif measurement == measure.START:
            print("Measurement stoped!")
            measurement = measure.STOP
    else:
        current_menu = option(current_menu.value + 1)
        if current_menu == option.CREDITS:
            current_menu = option.MAIN_MENU

def handle_long_press():
    
    global current_menu, menu_selector
    
    if current_menu == option.MAIN_MENU:
        current_menu = menu_selector
        menu_selector = option.MEASURING_MODE

    elif current_menu == option.MEASURING_MODE:
        print("Back to main menu after measuring!")
        current_menu = option.MAIN_MENU
                    
        # Display results
        calculate_perimiter()

        # Reset Measuring Variables
        reset_measurement_variables()

    elif current_menu != option.MAIN_MENU:
        current_menu = option.MAIN_MENU


def reset_measurement_variables():
    
    global acc_y, vel_y, dist_y, dps_y, deg_y, sampling_interval, measure_mode
    
    acc_y = vel_y = dist_y = dps_y = deg_y = 0
    sampling_interval = 0.1
    measure_mode = measure.DISTANCE

def calculate_perimiter():
    
    global distances, rotations
    
    for rotation in rotations:
        print(rotation)

    for distance in distances:
        print(distance)

    # Convert to cartesian coordinates
    if len(rotations) == len (distances):

        global x_coords, y_coords, resulting_vector
        
        # Iterate over the polar coordinates
        for r, angle_deg in zip(distances, rotations):
            angle_rad = math.radians(angle_deg)  # Convert angle to radians
            x = r * math.cos(angle_rad)          # Calculate x coordinate
            y = r * math.sin(angle_rad)          # Calculate y coordinate
            x_coords.append(x)
            y_coords.append(y)        
            resulting_vector = [sum(x_coords), sum(y_coords)]
        
        if resulting_vector[0] != 0 or resulting_vector[1] != 0: #TODO: Here should be a threshold to account for error
            print("Perimeter not closed!")
            #TODO: Put number of sides here  
        
        print (f"Total distance measured: {sum(distances)}")
            
    else:
        print ("Last distance missing!")

    # Reset Measurements
    distances = []
    rotations = [0]   
    x_coords = []
    y_coords = []
    resulting_vector = []
    
# # Function to display the main menu on the OLED with the selector ball
def draw_main_menu():
    
    global menu_selector, oled

    # Clear the OLED display
    oled.clear()

    # Create a new image with 1-bit color depth (black and white)
    image = Image.new('1', (oled.width, oled.height))
    draw = ImageDraw.Draw(image)

    # Load a font (adjust path as needed)
    font = ImageFont.load_default()

    # Draw "Main Menu" centered at the top
    menu_text = "Main Menu"
    text_width, _ = draw.textsize(menu_text, font=font)
    draw.text(((oled.width - text_width) // 2, 0), menu_text, font=font, fill=255)

    # Define menu items
    menu_items = [
        "1. Measuring Mode",
        "2. Diagnostic Mode",
        "3. Settings Mode"
    ]

    # Display each menu item with a selector
    for i, item in enumerate(menu_items):
        y_position = 16 + (i * 16)  # Position for each menu item (16 pixels apart)

        # Draw menu item text
        #draw.text((0, y_position), item, font=font, fill=255)
        draw.text((20, y_position), item, font=font, fill=255)

        # Draw selector dot if this item is selected
        if menu_selector.value == i + 2:  # Align with option Enum values
            #draw.ellipse((oled.width - 10, y_position + 4, oled.width - 6, y_position + 8), outline=255, fill=255)
            draw.ellipse((2, y_position + 4, 6, y_position + 8), outline=255, fill=255)  # Left position for ball


    # Display the updated image on the OLED
    oled.image(image)
    oled.display()

#!############################## --- EXECUTIVE CYCLE --- ###############################

if __name__ == "__main__":
    
    acc_scaling_factor = 0.000061 # Sensitivity/Resolution for +-2g scale
    dps_scaling_factor = 0.0035  # Sensitivity/Resolution for +-1000dps scale

    GPIO.add_event_detect(PUSH_BUTTON_PIN, GPIO.BOTH, callback=button_press_callback, bouncetime=150)

    try:
        while True:
            if current_menu == option.MAIN_MENU:
                
                #print("Press to start measurement...")
                print(f"current_menu:{current_menu}")
                print(f"menu_selector:{menu_selector}")
                print("\033[2A", end="")  # Move cursor up 2 lines

                draw_main_menu()
                time.sleep(0.1)

                # while current_menu == option.MAIN_MENU:
                #     time.sleep(0.1)

            elif current_menu == option.MEASURING_MODE:
                print("Measuring Mode")

                if measurement is measure.START:
                    if measure_mode is measure.DISTANCE:
                        print("Measuring distance...")  
                        print("\033[2A", end="")  # Move cursor up 2 lines
                        acc_y = lsm6ds3.read_acceleration_y() * acc_scaling_factor
                        vel_y += acc_y * sampling_interval
                        dist_y += vel_y * sampling_interval  
                        time.sleep(sampling_interval) 
                    else:
                        print("Measuring rotation...")
                        print("\033[2A", end="")  # Move cursor up 2 lines
                        dps_y = lsm6ds3.read_gyroscope_y() * acc_scaling_factor
                        deg_y += dps_y * sampling_interval
                        time.sleep(sampling_interval)  
                elif measurement is measure.STOP:
                    measurement = measure.IDLE #In between measurements
                    if measure_mode is measure.DISTANCE:
                        distances.append(dist_y) # Saving last measured distance
                        measure_mode = measure.ANGLE
                    elif measure_mode is measure.ANGLE:
                        rotations.append(deg_y) # Saving last measured roatation
                        measure_mode = measure.DISTANCE
                else:
                    while current_menu is option.MEASURING_MODE and measurement is measure.IDLE:
                        time.sleep(0.1)

            elif current_menu == option.DIAG_MODE:
                print("Diagnostic Mode")                    
                    
                acc_x = lsm6ds3.read_acceleration_x() * acc_scaling_factor
                acc_y = lsm6ds3.read_acceleration_y() * acc_scaling_factor
                acc_z = lsm6ds3.read_acceleration_z() * acc_scaling_factor

                dps_x = lsm6ds3.read_gyroscope_x() * acc_scaling_factor
                dps_y = lsm6ds3.read_gyroscope_y() * acc_scaling_factor
                dps_z = lsm6ds3.read_gyroscope_z() * acc_scaling_factor

                print(f"Accel (g): X={acc_x:.3f}, Y={acc_y:.3f}, Z={acc_z:.3f}")
                print(f"Ang Rate (dps): X={dps_x:.3f}, Y={dps_y:.3f}, Z={dps_z:.3f}")
                print("\033[2A", end="")  # Move cursor up 2 lines
                    
                while current_menu == option.DIAG_MODE:
                    time.sleep(0.1)

            elif current_menu == option.SETTINGS_MENU:
                print("Settings")         

                #TODO: Create inital menu to select resulution and sampling time
                acc_scaling_factor = 0.000061 # Sensitivity/Resolution for +-2g scale
                dps_scaling_factor = 0.0035  # Sensitivity/Resolution for +-1000dps scale

                while current_menu == option.SETTINGS_MENU:
                    time.sleep(0.1)

            else:
                current_menu = option.MAIN_MENU
                print("Default case")

    except IOError as e:
        print("Unable to communicate with LSM6DS3 or SSD1306. Check connections.")
        print(e)
        print(f"Error type: {type(e)}")
    except KeyboardInterrupt:
        print("Terminating program.")
    finally:
        GPIO.cleanup()  # Ensure GPIO resources are released