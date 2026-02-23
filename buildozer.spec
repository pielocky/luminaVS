[app]

title = Vision Assist
package.name = visionassist
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,ttf
source.exclude_exts = spec
source.inclusions = ./templates
version = 0.1

requirements = python3,kivy==2.1.0,opencv-python-headless==4.5.5.64,numpy==1.22.4,pyzbar==0.1.9,gtts==2.3.1,playsound==1.3.0,android,Pillow==9.5.0

orientation = portrait
fullscreen = 0

android.permissions = CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET
android.api = 31
android.minapi = 21
android.sdk = 31
android.ndk = 25b
android.private_storage = True
android.arch = arm64-v8a
android.accept_sdk_license = True
android.gradle_dependencies = 'me.zhanghai.android.libzbar:library:1.3.0'
android.recipes = zbar
android.debug = False
android.version_code = 1
android.release = True