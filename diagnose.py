import os
import sys

print("Current directory:", os.getcwd())
print("\nPython sys.path:")
for i, p in enumerate(sys.path):
    print(f"  {i}: {p}")

print("\n--- Looking for 'schools' folder ---")
for p in sys.path:
    candidate = os.path.join(p, 'schools')
    if os.path.exists(candidate):
        print(f"\nFound: {candidate}")
        print("Contents:", os.listdir(candidate))
        init_file = os.path.join(candidate, '__init__.py')
        print("__init__.py exists:", os.path.exists(init_file))
        
        models_file = os.path.join(candidate, 'models.py')
        print("models.py exists:", os.path.exists(models_file))

print("\n--- Trying to import schools ---")
try:
    import schools
    print("SUCCESS! schools found at:", schools.__file__)
except Exception as e:
    print("FAILED:", type(e).__name__, e)