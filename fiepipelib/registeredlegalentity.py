import fiepipelib.publickey
import fiepipelib.authoredlegalentity
import fiepipelib.abstractmanager

def FromJSONData(jsondata):
    assert isinstance(jsondata,dict)
    ret = registeredlegalentity()
    ret._fqdn = jsondata['fqdn']
    ret._publicKeys = []
    for k in jsondata['public_keys']:
        key = fiepipelib.publickey.legalentitypublickey()
        fiepipelib.publickey.FromJSONData(k,key)
        ret._publicKeys.append(key)
    ret._revocations = []
    for r in jsondata['revocations']:
        ret._revocations.append(r)
    return ret

def ToJSONData(entity):
    assert isinstance(entity,registeredlegalentity)
    ret = {}
    ret['fqdn'] = entity._fqdn
    ret['public_keys'] = []
    for k in entity._publicKeys:
        assert isinstance(k, fiepipelib.publickey.legalentitypublickey)
        ret['public_keys'].append(fiepipelib.publickey.ToJSONData(k))
    revocations = []
    for r in entity._revocations:
        revocations.append(r)
    ret['revocations'] = revocations
    return ret

def FromParameters(fqdn, publicKeys = [], revocations = []):
    ret = registeredlegalentity()
    ret._fqdn = fqdn
    ret._publicKeys = publicKeys
    ret._revocations = revocations
    return ret

class localregistry(fiepipelib.abstractmanager.abstractlocalmanager):

    def FromJSONData(self, data):
        return FromJSONData(data)

    def ToJSONData(self, item):
        return ToJSONData(item)

    def GetColumns(self):
        ret = super().GetColumns()
        ret.append(("fqdn","text"))
        return ret
    
    def GetPrimaryKeyColumns(self):
        return ["fqdn"]

    def GetManagedTypeName(self):
        return "registered_legal_entity"

    def DeleteByFQDN(self, fqdn):
        self._Delete("fqdn",str(fqdn))

    def GetByFQDN(self, fqdn):
        return self._Get([("fqdn",fqdn)])


class registeredlegalentity(object):
    """Configuration and functionality of a legal entity of which the local user is a member of some kind.
    Typically this is imported or pulled form a trusted location.
    
    When you import or use a registeredlegalentity, you are trusting that the source of that information is who
    they say they are.
    
    The registeredlegalenity contains all the public keys and revokation lists on which to base further digital trust.
    
    The registeredlegalentity should be updated regularly and securely, to maintain an up to date revokation list."""
    
    _fqdn = None
    _publicKeys = None
    _revocations = None

    def GetFQDN(self):
        """The well known fully qualfied domain name by which this entity is known.
        """
        return self._fqdn

    def ValidatePublicKey(self,publicKey):
        """Determines the validity of the given public key, as having been signed by this entity.  Or not.
        @param publicKey: The key to validate
        """
        assert isinstance(publicKey, fiepipelib.publickey.abstractpublickey)
        return self.ValidateMessage(publicKey._key,publicKey.GetSignatures())
        
    def ValidateMessage(self,msg,signatures):
        """
        Determines the validity of the given message, as being from this entity, using the given signatures.
        @param msg: The message to validate
        @param signatures: a list of fiepipelib.signature.signature objects for the message.
        """
        assert isinstance(signatures,list)

        unrevokedSignatures = signatures.copy()

        #first we filter out any revoked signatures.
        for s in signatures:
            for r in self._revocations:
                if r == signature.getSignature():
                    unrevokedSignatures.remove(s)

        signerName = fiepipelib.authoredlegalentity.GetSignerName(self._fqdn)
        #now we validate with the right algorithm if we have it.
        #walk through the keys
        for pk in self._publicKeys:
            #only if they're enabled.
            if pk.isEnabled():
                assert isinstance(pk, fiepipelib.publickey.legalentitypublickey)
                #check each signature.  It only takes one good one.
                algorithm = pk.GetAlgorithm()
                for s in unrevokedSignatures:
                    assert isinstance(s, fiepipelib.signature.signature)
                    #only bother trying if the signer is the right signer
                    if s.GetSigner() == signerName:
                        #only bother if its the right algorithm
                        if (algorithm == s.GetAlgorithm()):
                            #check validity move on if it's not valid.
                            if pk.verify(msg,s):
                                #if we match, we've validated!
                                return True
                    
        #if we get here we don't have an algorithm that generated a match.  It isn't valid.
        return False


