[app]

# (str) Title of your application
title = Vision Assist

# (str) Package name
package.name = visionassist

# (str) Package domain (необязательно, но рекомендуется)
package.domain = org.visionassist

# (str) Source directory where your main.py is
source.dir = .

# (list) Source files to include (расширения файлов)
source.include_exts = py,png,jpg,kv,atlas,txt

# (str) Version of your application
version = 1.0.0

# (list) Requirements - Python packages (ВАЖНО: разделяются запятыми)
requirements = python3,kivy==2.1.0,opencv-python-headless==4.5.5.64,numpy==1.22.4,pillow==9.5.0,pyzbar==0.1.9,gtts==2.3.1,playsound==1.2.2,android

# (str) Orientation of the app (portrait, landscape, etc.)
orientation = portrait

# (bool) Fullscreen mode
fullscreen = 0

# (list) Permissions for Android
android.permissions = CAMERA, INTERNET, RECORD_AUDIO

# (int) Android minimum API version (Android 5.0)
android.minapi = 21

# (int) Android target API version
android.api = 30

# (str) Android NDK version
android.ndk = 23b

# (int) Android SDK version
android.sdk = 30

# (bool) Auto accept SDK licenses
android.accept_sdk_license = True

# (list) Android architectures to build for
android.archs = arm64-v8a

# (str) Path to your icon (optional)
# icon.filename = %(source.dir)s/icon.png

# (str) Path to your splash screen (optional)
# presplash.filename = %(source.dir)s/splash.png

[buildozer]

# (int) Log level (0=quiet, 1=info, 2=debug)
log_level = 2

# (bool) Warn if running as root
warn_on_root = 1

# (str) Path to build directory
build_dir = ./.buildozer/

# (str) Path to bin directory (where APK will be)
bin_dir = ./bin/