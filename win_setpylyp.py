import os

print("Installing pyinstaller")
print("...")
os.system("pip install pyinstaller")

print("Creating pylyp.exe")
print("...")
os.system("pyinstaller --onefile --exclude-module _bootlocale pylyp.py")
