import os

from tools import append_file_to_wkng_dir

print(os.getcwd())
append_file_to_wkng_dir("file.txt", "Hello World")
