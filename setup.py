import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "fiepipe",
    version = "0.1.0.dev1",
    author= "Bradley Friedman",
    author_email = "brad@fie.us",
    description = ("A general workflow system for people and other legal entities."),
    license = "MIT",
    keywords = "pipeline,workflow,fie",
    url = "http://www.fie.us",
    py_modules=["fiepipe", "fiepipestateserver"],
    packages = find_packages(),
    
install_requires=["rpyc","plumbum","paramiko","cryptography","GitPython","bcrypt","pycryptodome","cookiecutter","watchdog>=0.9.0"],
    entry_points={
        'fiepipe.plugin.gitstorage.lfs.patterns' : [
            'fiepipe = fiepipelib.gitstorage.routines.lfs_tracked_patterns:get_patterns',
        ],
    },
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        ],
)
