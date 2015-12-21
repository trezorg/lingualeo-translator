"""The setup and build script for the lingualeo-translator library."""
import codecs
import os
from setuptools import setup, find_packages

__author__ = 'Igor Nemilentsev'
__author_email__ = 'trezorg@gmail.com'
__version__ = '0.0.1'
tests_require = ['nose']


def read(*names, **kwargs):
    return codecs.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()

setup(
    name="lingualeo-translator",
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    description='Translate and add words with Linualeo service',
    long_description=read('README.md'),
    license='MIT',
    url='https://github.com/trezorg/lingualeo-translator.git',
    keywords='lingualeo, python, english',
    packages=find_packages(),
    include_package_data=True,
    install_requires=read('requirements.txt').splitlines(),
    test_suite='nose.collector',
    scripts=['lingualeo_translator/lingualeo.py'],
    tests_require=tests_require,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Communications',
        'Topic :: Internet',
    ],
)
