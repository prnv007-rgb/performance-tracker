import os

file_path = "C:/Users/prana/OneDrive/Desktop/ts.json"

# Check if the file is accessible
if os.access(file_path, os.R_OK):
    print("Python has read permission for the file.")
else:
    print("Python does NOT have read permission for the file.")
