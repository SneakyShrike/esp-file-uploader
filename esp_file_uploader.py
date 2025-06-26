import subprocess
import sys
import os
import re
import requests
import tarfile
import serial
from serial.tools import list_ports
from zipfile import ZipFile 

# vars for generating littlefs binary
EXTENSIONS = ['.bin', '.exe', '']
OS_PLATFORM = sys.platform
MKLITTLEFS_BIN_PATH = None
DATA_FOLDER = 'data/'
DATA_FOLDER_FILES = os.listdir(DATA_FOLDER)
LITTLEFS_BIN_PATH = 'littlefs.bin'

# vars for uploading file to esp
CHIP = 'esp8266'
BAUD_RATE = '115200'

def check_data_file():

    text_files = ['macs.txt', 'deauth_settings.txt']

    # check if DATA_DIRECTORY exists
    if not os.path.isdir(DATA_FOLDER):
        print(f'\n{DATA_FOLDER} folder not found, please create this directory...')
        exit(1)

    # filter the DATA_DIRECTORY to only include visible files (files that don't start with .)
    visible_files = [file for file in DATA_FOLDER_FILES if not file.startswith('.') and os.path.isfile(os.path.join(DATA_FOLDER, file))]

    # if the counted files in DATA_DIRECTORY is not exactly one
    if len(visible_files) != 1:
        print(f'\n{DATA_FOLDER} folder is either empty or contains more than 1 file...')
        exit(1)

    # assign the one file in DATA_DIRECTORY to a var
    file = visible_files[0]

    # check if that one file in DATA_DIRECTORY matches a value in the text_files array
    if file not in text_files:
        print(f'\n{DATA_FOLDER} folder should only contain ONE of the following: {text_files}')
        exit(1)
    
    print(f'\n{file} found in {DATA_FOLDER} folder...')

def get_mklittlefs_binary():

    global MKLITTLEFS_BIN_PATH
    api_url = 'https://api.github.com/repos/earlephilhower/mklittlefs/releases/tags/2.5.1-1' # the mklittlefs binary must be 2.5.1-1 because the deauther board core is on an earlier verison of Ardunio core
    download_platform_str = None
    download_url = None
    filename = None

    # check if mklittlefs binary or exe exists in mklittlfs folder
    if any(os.path.isfile(f'mklittlefs/mklittlefs{ext}') for ext in EXTENSIONS):
        print('\nmklittlefs binary already present...') 
        
    else:
        print('\nDownloading mklittlefs...')

        try:
            # fetch api url for the latest mklittlefs binary with a get request
            api_response = requests.get(api_url, timeout=10)
            # raise exception if status code is not in the 200 range
            api_response.raise_for_status()
            # extract json from the response
            api_json = api_response.json()
        
        except requests.exceptions.RequestException as e:
            print(f'\n{e}')
            exit(1)
   
        # determine the platform str to use based on current OS in use
        download_platform_map = {
        "win32": "x86_64-w64-mingw32",
        "darwin": "x86_64-apple-darwin",
        "linux": "x86_64-linux-gnu"}

        download_platform_str = download_platform_map.get(OS_PLATFORM)

        try:
        # go to the assets section of the json and loop every asset (numbered)
            for asset in api_json['assets']:
                # if the current asset number has the name section with a value of platform_str
                if download_platform_str in asset['name']:
                    # fetch download file url
                    download_url = asset['browser_download_url']
                    # also fetch the current asset filename
                    filename = asset['name']
                    break
        except KeyError as e:
            print(f'\nError: The following JSON keys were not found from the request: {e}')
            exit(1)
            
        try:
            # download the file with a get request
            file_response = requests.get(download_url)
            file_response.raise_for_status()

        except requests.exceptions.RequestException as e:
            print(f'\n{e}')
            exit(1)

        try:
            # get the file_response content and write the file with the filename
            with open(filename, 'wb') as compressed_file:
                compressed_file.write(file_response.content)
            compressed_file.close()

            print(f'\nSuccesfully downloaded {filename}')

        except IOError as e:
            print(f'\n{e}')
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

            print(f'\nSuccesfully uncompressed {filename}')
        
        except (tarfile.TarError, zipfile.BadZipFile) as e:
            print(e)

        # remove the zip / tar.gz archive
        os.remove(filename)
    
    MKLITTLEFS_BIN_PATH = next((f'mklittlefs/mklittlefs{ext}' for ext in EXTENSIONS if os.path.exists(f'mklittlefs/mklittlefs{ext}')), None)

def make_littlefs_binary(channel=None):
    print(f'\nCreating {LITTLEFS_BIN_PATH}...')
    try:
        # if the deauth_settings.txt is foundin the data folder
        if DATA_FOLDER_FILES[0] == 'deauth_settings.txt':
            # modify deauth_settings.txt with the channel
            change_file_channel((str(channel)))

        cmd = [MKLITTLEFS_BIN_PATH, "-c", DATA_FOLDER, "-p", "256", "-b", "8192", "-s", "2072576", LITTLEFS_BIN_PATH]
        subprocess.run(cmd, capture_output=True, text=True) # run the above command to create the littlefs filesystem with the text file data
        print(f'\nSuccesfully created: {LITTLEFS_BIN_PATH} with {DATA_FOLDER_FILES[0]}')
    
    except subprocess.CalledProcessError as e:
        print(f'\nError: mklittlefs failed with exit code {e.returncode}')

    except FileNotFoundError:
        print(f'\nError: mklittlefs binary not found at {MKLITTLEFS_BIN_PATH}')

    except PermissionError:
        print(f'\nError: Permission denied when executing {MKLITTLEFS_BIN_PATH}')

