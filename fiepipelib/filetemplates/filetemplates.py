import pkg_resources

"""File template system.
Consumers simply call GetTemplates with appropriate parameters.

Providing templates requires that a package implement a plugin entry_point via pkg_resources in its setup.py.

the entry point is 'fiepipe.plugin.templates.file'

The method it points to should have the following signature method_name(tempalteType:str,fqdn:str,templatePaths:Dict[str:str])

Where:
  templateType is a well known name for the type of template being sought
  fqdn is a fully qualified domain name of the entity in which the request is being made
  templatePaths is a dictionary to add template names (str) and paths (str) to respectively: templatePaths[name] = path
  
A plugin may decide to ignore fqdn and provide templates globally in a well known manner, or only to a specific set of fqdns, discreetly.

Play nice.  Don't step on other people's well known template types and fqdns.

There is no runtime way to add templates to the system currently.
"""

def GetTemplates(templateType:str, fqdn:str):
    """Returns a dictionary of template names and paths.
    templateType - well known name of a type of file.
    fqdn - entity fqdn for which we are searching."""
    entrypoints = pkg_resources.iter_entry_points("fiepipe.plugin.templates.file")
    ret = {}
    for entrypoint in entrypoints:
        method = entrypoint.load()
        method(templateType,fqdn,ret)
    return ret
    
    
    