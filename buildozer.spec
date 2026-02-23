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

# (list) List of inclusions to use (list of directories with files)
source.inclusions = ./templates

# (list) Application requirements
# ⚠️ ВНИМАНИЕ: easyocr требует torch и torchvision, что сильно увеличит размер APK
# и может вызвать ошибки сборки. Если столкнётесь с проблемами, попробуйте заменить
# easyocr на более лёгкое решение (например, tesseract или ML Kit).
requirements = python3,kivy==2.1.0,opencv-python-headless==4.5.5.64,numpy==1.22.4,easyocr==1.6.2,pyzbar==0.1.9,gtts==2.3.1,playsound==1.3.0,android,Pillow==9.5.0

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

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

# (str) The Android arch to build for (armeabi-v7a, arm64-v8a, x86, x86_64)
android.arch = arm64-v8a

# (bool) If True, then automatically accept SDK licenses
android.accept_sdk_license = True

# (list) The Android Gradle dependencies to use
# Для поддержки zbar (используется pyzbar) добавляем библиотеку
android.gradle_dependencies = 'me.zhanghai.android.libzbar:library:1.3.0'

# (list) Additional libraries to compile with android
# Если pyzbar не находит libzbar, добавьте рецепт:
android.recipes = zbar

# (bool) If True, then the APK will be debuggable (adb logcat works)
android.debug = False

# (str) The version name of the app
android.version_name = 0.1

# (int) The version code of the app
android.version_code = 1

# (bool) If True, then buildozer will build the APK in release mode
android.release = True

# (str) The keystore to use for signing the APK (if not set, debug keystore will be used)
#android.keystore = ~/.buildozer/android/platform/keystore.jks

# (str) The keystore alias
#android.keystore_alias = mykey

# (str) The keystore password
#android.keystore_pass = mypass

# (str) The key password
#android.key_pass = mypass

# (bool) If True, then buildozer will try to copy the python for android distribution to the build directory
#android.copy_dists = False

# (list) The architectures to build for
#android.archs = armeabi-v7a, arm64-v8a

# (str) The version of the NDK to use
#android.ndk_version = 25b

# (str) The version of the SDK to use
#android.sdk_version = 31

# (str) The version of the build tools to use
#android.build_tools_version = 30.0.3

# (str) The package name for the Java class for the activity
#android.package_name = org.example.visionassist

# (bool) If True, then enable multidex support
#android.multidex = False

# (bool) If True, then the app will be built with support for AndroidX
#android.use_androidx = True

# (list) The AndroidX dependencies to use
#android.androidx_dependencies = androidx.core:core:1.6.0, androidx.appcompat:appcompat:1.3.1

# (str) The orientation of the app (portrait, landscape, sensor)
#android.orientation = portrait

# (bool) If True, then the app will be built with support for the camera API
#android.camera = True

# (bool) If True, then the app will be built with support for the storage
#android.storage = True

# (list) Permissions to request for the app
#android.permissions = CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET

# (bool) If True, then the app will be built with support for the microphone
#android.microphone = False

# (bool) If True, then the app will be built with support for the vibration
#android.vibration = False

# (bool) If True, then the app will be built with support for the sensors
#android.sensors = False

# (bool) If True, then the app will be built with support for the location
#android.location = False

# (bool) If True, then the app will be built with support for the bluetooth
#android.bluetooth = False

# (bool) If True, then the app will be built with support for the nfc
#android.nfc = False

# (bool) If True, then the app will be built with support for the usb
#android.usb = False

# (bool) If True, then the app will be built with support for the flashlight
#android.flashlight = False

# (str) The path to a custom AndroidManifest.xml template
#android.manifest = %(source.dir)s/android/AndroidManifest.xml

# (str) The path to a custom build.gradle template
#android.gradle = %(source.dir)s/android/build.gradle

# (str) The path to a custom activity
#android.activity = org.kivy.android.PythonActivity

# (list) Additional Java classes to add as activities
#android.add_activity =

# (list) Additional Java classes to add as services
#android.add_service =

# (list) Additional Java classes to add as receivers
#android.add_receiver =

# (list) Additional Java files to include
#android.add_src =

# (list) The libraries to link against
#android.libraries =

# (list) The repositories to add to gradle
#android.gradle_repositories =

# (bool) If True, then buildozer will try to compile the python for android distribution from source
#android.download_deps = False

# (bool) If True, then buildozer will not try to update the android dependencies
#android.no_update_libs = False

# (bool) If True, then the APK will be debuggable (adb logcat works)
android.debug = False

# (str) The logcat filter to use
#android.logcat_filters = *:S Python:V

# (bool) If True, then buildozer will try to copy the python for android distribution to the build directory
#android.copy_dists = False