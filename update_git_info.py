import subprocess
import shutil
import os

project_root = ""
test_branch= "test_builds"

def update_git_info():
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip().decode()[:7]
    date = subprocess.check_output(["git", "show", "-s", "--format=%ci", "HEAD"]).strip().decode()[:19]
    branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip().decode()

    # Create the header file
    header = f"""// GitInfo.h
    // This is an automatically generated header file that contains information about the git commit that can be used a runtime.
    // This file is created by update_git_info.py and is called as a PRE script in platformio.ini
    #ifndef __GITINFO__
    #define __GITINFO__
    
    extern const char* GitSHA;
    extern const char* GitDate;
    extern const char* GitBranch;
    
    #endif """
    with open("GitInfo.h", "w") as f1:
        for line in header.split("\n"):
            f1.write(line.strip() + "\n")

    # Create the Implementation File
    implemementation = f"""#include "GitInfo.h"
    
    const char* GitSHA = "{sha}";
    const char* GitDate =  "{date}";
    const char* GitBranch =  "{branch}";"""
    with open("./GitInfo.cpp", "w") as f2:
        for line in implemementation.split("\n"):
            f2.write(line.strip() + "\n")

def copytree(src, dst, symlinks=False, ignore=None, exist_ok=True):
    if not os.path.exists(dst):
        os.makedirs(dst, exist_ok=exist_ok)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore, exist_ok)
        else:
            shutil.copy2(s, d)

# Copy files to destination folder, keeping folder structure of source files. Returns the list of destination files with path
def copy_file_with_path(dest_file, src_file):
    if os.path.isdir(src_file):
        copytree(src_file, dest_file)
    else:
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
        shutil.copy2(src_file, dest_file)


# Record the current branch
current_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip().decode()

# Create the test branch if it doesn't exist
try:
    subprocess.check_call(["git", "rev-parse", "--verify", test_branch, "-q"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except subprocess.CalledProcessError:
    subprocess.check_call(["git", "branch", test_branch])

# Get the list of changed and new untracked files keep full path
# status_output = subprocess.check_output(["git", "status", "--porcelain"]).decode("utf-8") #TODO this doesn't work, need to do a git diff between current and test_builds
diff_output = subprocess.check_output(["git", "diff", "--name-status", test_branch]).decode()
diff_lines = diff_output.split("\n")

class File:
    def __init__(self):
        self.abspath = ""
        self.relpath = ""
        self.temppath = ""
    def __init__(self, abspath, relpath):
        self.abspath = abspath
        self.relpath = relpath
        self.temppath = ""

new_and_modified_files = []
deleted_files = []
renamed_files = []
for line in diff_lines:
    file_name = line[2:].strip()
    file = File(os.path.join(project_root, file_name), file_name)

    if line.startswith(("A", "C", "M", "T", "U")): # Added, Copied, Modified, Type Change, Unmerged (Ignoring unknown)
        new_and_modified_files.append(file)
    elif line.startswith(("D")): # Deleted
        deleted_files.append(file)
    elif line.startswith(("R")): # Renamed TODO: Handle renames
        renamed_files.append(file)

print("New and Modified files:")
if len(new_and_modified_files) > 0:
    for file in new_and_modified_files:
        print(f' - abspath: {file.abspath}   relpath: {file.relpath}')
else:
    print(' - NONE')

print("Deleted files:")
if len(deleted_files) > 0:
    for file in deleted_files:
        print(f' - abspath: {file.abspath}   relpath: {file.relpath}')
else:
    print(' - NONE')

print("Renamed files:")
if len(renamed_files) > 0:
    for file in renamed_files:
        print(f' - abspath: {file.abspath}   relpath: {file.relpath}')
else:
    print(' - NONE')

    
######################################################

# result = subprocess.run(['git', 'ls-files', '-m', '-o', '--exclude-standard'], stdout=subprocess.PIPE)
# files = result.stdout.decode().strip().split('\n')

# result = subprocess.run(['git', 'ls-files', '-d'], stdout=subprocess.PIPE)
# deleted_files2 = result.stdout.decode().strip().split('\n')

# new_and_modified_files2 = []
# for elem in files:
#     if elem not in deleted_files:
#         new_and_modified_files2.append(elem)

# # print("All files:")
# # for path in files:
# #     print(" - " + path)

# print("New and Modified files:")
# for path in new_and_modified_files2:
#     print(" - " + path)

# print("Deleted files:")
# for path in deleted_files2:
#     print(" - " + path)

###################################################################


# Copy the files to a temp folder
temp_folder = 'gitinfo_temp_folder'
if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)

print("Copied Files:")
for file in new_and_modified_files:
    file.temppath = os.path.join(temp_folder, file.relpath)
    copy_file_with_path(file.temppath, file.abspath)
    print(f' - temppath: {file.temppath}')

# Stash and change branch
subprocess.check_call(["git", "stash", "push", "--include-untracked"]) #stash the changes
try:
    subprocess.check_call(["git", "checkout", "test_builds"])
except:
    subprocess.check_call(["git", "checkout", "-b", "test_builds"])

# Paste the files back to their original locations
print("Placing Copied files back into position:")
for file in new_and_modified_files:
    temp_abs_path = os.path.abspath(file.temppath)
    copy_file_with_path(file.abspath, temp_abs_path)
    print(f' - temppath: {temp_abs_path}    abspath: {file.abspath}')

# Delete deleted files
if len(deleted_files) > 0:
    print("Deleting Files:")
    for file in deleted_files:
        if os.path.exists(file.abspath):
            os.remove(file.abspath)
            print(f'DELETED: {file.abspath}')
        else:
            print(f'FAILED: {file.abspath}')

# Commit changes to the test_builds branch
subprocess.check_call(["git", "add", "--all"]) # add any untracked files
subprocess.check_call(["git", "commit", "-a", "-m", f'Automatic build commit (from "{current_branch}")']) # commit the changes the test_builds branch

# Generate git info
update_git_info()

# Change back to original branch
subprocess.check_call(["git", "checkout", current_branch]) # go back to the original branch

# Unstash changes
subprocess.check_call(["git", "stash", "pop", "-q"]) # add the stashed changes back to the original branch and remove from the list

# Delete the temporary folder
print("Cleaning up temporary files:")
if os.path.exists(temp_folder):
    shutil.rmtree(temp_folder)