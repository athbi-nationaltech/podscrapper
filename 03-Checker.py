import argparse
import json
import os
import glob


directory2 = 'sayeralotaibi'
newDirectory = "Data/" + directory2 + "/json"
counter = 1
# try:
#     for filename in os.listdir(newDirectory):
#         if ".processed." in filename:
#             # print("Processed :: ", filename)
#             # print("----------------------------------")
#             continue
#         else:
#             print("Not processed :: ", filename)
#             print("----------------------------------")
# except FileNotFoundError:
#     print(f"Directory not found: {newDirectory}")
# except PermissionError:
#     print(f"Permission denied to access directory: {newDirectory}")


 
newFile = "3OfocZZnyI82"
os.chdir(newDirectory)
for file in glob.glob('*'+newFile+'*'):
    print(file)
    print("----------------------------------")
    break
else:
    print("No files found ", newFile)
