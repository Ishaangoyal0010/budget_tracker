[app]

# (str) Title of your application
title = PennyWise

# (str) Package name
package.name = pennywise

# (str) Package domain (needed for android packaging)
package.domain = org.pennywise

# (str) Source code directory where main.py resides
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,db

# (str) Application version
version = 1.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3==3.10.14,kivy,pyjnius,sqlite3

# (str) Supported orientations
# Valid values are: landscape, portrait, all
orientation = portrait

# (list) Permissions
# Request permissions to intercept SMS and send notification alerts
android.permissions = android.permission.RECEIVE_SMS, android.permission.READ_SMS, android.permission.POST_NOTIFICATIONS

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use private storage for data (needed for database storage)
android.private_storage = True

# (list) List of service to declare (leave empty if none)
# services = 

# (str) Icon of the application
# icon.filename = %(source.dir)s/icon.png

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/presplash.png

# (list) Android logcat filters
# android.logcat_filters = *:S python:D

# (bool) Copy library instead of linking (needed on Windows/macOS builds)
# android.copy_libs = 1

# (list) The Android archs to build for
android.archs = armeabi-v7a, arm64-v8a

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
