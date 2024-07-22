"""
Automatically build AlphaSeg software from source scripts and dependencies.
This script only works in Windows OS.

Args:
    source_dir: directory of repository (should contain main.py)
    build_dir: directory where the built software stores

Returns:
    Executable in build_dir
"""

import subprocess
import sys
import os
import shutil


def build_gui(source_dir, build_dir, env_name):
    # Ensure working in root directory
    os.chdir(os.path.expanduser("~"))
    BAT_NAME = os.path.join(os.getcwd(), "build_alphaseg.bat")

    # Check whether appropriate number of arguments is supplied
    if len(sys.argv) < 4:
        print(f"Not enough arguments. Expect 3, got {len(sys.argv) - 1}.")
        sys.exit()
    elif len(sys.argv) > 4:
        print(f"Too many arguments. Expect 3, got {len(sys.argv - 1)}.")
        sys.exit()
    else:
        # Check whether the supplied directories exist
        # Check existence of source directory
        if not os.path.exists(source_dir):
            print(f"Source directory ({source_dir}) does not exist.")
            sys.exit()
        # Check existence of "main.py" in source directory
        if "main.py" not in os.listdir(source_dir):
            print(f"No file named \"main.py\" in the source directory ({source_dir}).")
            sys.exit()
        # Check existence of build directory
        if not os.path.exists(build_dir):
            print(f"Build directory ({build_dir}) does not exist.")
            print("Attempt to create build directory...")
            os.makedirs(build_dir)
            print(f"Build directory ({build_dir}) created.")
        # Check complete
        print("Check completed. Ready to build.")

        # Delete any existing BAT file
        if os.path.exists(BAT_NAME):
            os.remove(BAT_NAME)
        # Create BAT for generating executable using pyinstaller
        with open(BAT_NAME, 'w+') as f:
            f.write(source_dir[0:2] + "\n")
            f.write("cd " + source_dir + "\n")
            f.write(f"call activate {env_name}" + "\n")
            f.write("pyinstaller main.py" + "\n")
            f.close()
        # Call the BAT file
        subprocess.call(BAT_NAME)
        # Move the build to build directory
        shutil.move(f"{source_dir}/build", f"{build_dir}")
        shutil.move(f"{source_dir}/dist", f"{build_dir}")
        shutil.move(f"{source_dir}/main.spec", f"{build_dir}")
        # Delete the BAT file
        if os.path.exists(BAT_NAME):
            os.remove(BAT_NAME)
        print("Finished.")

if __name__ == '__main__':
    build_gui(sys.argv[1], sys.argv[2], sys.argv[3])
