import os
import sys
import urllib.request
import zipfile
import tempfile
import shutil

REPO_URL = "https://github.com/iavhsofficial/salary-manager/archive/refs/heads/main.zip"
VERSION_FILE = "current_version.txt"

def get_latest_version():
    try:
        req = urllib.request.Request(REPO_URL, method="HEAD")
        with urllib.request.urlopen(req) as response:
            return response.headers.get("ETag", "unknown")
    except Exception:
        return "unknown"

def main():
    latest = get_latest_version()
    current = ""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            current = f.read().strip()

    if latest != current and latest != "unknown":
        print("Naya version mil raha hai...")
        try:
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "latest.zip")
            urllib.request.urlretrieve(REPO_URL, zip_path)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                
            extracted_folder = os.path.join(temp_dir, "salary-manager-main")
            
            for item in os.listdir(extracted_folder):
                s = os.path.join(extracted_folder, item)
                d = os.path.join(os.getcwd(), item)
                if os.path.isdir(s):
                    if os.path.exists(d): shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
                    
            with open(VERSION_FILE, "w") as f:
                f.write(latest)
        except Exception as e:
            pass # Agar internet na ho toh bhi software chalta rahe

    # Ab hum main.py ko import kar ke chalayenge (jo pehle test mein kamyab hua)
    import main

if __name__ == "__main__":
    main()