# loop over all the required dependencies in requirements.txt
# install them into the Scripts sims_tik_tok_mod/libs folder using pip install <dependency> --target ./libs

if __name__ == "__main__":
    import os
    import sys
    import subprocess

    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Install dependencies
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", f"{current_dir}/requirements.txt", "--target", current_dir])
    
    print("Dependencies installed successfully!")
    print("You can now run the Sims 4 mod.")