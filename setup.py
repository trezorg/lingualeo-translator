"""The setup and build script for the lingualeo-translator library."""
from __future__ import unicode_literals
import codecs
import os

from setuptools import (
    setup,
    find_packages,
)
try:
    from pypandoc import convert

    def read_md(fln):
        """Convert MD to RST."""
        return convert(fln, 'rst')

except ImportError:
    convert = None

    def read_md(fln):
        """Mock convert MD to RST. Just read."""
        return read(fln)

__author__ = 'Igor Nemilentsev'
__author_email__ = 'trezorg@gmail.com'
tests_require = ['py.test']
setup_requires = ['pytest-runner']


def prepare_version(version_tuple):
    """Parse project version."""
    if not isinstance(version_tuple[-1], int):
        return '.'.join(
            str(part) for part in version_tuple[:-1]) + version_tuple[-1]
    return '.'.join(str(part) for part in version_tuple)


def get_version():
    """Get project version."""
    init = os.path.join(
        os.path.dirname(__file__), 'lingualeo_translator', '__init__.py')
    version_line = next(iter(
        filter(lambda l: l.startswith('VERSION'), open(init))))
    return prepare_version(eval(version_line.split('=')[-1]))


def strip_comments(line):
    """Remove comments."""
    return line.split('#', 1)[0].strip()


def read(*names, **kwargs):
    """Read adn decode file."""
    return codecs.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()


def get_requirements(fln):
    """Read requirements from file."""
    gen = (strip_comments(line) for line in read(fln).splitlines())
    return list(req for req in gen if req)


setup(
    name="lingualeo-translator",
    version=get_version(),
    author=__author__,
    author_email=__author_email__,
    description='Translate and add words with Lingualeo service',
    long_description=read_md('README.md'),
    license='MIT',
    url='https://github.com/trezorg/lingualeo-translator.git',
    keywords='lingualeo, python, english',
    packages=find_packages(),
    include_package_data=True,
    install_requires=get_requirements('requirements.txt'),
    tests_require=tests_require,
    setup_requires=setup_requires,
    entry_points={
        'console_scripts': ['lingualeo=lingualeo_translator.lingualeo:main'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Communications',
        'Topic :: Internet',
    ],
)
