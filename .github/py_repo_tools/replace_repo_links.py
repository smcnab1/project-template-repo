# Python program to read
# json file
import os
import json
import datetime
import subprocess

# Get the current working directory
current_directory = os.getcwd()

# Execute the git command to get the remote origin URL
git_command = "git config --get remote.origin.url"
git_url = subprocess.check_output(git_command, shell=True, text=True).strip()

# Extract the repository name from the Git URL
repository_name = git_url.split("/")[-1].replace(".git", "")

# If the repository name is not found in the Git URL, use a default value
New_Repo_Name = repository_name if repository_name else "project-template-repo"

# Format the repository name as "smcnab1/New_Repo_Name"
Text_To_Replace_With = f"smcnab1/{New_Repo_Name}"

# Opening JSON file
f = open('.github/py_repo_tools/repo_config.json')
  
# returns JSON object as 
# a dictionary
config = json.load(f)

# Define the filename here you want to replace content in
FileName = "README.md"

Text_To_Replace = config['Text_To_Replace']

Date_To_Replace = "DATE"

current_date = datetime.datetime.now().strftime("%d %b %y")

# Closing file
f.close()


# Open the File
with open(FileName, 'r') as f:
    # Read the file contents
    contents = f.read()
    # Replace the file contents
    contents = contents.replace(Text_To_Replace, Text_To_Replace_With)
    contents = contents.replace(Date_To_Replace, current_date)

# Write the file out    
with open(FileName, 'w') as f:
    # Write the updated contents
    f.write(contents)  
