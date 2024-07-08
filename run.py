import webbrowser
from threading import Timer
from app import app
import platform
import os

def open_browser():
    print("Opening browser...")
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    system_arch = platform.machine()
    if system_arch == 'arm64':
        chromedriver_path = os.path.abspath('chromedriver_mac_arm')
    else:
        chromedriver_path = os.path.abspath('chromedriver_mac_x')

    if os.path.exists(chromedriver_path):
        os.environ['PATH'] += os.pathsep + chromedriver_path
        print(f"Added chromedriver to PATH: {chromedriver_path}")
    else:
        print(f"Chromedriver not found at path: {chromedriver_path}")
    
    Timer(1, open_browser).start()
    try:
        app.run(debug=True)
    except Exception as e:
        print(f"Error starting Flask server: {e}")
