import os
import shutil

def setup_dir(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)
        print(f"Directory '{dirname}' created.")
    else:
        print(f"Directory '{dirname}' already exists.")

def clean_dir(dirname):
    if not os.path.exists(dirname):
        return
    else:
        shutil.rmtree(dirname)
        print(f"Directory deleted.")