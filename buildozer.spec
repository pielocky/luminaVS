[app]
title = Vision Assist
package.name = visionassist
package.domain = org.visionassist
source.dir = .
version = 1.0.0

# Критически важно: правильные версии для Android
requirements = python3,kivy==2.1.0,numpy==1.23.5,opencv-python-headless==4.5.5.64,pillow==9.5.0,pyzbar==0.1.9,gtts==2.3.1,playsound==1.2.2,android, android_numpy

orientation = portrait
fullscreen = 0

# Разрешения
android.permissions = CAMERA, INTERNET

# Версии SDK/NDK - ЭТО КЛЮЧЕВОЕ!
android.api = 30
android.minapi = 21
android.ndk = 25b
android.sdk = 30
android.ndk_version = 25b

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

# ===== НАСТРОЙКИ ДЛЯ СКАЧИВАНИЯ С РОССИЙСКИХ ЗЕРКАЛ =====
# Предварительная загрузка numpy с российских зеркал
pre-build = 
    # Создаем директорию для кеша
    mkdir -p ~/.buildozer/android/packages/numpy/
    mkdir -p ~/.buildozer/android/platform/python-for-android/pythonforandroid/recipes/numpy/
    
    # Скачиваем numpy с Яндекс зеркала (самое быстрое в РФ)
    echo "Скачиваем numpy с Яндекс зеркала..."
    wget --timeout=30 --tries=3 https://mirror.yandex.ru/pypi/packages/source/n/numpy/numpy-1.23.5.tar.gz \
         -O ~/.buildozer/android/packages/numpy/numpy-1.23.5.tar.gz || \
    wget --timeout=30 --tries=3 https://mirror.sbercloud.ru/pypi/packages/source/n/numpy/numpy-1.23.5.tar.gz \
         -O ~/.buildozer/android/packages/numpy/numpy-1.23.5.tar.gz || \
    wget --timeout=30 --tries=3 https://mirror.selectel.org/pypi/packages/source/n/numpy/numpy-1.23.5.tar.gz \
         -O ~/.buildozer/android/packages/numpy/numpy-1.23.5.tar.gz
    
    # Создаем маркерный файл
    touch ~/.buildozer/android/packages/numpy/.mark-numpy-1.23.5.tar.gz
    
    # Создаем кастомный рецепт numpy, который использует локальный файл
    cat > ~/.buildozer/android/platform/python-for-android/pythonforandroid/recipes/numpy/__init__.py << 'EOF'
from pythonforandroid.recipe import PythonRecipe
import shutil
import os
from pythonforandroid.logger import info

class NumpyRecipe(PythonRecipe):
    version = '1.23.5'
    url = 'https://mirror.yandex.ru/pypi/packages/source/n/numpy/numpy-{version}.tar.gz'
    depends = ['setuptools']
    
    def download_file(self, url, target, cwd=None):
        # Используем локальный файл из кеша
        cached_file = os.path.expanduser(f'~/.buildozer/android/packages/numpy/numpy-{self.version}.tar.gz')
        if os.path.exists(cached_file):
            info(f"Using cached numpy from {cached_file}")
            shutil.copyfile(cached_file, target)
            return True
        else:
            info(f"Downloading numpy from mirror")
            super().download_file(url, target, cwd)
    
    def get_recipe_dir(self):
        return os.path.dirname(__file__)

recipe = NumpyRecipe()
EOF

    # Патчим python-for-android для использования правильных URL
    find .buildozer/android/platform/python-for-android -type f -name "*.py" -exec sed -i 's/pypi.python.org/mirror.yandex.ru/g' {} \; 2>/dev/null || true
    find .buildozer/android/platform/python-for-android -type f -name "*.py" -exec sed -i 's/packages.python.org/mirror.yandex.ru/g' {} \; 2>/dev/null || true

# Настройки pip для использования российских зеркал
pre-build2 = 
    mkdir -p ~/.pip
    cat > ~/.pip/pip.conf << EOF
[global]
index-url = https://mirror.yandex.ru/pypi/simple
trusted-host = mirror.yandex.ru
EOF

# Очистка кеша если нужно
clean = 
    rm -rf ~/.buildozer/android/packages/numpy/
    rm -rf ./.buildozer/android/platform/build-arm64-v8a/packages/numpy

[buildozer]
log_level = 2
warn_on_root = 1
build_dir = ./.buildozer/
bin_dir = ./bin/