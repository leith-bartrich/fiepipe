import fiepipelib.registeredlegalentity

def ToJSONData(site, data):
    assert isinstance(site, abstractsite)
    assert isinstance(data,dict)
    data['version'] = 1
    data['name'] = site._name
    data['entity_fqdn'] = site._entityFQDN

def FromJSONData(site, data):
    assert isinstance(site, abstractsite)
    assert isinstance(data,dict)
    site._name = data['name']
    site._entityFQDN = data['entity_fqdn']

def FromParameters(site, name, fqdn):
    assert isinstance(site, abstractsite)
    site._name = name
    site._entityFQDN = fqdn

class abstractlocalregistry(fiepipelib.abstractmanager.abstractlocalmanager):

    def GetColumns(self):
        """Override this and append to super's returned list:  A list of tupples of column names and sqlite data types for indexed columns e.g. [('id','text')]"""
        ret = super().GetColumns()
        ret.append(("entity_fqdn","text"))
        ret.append(("name","text"))
        return ret

    def GetByFQDN(self, fqdn):
        return self._Get([("entity_fqdn",fqdn)])

    def GetByFQDNandName(self, fqdn, name):
        return self._Get([("entity_fqdn",fqdn),("name",name)])

    def DeleteByFQDN(self, fqdn):
        self._Delete("entity_fqdn",fqdn)

    def DeleteByFQDNAndName(self, fqdn, name):
        self._DeleteByMultipleAND([("entity_fqdn",fqdn),("name",name)])
    
    def GetPrimaryKeyColumns(self):
        return ["entity_fqdn","name"]

class abstractsite(object):
    """A configured site for a given legal entity

    A site is typically stored on disk and acquired by a registry or manager.

    Specific implementations of the abstract site type will know more about how they are managed.
    """

    _entityFQDN = None
    _name = None

    def GetName(self):
        """The name of the site.  Typically short, lowercase and with no white space.
        """
        return self._name

    def GetEntityFQDN(self):
        """The FQDN of this site.  In otherwords, to which legal entity does this site belong.
        """
        return self._entityFQDN