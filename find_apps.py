import os

root = r"D:\timetable_project"
print("Contents of project root:")
for item in sorted(os.listdir(root)):
    full = os.path.join(root, item)
    if os.path.isdir(full):
        print(f"  [DIR]  {item}")
    else:
        print(f"  [FILE] {item}")

print("\n--- Searching for 'school' anywhere in project ---")
for dirpath, dirnames, filenames in os.walk(root):
    # Skip venv
    if 'venv' in dirpath or '__pycache__' in dirpath:
        continue
    for d in dirnames:
        if 'school' in d.lower():
            print(f"  Found dir:  {os.path.join(dirpath, d)}")
    for f in filenames:
        if 'school' in f.lower() and f.endswith('.py'):
            print(f"  Found file: {os.path.join(dirpath, f)}")

print("\n--- Checking INSTALLED_APPS path ---")
import django
from django.conf import settings
print("Settings module:", settings.SETTINGS_MODULE)
print("Project root (from settings):", getattr(settings, 'BASE_DIR', 'NOT SET'))