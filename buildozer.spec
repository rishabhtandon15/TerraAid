[app]

# (str) Title of your application
title = TerraAid

# (str) Package name
package.name = terraaid

# (str) Package domain (needed for android/ios packaging)
package.domain = org.terraaid

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,md,txt

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, .venv_py311, .venv_windows, build, .buildozer, cache

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,kivy_garden.mapview,requests,urllib3,idna,chardet,certifi,pillow,numpy

# (list) Garden requirements
garden_requirements = mapview

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
permissions = CAMERA, INTERNET, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (int) Target Android API, should be high enough to support recent Android versions
android.api = 33

# (int) Minimum API your APK will support
android.minapi = 21

# (str) Android NDK version
android.ndk = 25b

# (bool) If True, then skip try to update the Android sdk tool
android.skip_update = False

# (bool) If True, then accept all SDK licenses automatically
android.accept_sdk_license = True

# (str) Android entry point, default is ok for Kivy-based app
android.entrypoint = org.kivy.android.PythonActivity

# (bool) Enable AndroidX support. Required when targeting API 28+
android.enable_androidx = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = error, 1 = warning, 2 = ignore)
warn_on_root = 1
