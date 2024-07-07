import webbrowser
from threading import Timer
from app import app
import platform
import os

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    system_arch = platform.machine()
    if system_arch == 'arm64':
        os.environ['PATH'] += os.pathsep + os.path.abspath('chromedriver_mac_arm')
    else:
        os.environ['PATH'] += os.pathsep + os.path.abspath('chromedriver_mac_x')
        
    Timer(1, open_browser).start()
    app.run(debug=True)
