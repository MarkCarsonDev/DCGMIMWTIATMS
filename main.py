import pystray
from PIL import Image, ImageDraw, ImageFont
from pystray import MenuItem as item
import threading
import time
import keyring
from pydexcom import Dexcom, AccountError
import tkinter as tk
from tkinter import simpledialog, messagebox
import os
import sys
import winreg  # For setting run at startup on Windows

# Global flag to control the update thread
stop_flag = False


# Function to clear saved credentials from the keyring
def clear_credentials():
    keyring.delete_password("dexcom", "username")
    keyring.delete_password("dexcom", "password")


# Function to authenticate with Dexcom
def authenticate_dexcom():
    username = keyring.get_password("dexcom", "username")
    password = keyring.get_password("dexcom", "password")

    if not username or not password:
        credentials_window()
        username = keyring.get_password("dexcom", "username")
        password = keyring.get_password("dexcom", "password")

    if not username or not password:
        return None

    try:
        dexcom = Dexcom(username=username, password=password)
        return dexcom
    except AccountError:
        clear_credentials()
        messagebox.showerror("Authentication Error", "Failed to authenticate. Please try again.")
        credentials_window()
        return authenticate_dexcom()


# Function for fetching glucose reading from Dexcom
def get_glucose_reading(dexcom):
    try:
        glucose_data = dexcom.get_current_glucose_reading()
        return glucose_data.value
    except Exception:
        return None


# Function to create an image with glucose value
def create_image_with_value(glucose_value):
    image = Image.new('RGB', (64, 64), (255, 182, 193))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except IOError:
        font = ImageFont.load_default()

    draw.text((8, 16), str(glucose_value), font=font, fill="black")

    return image


# Function to update the tray icon with the glucose value
def update_icon(icon, dexcom):
    global stop_flag  # Access the global stop flag

    while not stop_flag:  # Run until the stop flag is set to True
        glucose_value = get_glucose_reading(dexcom)

        if glucose_value:
            icon.icon = create_image_with_value(glucose_value)
            icon.title = f"Glucose Level: {glucose_value} mg/dL\nRefreshed at {time.strftime('%H:%M:%S', time.localtime())}"
        else:
            icon.title = "Error fetching glucose data"
            dexcom = authenticate_dexcom()

        time.sleep(300)  # Update every 5 minutes


# Function to quit the program when "Exit" is clicked
def quit_program(icon, item):
    global stop_flag  # Use the global stop flag
    stop_flag = True  # Signal the update thread to stop
    icon.stop()  # Stop the tray icon
    os._exit(0)  # Forcefully terminate the program


# Function to handle credential entry via a GUI
def credentials_window():
    root = tk.Tk()
    root.withdraw()

    username = simpledialog.askstring("Dexcom Login", "Enter your Dexcom username/email/phone:")
    if username:
        password = simpledialog.askstring("Dexcom Login", "Enter your Dexcom password:", show="*")
        if password:
            keyring.set_password("dexcom", "username", username)
            keyring.set_password("dexcom", "password", password)
            messagebox.showinfo("Success", "Credentials saved!")
        else:
            messagebox.showwarning("Error", "Credentials were not entered.")
    root.destroy()


# Function to set up 'Run on Startup' option
def toggle_run_on_startup(icon, item):
    app_name = "GlucoseMonitor"
    startup_path = f"{os.environ['APPDATA']}\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\{app_name}.lnk"
    exe_path = sys.executable

    if item.checked:
        if os.path.exists(startup_path):
            os.remove(startup_path)
    else:
        import winshell
        shortcut = winshell.shortcut(startup_path)
        shortcut.path = exe_path
        shortcut.write()

    item.checked = not item.checked


# Function to reload the application
def reload_app(icon, item):
    global stop_flag  # Use the global stop flag
    stop_flag = True  # Signal the update thread to stop
    icon.stop()  # Stop the tray icon
    setup_tray()  # Restart the tray app


# Function to set up and run the tray app
def setup_tray():
    global stop_flag  # Access the global stop flag
    stop_flag = False  # Reset the stop flag

    dexcom = authenticate_dexcom()
    if not dexcom:
        return

    icon = pystray.Icon("glucose_monitor", create_image_with_value(get_glucose_reading(dexcom)), menu=pystray.Menu(
        item('Enter Credentials', lambda: credentials_window()),
        item('Reload App', reload_app),
        item('Run on Startup', toggle_run_on_startup, checked=lambda item: check_run_on_startup()),
        item('Exit', quit_program)
    ))

    glucose_value = get_glucose_reading(dexcom)
    if glucose_value:
        icon.title = f"Glucose Level: {glucose_value} mg/dL"
    else:
        icon.title = "Error fetching glucose data"

    # Start the update thread with respect to the global stop flag
    threading.Thread(target=update_icon, args=(icon, dexcom), daemon=True).start()
    icon.run()


# Function to check if the app is set to run on startup
def check_run_on_startup():
    app_name = "GlucoseMonitor"
    startup_path = f"{os.environ['APPDATA']}\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\{app_name}.lnk"
    return os.path.exists(startup_path)


if __name__ == "__main__":
    setup_tray()
