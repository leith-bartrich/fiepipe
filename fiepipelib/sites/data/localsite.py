import fiepipelib.sites.data.abstractsite

def FromParameters(fqdn):
    assert isinstance(fqdn, str)
    ret = localsite()
    fiepipelib.sites.data.abstractsite.FromParameters(ret, "localsite", fqdn)
    return ret


class localsite(fiepipelib.sites.data.abstractsite.abstractsite):
    """Represents the local site for a given fqdn on this system.
    
    Usually used to work locally in a disconnected sense, or when whatever network
    information that might be needed, has been sufficiently cached locally to
    ignore any network dependencies.
    
    A higher level routine or workflow might:

        -spawn a network site
            -pull some data,
        -destroy the network site
        -create a local site
            -do work
            -do other work
            -finish work
        -destroy the local site
        -spawn a network site
            -push data
        -destroy the network site
    """



      

