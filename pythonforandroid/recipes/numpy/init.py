from pythonforandroid.recipe import PythonRecipe

class NumpyRecipe(PythonRecipe):
    version = '1.23.5'
    url = 'https://pypi.org/packages/source/n/numpy/numpy-{version}.tar.gz'
    depends = ['setuptools']

recipe = NumpyRecipe()