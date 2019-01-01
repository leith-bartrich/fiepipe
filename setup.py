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
    
install_requires=["rpyc","plumbum","paramiko","cryptography","GitPython","cmd2","cmd2-submenu>=0.3.0","bcrypt","pycryptodome","pyreadline","keyboard","cookiecutter","watchdog>=0.9.0"],
    entry_points={
        'fiepipe.plugin.shell.gitlabserver.shell.v1' : [
            'container = fiepipelib.container.shells.gitlabserver:FIEPipeShellPlugin',
            'registered_entity = fiepipelib.legalentity.registry.shell.gitlabserver:FIEPipeShellPlugin',
        ],
        'console_scripts': [
            'fiepipe = fiepipelib.shells.fiepipe:main',
            #'fiepipestateserver = fiepipestateserver:main',
            'fiepipe_gitlab = fiepipelib.gitlabserver.shell.manager:main',
            'fiepipe_containers = fiepipelib.container.shells.manager:main',
            'fiepipe_watchfolder = fiepipelib.watchfolder.shell.watchfolder:main',
        ],
        'fiepipe.plugin.gitstorage.lfs.patterns' : [
            'fiepipe = fiepipelib.gitstorage.routines.lfs_tracked_patterns:get_patterns',
        ],
        'fiepipe.plugin.shell.gitasset.v1': [
            'watchfolders = fiepipelib.watchfolder.shell.watchfolder:git_asset_shell_plugin',
        ],

    },
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        ],
)
