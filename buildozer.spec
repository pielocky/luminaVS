[app]
# Заголовок приложения
title = LuminaVS

# Имя пакета (должно быть уникальным)
package.name = luminavision

# Домен пакета (обычно ваш сайт или github)
package.domain = org.example

# Исходная директория
source.dir = .

# Расширения файлов для включения
source.include_exts = py,png,jpg,kv,atlas,txt

# Версия приложения
version = 0.1

# Требования (зависимости)
requirements = python3,kivy

# Ориентация экрана
orientation = portrait

# Полноэкранный режим
fullscreen = 0

# Иконка приложения (если есть)
# icon.filename = %(source.dir)s/icon.png

# Разрешения (что приложение может делать)
android.permissions = INTERNET

# Минимальная версия Android
android.minapi = 21

# Целевая версия Android
android.api = 31

# Версия SDK
android.sdk = 33

# Версия NDK
android.ndk = 25b

# Включить Java (если нужно)
# android.add_src =

# Цвета приложения
android.accept_sdk_license = True

# Архитектуры для сборки
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
# Уровень логирования
log_level = 2

# Предупреждения при запуске от root
warn_on_root = 1