import subprocess
import sys
import os
import requests
import tarfile
from zipfile import ZipFile 

# vars for generating littlefs binary
EXTENSIONS = ['.bin', '.exe', '']
OS_PLATFORM = sys.platform
MKLITTLEFS_BIN_PATH = None
DATA_FILE = file = next((file for file in os.listdir("data/") if os.path.isfile(f"data/{file}")), None) # checks that a file is present in the data folder
LITTLEFS_BIN_PATH = 'littlefs.bin'

# vars for uploading file to esp
ESP_ARRAY = [] # each plugged in esp name will be stored in an array
CHIP = 'esp8266'
BAUD_RATE = '115200'

def get_mklittlefs_binary():

    global MKLITTLEFS_BIN_PATH
    api_url = 'https://api.github.com/repos/earlephilhower/mklittlefs/releases/tags/2.5.1-1' # the mklittlefs binary must be 2.5.1-1 because the deauther board core is on an earlier verison of Ardunio core
    platform_str = None
    download_url = None
    filename = None

    # check if mklittlefs binary or exe exists in mklittlfs folder
    if any(os.path.isfile(f'mklittlefs/mklittlefs{ext}') for ext in EXTENSIONS):
        print('mklittlefs binary already present...\n') 
        
    else:
        print('Downloading mklittlefs...\n')

        try:
            # fetch api url for the latest mklittlefs binary with a get request
            api_response = requests.get(api_url, timeout=10)
            # raise exception if status code is not in the 200 range
            api_response.raise_for_status()
            # extract json from the response
            api_json = api_response.json()
        
        except requests.exceptions.RequestException as e:
            print(e,'\n')
            exit(1)
   
        # determine the platform str to use based on current OS in use
        platform_map = {
        "win32": "x86_64-w64-mingw32",
        "darwin": "x86_64-apple-darwin",
        "linux": "x86_64-linux-gnu"}

        platform_str = platform_map.get(OS_PLATFORM)

        try:
        # go to the assets section of the json and loop every asset (numbered)
            for asset in api_json['assets']:
                # if the current asset number has the name section with a value of platform_str
                if platform_str in asset['name']:
                    # fetch download file url
                    download_url = asset['browser_download_url']
                    # also fetch the current asset filename
                    filename = asset['name']
                    break
        except KeyError as e:
            print('Error: The following JSON keys were not found from the request:', e,'\n')
            exit(1)
            
        try:
            # download the file with a get request
            file_response = requests.get(download_url)
            file_response.raise_for_status()

        except requests.exceptions.RequestException as e:
            print(e,'\n')
            exit(1)

        try:
            # get the file_response content and write the file with the filename
            with open(filename, 'wb') as compressed_file:
                compressed_file.write(file_response.content)
            compressed_file.close()

            print('Succesfully downloaded', filename,'\n')

        except IOError as e:
            print(e,'\n')
            exit(1)
               
        try: 
            # extract either the downloaded zip or tar.gz archive
            if OS_PLATFORM == 'win32':
                with ZipFile(filename) as zObject:
                    zObject.extractall()

            elif OS_PLATFORM == 'darwin' or OS_PLATFORM == 'linux':
                file = tarfile.open(filename)
                file.extractall(filter='data')
                file.close()

            print('Succesfully uncompressed', filename,'\n')
        
        except (tarfile.TarError, zipfile.BadZipFile) as e:
            print(e)

        # remove the zip / tar.gz archive
        os.remove(filename)
    
    MKLITTLEFS_BIN_PATH = next((f'mklittlefs/mklittlefs{ext}' for ext in EXTENSIONS if os.path.exists(f'mklittlefs/mklittlefs{ext}')), None)

def make_littlefs_binary():
    print('Creating',LITTLEFS_BIN_PATH,'...\n')
    try:
        cmd = [MKLITTLEFS_BIN_PATH, "-c", 'data/', "-p", "256", "-b", "8192", "-s", "2072576", LITTLEFS_BIN_PATH]
        subprocess.run(cmd, capture_output=True, text=True) # run the above command to create the littlefs filesystem with the text file data
        print('Succesfully created:', LITTLEFS_BIN_PATH, 'with', DATA_FILE, 'data\n')
    
    except subprocess.CalledProcessError as e:
        print(f"Error: mklittlefs failed with exit code {e.returncode}",'\n')
        # print("Output:\n", e.stderr if e.stderr else e.stdout)

    except FileNotFoundError:
        print(f"Error: mklittlefs binary not found at {MKLITTLEFS_BIN_PATH}",'\n')

    except PermissionError:
        print(f"Error: Permission denied when executing {MKLITTLEFS_BIN_PATH}",'\n')

def pop_esp_array():
    # determine esp name format as this is different among operating systems
    os_esp_format = ''
    if OS_PLATFORM == 'darwin':
        os_esp_format = 'tty.usbserial'
    if OS_PLATFORM == 'linux':
        os_esp_format = 'ttyUSB'
    # TODO add windows option

    # on mac and linux loop through /dev dir and add found esps to the array
    for esp in os.listdir('/dev'):
        if esp.startswith(os_esp_format):
            ESP_ARRAY.append(esp)

def upload_file_to_esp():
    print('Uploading LittleFS filesystem with', DATA_FILE,'...\n')
    # loop through the esp array and for each esp
    for esp in ESP_ARRAY:
        cmd = ['esptool.py', '--chip', CHIP, '--port', f'/dev/{esp}', '--baud', BAUD_RATE, 'write_flash', '2097152', LITTLEFS_BIN_PATH]
        subprocess.run(cmd) # run the above command to upload the littlefs filesystem with the text data to the current esp in the array
 
print('\nDetected OS:',OS_PLATFORM, '\n')

pop_esp_array()
print(ESP_ARRAY)
get_mklittlefs_binary()
make_littlefs_binary()
upload_file_to_esp()