def change_file_channel(channel):
    # read all lines in deauth_settings.txt
    file_lines = open(f'{DATA_FOLDER}deauth_settings.txt', 'r').readlines()
    # process the first line (channel=1) find the first number and replace that number with new channel
    file_lines[0] = re.sub(r'\d+', channel, file_lines[0], count=1)
    # write all lines including the changed channel line back to the file
    open(f'{DATA_FOLDER}deauth_settings.txt', 'w').writelines(file_lines)
    print(f'\nChanged {DATA_FOLDER_FILES[0]} channel to {channel}')
    
def upload_file_to_esp(esp, channel):   

    # if the deauth_settings.txt is found in the data folder
    if DATA_FOLDER_FILES[0] == 'deauth_settings.txt':
        # create a new littelfs binary with the channel
        make_littlefs_binary(channel)
        # increment the channel for the next esp
        channel+=1

    # for each esp attempt to upload twice 
    # (windows sometimes disconnects and reconnects COM ports when switching COM port so we try to upload again if it fails)
    for i in range(2):

        esptool_fmt = ''

        upload_error = f"A fatal error occurred: Could not open {esp}, the port is busy or doesn't exist."
        success_message = "Hash of data verified."

        esptool_format_map = {
            'win32': 'esptool',
            'darwin': 'esptool.py',
            'linux': 'esptool.py'}
        
        esptool_fmt = esptool_format_map[OS_PLATFORM]

        print(f'\nUploading {DATA_FOLDER_FILES[0]} to {esp}...\n')
        upload_cmd = [esptool_fmt, '--chip', CHIP, '--port', esp, '--baud', BAUD_RATE, 'write_flash', '2097152', LITTLEFS_BIN_PATH]
        # run the above command to upload the littlefs filesystem with the text data to the current esp in the array and capture the cmd output into a var
        output = subprocess.run(upload_cmd, capture_output=True, text=True) 
        # if the cmd output contains upload_error and the current iteration is 0
        if upload_error in output.stdout and i == 0:
            print('Trying once more...')
            # try again on the next iteraton (takes into account windows disconnnecting and reconnecting COM ports)     
            continue
        # if the cmd output contains upload_error and the iteration is not the first 
        elif upload_error in output.stdout and i < 0:
            # don't try again and terminate the program
            print(f'Failed to upload {DATA_FOLDER_FILES[0]} to {esp}...\n')
            exit(1)
        # else the file uploaded sucessfully. 
        elif success_message in output.stdout:
            # break out of the inner loop and move into the next esp in the outer loop
            print(f'Succesfully uploaded {DATA_FOLDER_FILES[0]} to {esp}\n')
            break
    print('-----------------------------------------------------------------------------')

    # only delete littefs.bin after each iteration for the deauther as the text file changes for every esp
    if DATA_FOLDER_FILES[0] == 'deauth_settings.txt':
        os.remove(LITTLEFS_BIN_PATH)

def check_serial_output(esp):
    print(f'\nChecking serial output for {esp}...\n')
    # setup serial connection for current esp
    ser = serial.Serial(esp, 115200, timeout=2)

    # disable data terminal ready (dtr) and request to send (rts)
    # as this interferes with the serial output
    ser.dtr = False
    ser.rts = False

    while True:
        # read the serial output one line at a time
        line = ser.readline().decode('utf-8', errors='replace').strip('\n')
        # skip printing the line if it contains any � symbols as this is boot code for the esp
        if '�' in line:
            continue
        # if the line output is empty we can terminate the serial connection
        if not line:
            ser.close()
            break
        
        # print the serial output line if none of the above conditions are met 
        print(line)

    print('\n-----------------------------------------------------------------------------')

# print out detected OS
print(f'\nDetected OS: {OS_PLATFORM}')

check_data_file()
get_mklittlefs_binary()

# if we are uploading to cam detector we only need to create mklittlefs binary once
if DATA_FOLDER_FILES[0] == 'macs.txt':
    make_littlefs_binary()
print('\n-----------------------------------------------------------------------------')

# filter to create a list of only usb com ports
esp_list = [esp for esp in list_ports.comports() if 'USB' in esp.hwid]

if not esp_list:
    print('\nNo ESP boards were detected, check you have plugged in your desired boards...\n')
    exit(1)

for i, esp in enumerate(esp_list, start=1):
    print(f'\nESP {i}/{len(esp_list)}: {esp.device}')
    print('\n-----------------------------------------------------------------------------')
    upload_file_to_esp(esp.device, i)
    check_serial_output(esp.device)

# remove littlefs if it hasn't already been deleted
if os.path.exists(LITTLEFS_BIN_PATH):
    os.remove(LITTLEFS_BIN_PATH)

print('\nUploads completed, please verify the serial output of each ESP is correct before deploying...\n')


