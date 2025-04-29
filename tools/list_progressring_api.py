from PyQt5.QtWidgets import QApplication
import sys
import inspect
from qfluentwidgets import ProgressRing

# Initialize QApplication (required for Qt applications)
app = QApplication(sys.argv)

# Get ProgressRing class
pr_class = ProgressRing

# Print class information
print("=== ProgressRing Class Information ===")
print(f"Class Name: {pr_class.__name__}")
print(f"Base Classes: {pr_class.__bases__}")
print("\n=== Methods ===")

# Get methods
methods = inspect.getmembers(pr_class, predicate=inspect.isfunction)
for name, method in methods:
    if not name.startswith('__'):  # Filter out special methods
        try:
            signature = inspect.signature(method)
            print(f"{name}{signature}")
        except:
            print(f"{name}()")

# Create an instance to check instance methods and properties
pr_instance = ProgressRing()

print("\n=== Instance Methods ===")
instance_methods = [m for m in dir(pr_instance) if callable(getattr(pr_instance, m)) and not m.startswith('__')]
for method in instance_methods:
    if method not in [m[0] for m in methods]:  # Don't duplicate methods from class
        try:
            attr = getattr(pr_instance, method)
            signature = inspect.signature(attr)
            print(f"{method}{signature}")
        except:
            print(f"{method}()")

print("\n=== Properties ===")
properties = [p for p in dir(pr_instance) if not callable(getattr(pr_instance, p)) and not p.startswith('__')]
for prop in properties:
    try:
        value = getattr(pr_instance, prop)
        print(f"{prop}: {type(value).__name__}")
    except:
        print(f"{prop}: <Unable to get type>")

# Exit the application
sys.exit(0) 