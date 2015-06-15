import glob
from distutils.core import setup
from distutils.extension import Extension

from Cython.Distutils import build_ext

ext_modules = [
        Extension("crf.model", ["crf/model.pyx", "crf/conns.pxi"],
            include_dirs=["crf/libcrf"],
            library_dirs=["crf/libcrf"], libraries=["fastcrf"]),
        Extension("crf.array", ["crf/array.pyx"]),
        Extension("crf.data.sentence", ["crf/data/sentence.pyx"]),
        Extension("crf.data.connsbuf", ["crf/data/connsbuf.pyx"],
            include_dirs=["crf/libcrf"],
            library_dirs=["crf/libcrf"], libraries=["fastcrf"]),
        Extension("crf.data.auxdata", ["crf/data/auxdata.pyx"]),
        Extension("crf.train.sgd", ["crf/train/sgd.pyx"],
            include_dirs=["crf/libcrf"]),
        Extension("crf.train.gradient", ["crf/train/gradient.pyx"],
            include_dirs=["crf/libcrf"],
            library_dirs=["crf/libcrf"], libraries=["fastcrf"]),
        Extension("crf.tager", ["crf/tager.pyx"],
            include_dirs=["crf/libcrf"],
            library_dirs=["crf/libcrf"], libraries=["fastcrf"]),
    ]

setup(name="pycrf",
        version="0.2",
        author='Jakub Waszczuk',
        author_email='waszczuk.kuba@gmail.com',
        cmdclass={'build_ext': build_ext},
        ext_modules=ext_modules,
        packages=["crf", "crf.data", "crf.train"])
