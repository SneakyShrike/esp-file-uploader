import subprocess
import sys
import os
import re
import requests
import tarfile
from zipfile import ZipFile 

# vars for generating littlefs binary
EXTENSIONS = ['.bin', '.exe', '']
OS_PLATFORM = sys.platform
MKLITTLEFS_BIN_PATH = None
DATA_FOLDER = 'data/'
DATA_FOLDER_FILES = os.listdir(DATA_FOLDER)
LITTLEFS_BIN_PATH = 'littlefs.bin'

# vars for uploading file to esp
ESP_ARRAY = [] # each plugged in esp name will be stored in an array
CHIP = 'esp8266'
BAUD_RATE = '115200'

def check_data_file():

    text_files = ['macs.txt', 'deauth_settings.txt']

    # check if DATA_DIRECTORY exists
    if not os.path.isdir(DATA_FOLDER):
        print(f'\n{DATA_FOLDER} folder not found, please create this directory...')
        exit(1)

    visible_files = [file for file in DATA_FOLDER_FILES if not file.startswith('.') and os.path.isfile(os.path.join(DATA_FOLDER, file))]

    if len(visible_files) != 1:
        print(f'\n{DATA_FOLDER} folder is either empty or contains more than 1 file...')
        exit(1)

    file = visible_files[0]
    if file not in text_files:
        print(f'\n{DATA_FOLDER} folder should only contain ONE of the following: {text_files}')
        exit(1)
    
    print(f'\n{file} found in {DATA_FOLDER} folder...')

def upload_options():

    while True:
        user_choice = input('\nChoose an ESP project to upload to: \n1: DEAUTHER\n2: CAM-DETECTOR\n:')
        global ESP_TYPE

        if user_choice != '1' or user_choice != '2':
            print('Error: Invalid Option! Please choose 1 or 2!')
            continue
        if user_choice == '1':
            ESP_TYPE = 'DEAUTHER'
            break
        elif user_choice == '2':
            ESP_TYPE = 'CAM-DETECTOR'
            break

def get_mklittlefs_binary():

    global MKLITTLEFS_BIN_PATH
    api_url = 'https://api.github.com/repos/earlephilhower/mklittlefs/releases/tags/2.5.1-1' # the mklittlefs binary must be 2.5.1-1 because the deauther board core is on an earlier verison of Ardunio core
    platform_str = None
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

def make_littlefs_binary():
    print(f'\nCreating {LITTLEFS_BIN_PATH}...')
    try:
        cmd = [MKLITTLEFS_BIN_PATH, "-c", DATA_FOLDER, "-p", "256", "-b", "8192", "-s", "2072576", LITTLEFS_BIN_PATH]
        subprocess.run(cmd, capture_output=True, text=True) # run the above command to create the littlefs filesystem with the text file data
        print(f'\nSuccesfully created: {LITTLEFS_BIN_PATH} with {DATA_FOLDER_FILES[0]}')
    
    except subprocess.CalledProcessError as e:
        print(f'\nError: mklittlefs failed with exit code {e.returncode}')

    except FileNotFoundError:
        print(f'\nError: mklittlefs binary not found at {MKLITTLEFS_BIN_PATH}')

    except PermissionError:
        print(f'\nError: Permission denied when executing {MKLITTLEFS_BIN_PATH}')

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

def change_file_channel(channel):
    # read all lines in deauth_settings.txt
    file_lines = open(f'{DATA_FOLDER}deauth_settings.txt', 'r').readlines()
    # process the first line (channel=1) find the first number and replace that number with new channel
    file_lines[0] = re.sub(r'\d+', channel, file_lines[0], count=1)
    # write all lines including the changed channel line back to the file
    open(f'{DATA_FOLDER}deauth_settings.txt', 'w').writelines(file_lines)
    print(f'\nChanged {DATA_FOLDER_FILES[0]} channel to {channel}')
    
def upload_file_to_esp():
    # if the esp array is empty
    while True:
        if not ESP_ARRAY:
            print('\nNo ESP boards were detected, check you have plugged in your desired boards...')
            continue
        break

    #  if we're uploading files to a deauther ESP
    if DATA_FOLDER_FILES[0] == 'deauth_settings.txt':
    # if ESP_TYPE == 'DEAUTHER':
        # populate channel array to match how many ESP boards are plugged in
        channel_array = list(range(1,len(ESP_ARRAY)+1))
        index = 0
        current_channel = str(channel_array[index])
        print(channel_array)
    # loop through the esp array and for each esp
    for esp in ESP_ARRAY:
        # if files are being uploaded to the deauther
        if DATA_FOLDER_FILES[0] == 'deauth_settings.txt':
        # if ESP_TYPE == 'DEAUTHER':
            # change the files channel starting at index 0 of the channel_array
            change_file_channel(current_channel)
            # increment index so next channel is added to next esp file upload in loop
            index = index+1
            print(index)
        print(f'\nUploading {DATA_FOLDER_FILES[0]} to ESP: {esp}')
        cmd = ['esptool.py', '--chip', CHIP, '--port', f'/dev/{esp}', '--baud', BAUD_RATE, 'write_flash', '2097152', LITTLEFS_BIN_PATH]
        subprocess.run(cmd) # run the above command to upload the littlefs filesystem with the text data to the current esp in the array
      
print(f'\nDetected OS: {OS_PLATFORM}')
print(f'\nPlease plug in your ESP boards...')

check_data_file()
# upload_options()
pop_esp_array()
get_mklittlefs_binary()
make_littlefs_binary()
upload_file_to_esp()
