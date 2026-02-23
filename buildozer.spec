[app]

# (str) Title of your application
title = Vision Assist

# (str) Package name
package.name = visionassist

# (str) Package domain (needed for android)
package.domain = org.example

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (patterns)
source.include_exts = py,png,jpg,kv,atlas,txt,ttf

# (list) Source files to exclude
source.exclude_exts = spec

# (list) List of inclusions to use
source.inclusions = ./templates

# (list) Application requirements
requirements = python3,kivy==2.1.0,opencv-python-headless==4.5.5.64,numpy==1.22.4,easyocr==1.6.2,pyzbar==0.1.9,gtts==2.3.1,playsound==1.3.0,android,Pillow==9.5.0

# (list) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen
fullscreen = 0

# (list) Permissions for Android
android.permissions = CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET

# (int) Android API level to use
android.api = 31

# (int) Minimum API level
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 31

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use Android's private storage instead of external storage
android.private_storage = True

# (str) The Android arch to build for
android.arch = arm64-v8a

# (bool) If True, then automatically accept SDK licenses
android.accept_sdk_license = True

# (list) The Android Gradle dependencies to use (for zbar)
android.gradle_dependencies = 'me.zhanghai.android.libzbar:library:1.3.0'

# (list) Additional libraries to compile with android
android.recipes = zbar

# (bool) If True, then the APK will be debuggable (adb logcat works)
android.debug = False

# (str) The version name of the app
android.version_name = 0.1

# (int) The version code of the app
android.version_code = 1

# (bool) If True, then buildozer will build the APK in release mode
android.release = True