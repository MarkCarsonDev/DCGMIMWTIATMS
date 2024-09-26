import pystray
from PIL import Image, ImageDraw, ImageFont
from pystray import MenuItem as item
import threading
import time
import keyring
from pydexcom import Dexcom, AccountError
import tkinter as tk
from tkinter import simpledialog, messagebox
import time


# Function to clear saved credentials from the keyring
def clear_credentials():
    keyring.delete_password("dexcom", "username")
    keyring.delete_password("dexcom", "password")


# Function to authenticate with Dexcom
def authenticate_dexcom():
    # Retrieve saved credentials from the keyring
    username = keyring.get_password("dexcom", "username")
    password = keyring.get_password("dexcom", "password")

    # If credentials are missing, ask for them via a GUI
    if not username or not password:
        credentials_window()

    # After getting the credentials, authenticate with Dexcom
    username = keyring.get_password("dexcom", "username")
    password = keyring.get_password("dexcom", "password")

    if not username or not password:
        return None  # Handle failed authentication

    try:
        # Authenticate with Dexcom using the correct keyword arguments
        dexcom = Dexcom(username=username, password=password)
        return dexcom
    except AccountError as e:
        # Authentication failed, clear credentials and show an error
        clear_credentials()
        messagebox.showerror("Authentication Error", "Failed to authenticate. Please try again.")
        credentials_window()  # Prompt for credentials again
        return authenticate_dexcom()  # Retry authentication


# Function for fetching glucose reading from Dexcom
def get_glucose_reading(dexcom):
    try:
        glucose_data = dexcom.get_current_glucose_reading()
        return glucose_data.value  # Glucose value in mg/dL
    except Exception as e:
        return None  # Handle connection or data fetching errors


# Function to create an image with glucose value
def create_image_with_value(glucose_value):
    # Create an empty image
    image = Image.new('RGB', (64, 64), "black")
    draw = ImageDraw.Draw(image)

    # Load a font (adjust the path to a font on your system, or use default font)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except IOError:
        font = ImageFont.load_default()

    # Draw the glucose value as text in the middle of the image
    draw.text((8, 16), str(glucose_value), font=font, fill="white")

    return image


# Function to update the tray icon with the glucose value
def update_icon(icon, dexcom):
    while True:
        # Fetch the current glucose reading
        glucose_value = get_glucose_reading(dexcom)

        if glucose_value:
            # Update the icon with the current glucose value
            icon.icon = create_image_with_value(glucose_value)

            # Update the tooltip (hover text) with the current glucose value
            icon.title = f"Glucose Level: {glucose_value} mg/dL\nRefreshed at {time.strftime("%H:%M:%S", time.localtime())}"
        else:
            icon.title = "Error fetching glucose data"

        # Sleep for a while before updating again (e.g., every 5 minutes)
        time.sleep(300)  # Update every 5 minutes


# Function to quit the program when "Exit" is clicked
def quit_program(icon, item):
    icon.stop()


# Function to handle credential entry via a GUI
def credentials_window():
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Ask the user for Dexcom username and password
    username = simpledialog.askstring("Dexcom Login", "Enter your Dexcom username/email/phone:")

    if username:
        password = simpledialog.askstring("Dexcom Login", "Enter your Dexcom password:", show="*")

        if password:
            # Save credentials securely using keyring
            keyring.set_password("dexcom", "username", username)
            keyring.set_password("dexcom", "password", password)
            messagebox.showinfo("Success", "Credentials saved!")
        else:
            messagebox.showwarning("Error", "Credentials were not entered.")

    root.destroy()


# Function to set up and run the tray app 
def setup_tray():
    # Authenticate and get Dexcom object
    dexcom = authenticate_dexcom()

    if not dexcom:
        return

    # Create a system tray icon with a menu
    icon = pystray.Icon("glucose_monitor", create_image_with_value(get_glucose_reading(dexcom)), menu=pystray.Menu(
        item('Enter Credentials', lambda: credentials_window()),
        item('Exit', quit_program)
    ))

    # Set the initial tooltip with the first glucose reading
    glucose_value = get_glucose_reading(dexcom)
    if glucose_value:
        icon.title = f"Glucose Level: {glucose_value} mg/dL"
    else:
        icon.title = "Error fetching glucose data"

    # Start a separate thread to update the icon continuously
    threading.Thread(target=update_icon, args=(icon, dexcom)).start()

    # Run the icon in the system tray
    icon.run()


# Run the tray app setup in the main thread
if __name__ == "__main__":
    setup_tray()
