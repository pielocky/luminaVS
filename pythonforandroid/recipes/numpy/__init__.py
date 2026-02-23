from pythonforandroid.recipe import PythonRecipe

class NumpyRecipe(PythonRecipe):
    version = '1.23.5'
    url = 'https://mirror.yandex.ru/pypi/packages/source/n/numpy/numpy-1.23.5.tar.gz'
    depends = ['setuptools']

recipe = NumpyRecipe()