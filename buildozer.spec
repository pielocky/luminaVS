[app]
title = Vision Assist
package.name = visionassist
package.domain = org.visionassist
source.dir = .
version = 1.0.0

# Критически важно: правильные версии для Android
requirements = python3,kivy==2.1.0,numpy==1.19.5,opencv-python-headless==4.5.5.64,pillow==9.5.0,pyzbar==0.1.9,gtts==2.3.1,playsound==1.2.2,android, android_numpy

orientation = portrait
fullscreen = 0

# Разрешения
android.permissions = CAMERA, INTERNET

# Версии SDK/NDK - ЭТО КЛЮЧЕВОЕ!
android.api = 30
android.minapi = 21
android.ndk = 23b
android.sdk = 30
android.ndk_version = 23b

# Важные настройки для сборки
android.accept_sdk_license = True
android.archs = arm64-v8a
android.ndk_compiler = clang
android.gradle_dependencies = 'com.google.android.gms:play-services-vision:20.1.3'

# Специальные рецепты для numpy и opencv
android.add_src = 
android.recipes = numpy, opencv

# Увеличиваем время сборки
android.timeout = 3600

[buildozer]
log_level = 2
warn_on_root = 1
build_dir = ./.buildozer/
bin_dir = ./bin/