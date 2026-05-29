from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy

#original #EMBREE3_INCLUDE_DIR = '/usr/include/embree3'
#original #EMBREE3_LIBRARY_DIR = '/usr/lib/embree3'
EMBREE3_INCLUDE_DIR = '/home/koprivnanska7/miniconda3/envs/nerftex/include'  #I added
EMBREE3_LIBRARY_DIR = '/home/koprivnanska7/miniconda3/envs/nerftex/lib' #I added

ext = Extension(
    name='instancer',
    sources=['instancer.pyx'], 
    include_dirs=[numpy.get_include(), 'submodules/eigen', 'submodules/libigl/include', 'submodules/stb', 'submodules/json/single_include/nlohmann', EMBREE3_INCLUDE_DIR],
    library_dirs=[EMBREE3_LIBRARY_DIR],
    libraries=['embree3'],
    language='c++',
    extra_compile_args=['-w', '-lembree3', '-std=c++17', '-fPIC'], #I added '-std=c++17', '-fPIC'
    extra_link_args=['-Wl,-rpath,' + EMBREE3_LIBRARY_DIR]
)

setup(
    name='instancer',
    ext_modules=cythonize(ext)
)
