import subprocess
import sys
import os
import requests
import tarfile
from zipfile import ZipFile 

# vars for generating littlefs binary
OS_PLATFORM = sys.platform
MKLITTLEFS_BIN_DIR = './mklittlefs'
FILE_DATA_FOLDER = './data'
LITTLEFS_BIN = ''

# vars for uploading file to esp
PORT = []
BAUD_RATE = '115200'
FLASH_ADDRESS = ''

def get_mklittlefs_binary():
    api_url = 'https://api.github.com/repos/earlephilhower/mklittlefs/releases/latest'
    platform_str = None
    download_url = None
    filename = None

    # check if mklittlefs binary or exe exists in current dir
    if any(os.path.isfile(f'{MKLITTLEFS_BIN_DIR}/mklittlefs{ext}') for ext in ['.bin', '.exe', '']):
        print('mklittlefs binary already present\n') 
        
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
            print(e,'\n')
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

            print('Succesfully downloaded ', filename,'\n')

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

            print('Succesfully uncompressed ', filename,'\n')
        
        except (tarfile.TarError, zipfile.BadZipFile) as e:
            print(e)

        # remove the zip / tar.gz archive
        os.remove(filename)

        

  
            

print('\nDetected OS:', OS_PLATFORM, '\n')

get_mklittlefs_binary()


# def make_littlefs_binary(os):

# def upload_file_to_esp():
