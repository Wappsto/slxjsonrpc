from setuptools import find_packages
from setuptools import setup

import pathlib
import codecs
import os
import re


readme_file = pathlib.Path('README.md')
changelog_file = pathlib.Path('CHANGELOG.md')

here = os.path.abspath(os.path.dirname(__file__))


def get_long_description():
    long_description = ""

    if not readme_file.exists():
        return ""

    with readme_file.open("r") as file:
        long_description += file.read()

    long_description += "\n\n"

    if not changelog_file.exists():
        return long_description

    with changelog_file.open("r") as file:
        long_description += file.read()

    return long_description


def find_version(*file_paths):
    path = os.path.join(here, *file_paths)
    with codecs.open(path, 'r') as fp:
        version_file = fp.read()
        version_match = re.search(r"__version__ = ['\"]([^'\"]*)['\"]",
                                  version_file, re.M)
        if version_match:
            return version_match.group(1)
        raise RuntimeError("Unable to find version string.")


def find_auther(*file_paths):
    path = os.path.join(here, *file_paths)
    with codecs.open(path, 'r') as fp:
        auther_file = fp.read()
        auther_match = re.search(r"__auther__ = ['\"]([^'\"]*)['\"]",
                                 auther_file, re.M)
        if auther_match:
            return auther_match.group(1)
        raise RuntimeError("Unable to find auther string.")


setup(
    name="slxjsonrpc",
    version=find_version("slxjsonrpc", "__init__.py"),
    author=find_auther("slxjsonrpc", "__init__.py"),
    author_email="support@seluxit.com",
    license="Apache-2.0",
    description="SlxJsonRpc JsonRpc helper class, that uses pydantic.",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/Wappsto/slxjsonrpc",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent"
    ],
    packages=find_packages(),
    package_data={
        'slxjsonrpc': ['jsonrpc.pyi'],
        'slxjsonrpc/schema': ['schema/jsonrpc.pyi'],
    },
    tests_require=[
        'pytest',
        'tox'
    ],
    data_files=[('info', [readme_file.name, changelog_file.name])],
    install_requires=[
       'pydantic>=1.6.1'
    ],
    python_requires='>3.6.0',
)
