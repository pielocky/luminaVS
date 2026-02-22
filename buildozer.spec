[app]
# (str) Title of your application
title = Vision Assist

# (str) Package name (unique identifier)
package.name = visionassist

# (str) Package domain (usually your website or GitHub)
package.domain = org.example

# (str) Source directory where your main.py is
source.dir = .

# (str) Version of your app
version = 1.0.0

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,txt

# (list) Requirements (Python packages)
requirements = python3,kivy==2.1.0,opencv-python-headless==4.5.5.64,numpy==1.22.4,pillow==9.5.0,pyzbar==0.1.9,gtts==2.3.1,playsound==1.2.2,android

# (str) Orientation of the app
orientation = portrait

# (bool) Full screen mode
fullscreen = 0

# (list) Android permissions
android.permissions = CAMERA, INTERNET

# (int) Android minimum API level
android.minapi = 21

# (int) Android target API level
android.api = 30

# (str) Android NDK version
android.ndk = 23b

# (int) Android SDK version
android.sdk = 30

# (bool) Accept SDK license
android.accept_sdk_license = True

# (list) Android architectures to build for
android.archs = arm64-v8a

[buildozer]
# (int) Log level (0-2)
log_level = 2

# (bool) Warn when running as root
warn_on_root = 1

# (str) Path to build directory
build_dir = ./.buildozer/

# (str) Path to bin directory
bin_dir = ./bin/