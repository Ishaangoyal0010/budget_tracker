import os
import subprocess
import sys

def print_banner():
    print("=" * 60)
    print("      PENNYWISE SMS TRANSACTION TRACKER SIMULATOR")
    print("=" * 60)
    print("\nHow to run and test locally:")
    print("1. Install Kivy on your machine:")
    print("   pip install kivy")
    print("\n2. Run this script or main.py directly:")
    print("   python main.py")
    print("\n3. In the application UI:")
    print("   - You will see a 'TOTAL MONTHLY SPEND' card.")
    print("   - You will see an 'SMS SIMULATOR' input text panel at the bottom.")
    print("   - Paste any typical Indian bank UPI transaction SMS inside the input box.")
    print("   - Click 'Send Simulated SMS to App'.")
    print("   - Notice the amount, date, and clean name are auto-parsed.")
    print("   - Because the merchant name is unknown, a 'Categorize Unknown Merchant' card appears.")
    print("   - Enter a clean name (e.g. 'Ramesh Kirana Store') and a category (e.g. 'Groceries').")
    print("   - Click 'Save Mapping'. The card disappears and the list updates.")
    print("   - Try sending another simulated SMS with the SAME merchant name (e.g. 'RAMESH KUMAR').")
    print("   - It will auto-categorize instantly without prompting again!")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    print_banner()
    
    # Launch main.py
    try:
        import kivy
        print("Launching PennyWise App...")
        # Execute main.py
        os.system("python main.py")
    except ImportError:
        print("\n[WARNING] Kivy is not installed. To run the simulator, please run:")
        print("   pip install kivy")
        print("\nOnce installed, start the app with: python main.py")
        input("\nPress Enter to exit...")
