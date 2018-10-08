import typing

import cookiecutter.main

from fiepipelib.filetemplates.filetemplates import GetTemplates


def get_available_templates(fqdn: str) -> typing.Dict[str, str]:
    """
    Returns a dictionary of names and paths for cookiecutter templates for the given FQDN.

    :param fqdn: The fqdn for which we are looking for templates.
    :return: Dict[str,str] of names and paths/urls

    The string path/urls are passed directly to cookiecutter.  And therefore, they can
    be anything legal. e.g. internet URL e.g. path to a local python package resource (zip or dir)
    e.g. a local directory listing where you've just pulled/updated a bunch of templates from a server.
    """
    ret = GetTemplates("cookiecutter", fqdn)
    return ret


def deploy_shell(fqdn: str, name: str, local_path: str):
    """Executes a deployment in shell mode.  Where cookiecutter uses its CLI.
    Note: if you call this in a GUI, you probably will stall as cookiecutter expects CLI input."""
    templates = get_available_templates(fqdn)
    template = templates[name]
    cookiecutter.main.cookiecutter(template=template, output_dir=local_path)
