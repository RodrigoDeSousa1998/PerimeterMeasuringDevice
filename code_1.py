
#TODO: Create script to initialize after turning RPi on and to turn the RPi off after pressing for more than 4 seconds
#TODO: Implement buzer to play for the time the button is being pushed
#TODO: Create menus for the OLED SS1306

# Python Standard Libraries
import os 
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
SHUTDOWN_THRESHOLD = 4.0 # seconds
PUSH_BUTTON_PIN = 17 # BCM GPIO 17 = Pin 11 in P1 Header
BUZZER_PIN = 18 # BCM GPIO 17 = Pin 12 in P1 Header
GPIO.setmode(GPIO.BCM) # Set pin-numbering scheme to BCM Pinout 
GPIO.setup(PUSH_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set GPIO pins to I/O and activate internal pull-up resistances
GPIO.setup(BUZZER_PIN, GPIO.OUT)

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
    END      = 6

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
resulting_vector = [0, 0] # List to store X,Y coordinates of resulting vector

# Callback function for button press/release
def button_press_callback(channel):
    global button_press_start_time, current_menu

    if GPIO.input(channel) == GPIO.HIGH:  # Button pressed (rising edge)
            #print("Button pressed!")
            GPIO.output(BUZZER_PIN, GPIO.HIGH)  # Activate buzzer
            button_press_start_time = time.time()  # Record the start time of the press

    if GPIO.input(channel) == GPIO.LOW:  # Button released (falling edge)
            GPIO.output(BUZZER_PIN, GPIO.LOW)  # Deactivate buzzer
            press_duration = time.time() - button_press_start_time  # Calculate how long the button was pressed

            if press_duration > SHUTDOWN_THRESHOLD:  # Shutdown condition
                shutdown_rpi()
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
        elif measurement == measure.END:
            print("Back to main menu after measuring!")
            # Reset Measuring Variables
            reset_measurement_variables()
            current_menu = option.MAIN_MENU
            measurement = measure.IDLE
    else:
        # current_menu = option(current_menu.value + 1)
        # if current_menu == option.SETTINGS_MENU:
            current_menu = option.MAIN_MENU

def handle_long_press():
    
    global current_menu, menu_selector, measurement
    
    if current_menu == option.MAIN_MENU:
        current_menu = menu_selector
        menu_selector = option.MEASURING_MODE

    elif current_menu == option.MEASURING_MODE:

        measurement = measure.END
                    
        # Display results
        calculate_perimiter()

    elif current_menu != option.MAIN_MENU:
        current_menu = option.MAIN_MENU

def shutdown_rpi():
    print("Shutting down the Raspberry Pi...")
    oled.clear()
    oled.display()
    os.system("sudo shutdown now")

def reset_measurement_variables():
    
    global acc_y, vel_y, dist_y, dps_y, deg_y, measure_mode, distances, rotations, x_coords, y_coords, resulting_vector
    
    acc_y = vel_y = dist_y = dps_y = deg_y = 0
    measure_mode = measure.DISTANCE
    
    distances = []
    rotations = [0]   
    x_coords = []
    y_coords = []
    resulting_vector = [0,0]

def calculate_perimiter():
    
    global distances, rotations, x_coords, y_coords, resulting_vector

    # Iterate over the polar coordinates
    for r, angle_deg in zip(distances, rotations):
        angle_rad = math.radians(angle_deg)  # Convert angle to radians
        x = r * math.cos(angle_rad)          # Calculate x coordinate
        y = r * math.sin(angle_rad)          # Calculate y coordinate
        x_coords.append(x)
        y_coords.append(y)        
        resulting_vector = [sum(x_coords), sum(y_coords)]
    
# Function to display the main menu on the OLED with the selector ball
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
        draw.text((20, y_position), item, font=font, fill=255)

        # Draw selector dot if this item is selected
        if menu_selector.value == i + 2:  # Align with option Enum values
            draw.ellipse((2, y_position + 4, 6, y_position + 8), outline=255, fill=255)  # Left position for ball


    # Display the updated image on the OLED
    oled.image(image)
    oled.display()

def draw_measuring_mode():
    
    global measurement, measure_mode, dist_y, deg_y, rotations, distances, resulting_vector, oled

    # Clear the OLED display
    oled.clear()

    # Create a new image with 1-bit color depth (black and white)
    image = Image.new('1', (oled.width, oled.height))
    draw = ImageDraw.Draw(image)

    # Load a font (adjust path as needed)
    font = ImageFont.load_default()

    # Draw "Measuring Mode" centered at the top
    title_text = "Measuring Mode"
    text_width, _ = draw.textsize(title_text, font=font)
    draw.text(((oled.width - text_width) // 2, 0), title_text, font=font, fill=255)

    # Define the second line text (either "Distance" or "Rotation")
    if measurement == measure.IDLE:
        mode_text = "Press to start..."
        value_text = ""  # No value to display in IDLE mode
        extra_value_text = "" # No value to display in IDLE mode
    elif measurement == measure.END:
        if len(rotations) != len (distances):
            mode_text = "Last distance missing!"
            value_text = f"Total distance: {resulting_vector[0]:.2f} m"
            extra_value_text = f"# of sides: {len(distances)}"
        else:
            if resulting_vector[0] != 0 or resulting_vector[1] != 0: #TODO: Here should be a threshold to account for error
                mode_text = "Perimeter not closed!"
                value_text = f"Total distance: {resulting_vector[0]:.2f} m"
                extra_value_text = f"# of sides: {len(distances)}"  
    else:
        if measure_mode == measure.DISTANCE:
            mode_text = "Distance:"
            value_text = f"{dist_y:.2f} m"
            extra_value_text = "Measuring..."
        else:
            mode_text = "Rotation:"
            value_text = f"{deg_y:.2f}°"
            extra_value_text = "Measuring..."

    # Draw the mode text (Distance, Rotation, or Results)
    draw.text((0, 16), mode_text, font=font, fill=255)

    # Draw the first value text on the second line
    draw.text((0, 32), value_text, font=font, fill=255)

    # Draw the extra value text on the third line
    draw.text((0, 48), extra_value_text, font=font, fill=255)

    # Display the updated image on the OLED
    oled.image(image)
    oled.display()

def draw_diag_mode():
    
    global oled

    # Clear the OLED display
    oled.clear()

    # Create a new image with 1-bit color depth (black and white)
    image = Image.new('1', (oled.width, oled.height))
    draw = ImageDraw.Draw(image)

    # Load a font (adjust path as needed)
    font = ImageFont.load_default()

    # Draw "Diagnostic Mode" centered at the top
    title_text = "Diagnostic Mode"
    text_width, _ = draw.textsize(title_text, font=font)
    draw.text(((oled.width - text_width) // 2, 0), title_text, font=font, fill=255)

    # Display diagnostic values
    acc_x = lsm6ds3.read_acceleration_x() * acc_scaling_factor
    acc_y = lsm6ds3.read_acceleration_y() * acc_scaling_factor
    acc_z = lsm6ds3.read_acceleration_z() * acc_scaling_factor

    dps_x = lsm6ds3.read_gyroscope_x() * dps_scaling_factor
    dps_y = lsm6ds3.read_gyroscope_y() * dps_scaling_factor
    dps_z = lsm6ds3.read_gyroscope_z() * dps_scaling_factor

    draw.text((0, 16), f"Ax:{acc_x:.2f}g", font=font, fill=255)
    draw.text((0, 32), f"Ay:{acc_y:.2f}g", font=font, fill=255)
    draw.text((0, 48), f"Az:{acc_z:.2f}g", font=font, fill=255)
    draw.text((64, 16), f"Ox:{dps_x:.2f}°/s", font=font, fill=255)
    draw.text((64, 32), f"Oy:{dps_y:.2f}°/s", font=font, fill=255)
    draw.text((64, 48), f"Oz:{dps_z:.2f}°/s", font=font, fill=255)

    # Display the updated image on the OLED
    oled.image(image)
    oled.display()

def draw_settings_menu():
    global oled, acc_scaling_factor, dps_scaling_factor

    # Clear the OLED display
    oled.clear()

    # Create a new image with 1-bit color depth (black and white)
    image = Image.new('1', (oled.width, oled.height))
    draw = ImageDraw.Draw(image)

    # Load a font (adjust path as needed)
    font = ImageFont.load_default()

    # Draw "Settings Menu" centered at the top
    title_text = "Settings Menu"
    text_width, _ = draw.textsize(title_text, font=font)
    draw.text(((oled.width - text_width) // 2, 0), title_text, font=font, fill=255)

    # Display current settings
    draw.text((0, 16), "Resolution:", font=font, fill=255)
    draw.text((0, 32), f"Acc: {acc_scaling_factor} g/LSB", font=font, fill=255)
    draw.text((0, 48), f"Gyro: {dps_scaling_factor} °/s/LSB", font=font, fill=255)

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
                #print("Measuring Mode")

                if measurement == measure.START:
                    if measure_mode == measure.DISTANCE:
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

                    draw_measuring_mode()

                elif measurement == measure.STOP:
                    measurement = measure.IDLE #In between measurements
                    if measure_mode == measure.DISTANCE:
                        distances.append(dist_y) # Saving last measured distance
                        measure_mode = measure.ANGLE
                    elif measure_mode == measure.ANGLE:
                        rotations.append(deg_y) # Saving last measured roatation
                        measure_mode = measure.DISTANCE
                
                elif measurement == measure.IDLE:
                        draw_measuring_mode()
                        time.sleep(0.1)
                else:
                        draw_measuring_mode()
                        time.sleep(0.1)

            elif current_menu == option.DIAG_MODE:
                # print("Diagnostic Mode")                    
                    
                # acc_x = lsm6ds3.read_acceleration_x() * acc_scaling_factor
                # acc_y = lsm6ds3.read_acceleration_y() * acc_scaling_factor
                # acc_z = lsm6ds3.read_acceleration_z() * acc_scaling_factor

                # dps_x = lsm6ds3.read_gyroscope_x() * acc_scaling_factor
                # dps_y = lsm6ds3.read_gyroscope_y() * acc_scaling_factor
                # dps_z = lsm6ds3.read_gyroscope_z() * acc_scaling_factor

                # print(f"Accel (g): X={acc_x:.3f}, Y={acc_y:.3f}, Z={acc_z:.3f}")
                # print(f"Ang Rate (dps): X={dps_x:.3f}, Y={dps_y:.3f}, Z={dps_z:.3f}")
                # print("\033[2A", end="")  # Move cursor up 2 lines
                    
                # while current_menu == option.DIAG_MODE:
                #     time.sleep(0.1)

                draw_diag_mode()
                time.sleep(0.1)

            elif current_menu == option.SETTINGS_MENU:
                # print("Settings")         

                # #TODO: Create initial menu to select resulution units
                # print(f"Accelerometer resolution {acc_scaling_factor}m")
                # print(f"Gyroscope resolution: {dps_scaling_factor}°")
                # print("Scale: +-2g")

                # while current_menu == option.SETTINGS_MENU:
                #     time.sleep(0.1)
                draw_settings_menu()
                time.sleep(0.5)

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