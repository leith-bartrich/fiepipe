import fiepipelib.privatekey
import Crypto.PublicKey
import Crypto.Signature
import Crypto.Hash
import fiepipelib.registeredlegalentity
import fiepipelib.abstractmanager

def CreateFromParameters(fqdn,privatekeys,revokations):
    """Creates an authored legal entity from the given parameters
    @param fqdn: the fully qualified domain name of the entity
    @param privatekeys: a list of legalentityprivatekey objects
    @param revokations: a list of signatures that have been revoked by this entity
    """
    ret = authoredlegalentity()
    ret._fqdn = fqdn
    ret._privateKeys = privatekeys
    ret._revokations = revokations
    return ret

def FromJSONData(data):
    ret = authoredlegalentity()
    ret._fqdn = data['fqdn']
    privateKeys = []
    for kd in data['private_keys']:
        key = fiepipelib.privatekey.legalentityprivatekey()
        fiepipelib.privatekey.FromJSONData(kd,key)
        privateKeys.append(key)
    ret._privateKeys = privateKeys
    ret._revokations = data['revokations']
    return ret

def ToJSONData(entity):
    assert isinstance(entity,authoredlegalentity)
    ret = {}
    ret['version'] = 1
    ret['fqdn'] = entity._fqdn
    privateKeys = []
    for key in entity._privateKeys:
        privateKeys.append(fiepipelib.privatekey.ToJSDONData(key))
    ret['private_keys'] = privateKeys
    ret['revokations'] = entity._revokations
    return ret

def GetSignerName(fqdn):
    """Gets the signer name for the given fqdn.

    When checking signatures for a signature by a authored legal entity,
    one should search for a signer that matches this name.
    """
    return 'legalentity:' + fqdn


class localauthority(fiepipelib.abstractmanager.abstractlocalmanager):
    """Manages the state of entities over which this user has created authority.  Such entities
    can then be registered for use on this system, or other systems that trust this system to have
    authority over the entity.

    It's important to note that a user is always capable of creating authority
    for any FQDN they wish.  One can pretend to be anyone in their own computer system.
    But of course, that
    doesn't grant them access to the true FQDN owner's identity outside their own computer system.
    Rather, they
    are creating a compartmentalized and independent entity that may be rejected by the rest of the world as being illegitimate.

    The difference between a legitimate member of an entity creating a fully disconnected
    and ad-hoc compartment for working within that entity, and a malicious individual
    doing the same, is nearly impossible to discern within the computer system because
    the administrator of that system can always force the software to make the wrong decision.  One must assume
    that any digital rights managment systems can be overridden by the administrator of the
    malicious system as well.
    However we need to allow the former and protect against the latter.

    The actual decision point therefore, is the point of data migration.  Either automated
    or manual.  In either case, the question is: "Do you trust the source of the data you are
    migrating into your compartment?"  The answer can come in many forms.  Usually, based on
    physical security in the end.
    e.g. The person bringing you the data is an actual trusted
    employee who has a
    legitimate reason and authorization for migrating data from an ad-hoc setup.
    e.g. The machine that is pushing
    data was authorized to do so when it was configured by an authorized administrator by installing a
    private key, that has not been revoked.
    
    Similarly, parralel, fully air-gapped and compartmentalized entities created by the FQDN
    might be desirable in high security environments.  And similarly, the security mechanisms
    center around data migration in the same way.

    fiepipe maintains the idea of multiple compartments within a FQDN on a system.  However, such
    compartments are lower security than actual parallel, fully air-gapped compartments.  We call the
    lower security compartments: containers.  Some might see them as simlar to 'projects' in other
    digital asset managment and workflow systems.  Though we use a more generic term here becasue
    not all compartmentalized data is project based.  It might be department based.  Or based on
    fiscal year, for example.
  
    The provisioning of extremely high security compartments starts here at the legal entity authority
    level, when an
    individual legitimately provisions an independent FQDN entity in the computer system,
    in which to create such a high security compartment.

    In the extreme, the legal entity (company) has a parallel facility and staff who operate a fully
    compartmentalized set of containers.  The less secure staff might not even know about the existence of 
    the legitimate, but compartmentalized facility, staff and their projects and operations.  In that case,
    you have a completely
    different set of keys for the indepdendently provisioned FQDN.  Data from the high security compartment might
    migrate to lower security some day.  But that will require that the higher security data be migrated (declassified).
    And the people doing the ingest side of the migration need to be able to trust that whomever is delivering the
    data, is legitimate.  As such, the digital security is only maintained by the physical security.  Which is the correct
    way to handle redaction and declassification in highly secure scenarios.
    """

    def FromJSONData(self, data):
        return FromJSONData(data)

    def ToJSONData(self, item):
        return ToJSONData(item)

    def GetManagedTypeName(self):
        return "authored_legal_entity"

    def GetColumns(self):
        ret = super().GetColumns()
        ret.append(("fqdn","text"))
        return ret

    def GetPrimaryKeyColumns(self):
        return ["fqdn"]

    def DeleteByFQDN(self, fqdn):
        self._Delete("fqdn",fqdn)

    def GetByFQDN(self, fqdn):
        return self._Get([("fqdn",fqdn)])


class authoredlegalentity(object):
    """
    A legal entity that has been created by this user.
    
    A good amount of the information in this entity is private or secret.
    
    This kind of object should be very carefully guarded.

    It is typically stored on disk and managed by the legalentityauthority
    """

    _fqdn = None
    _privateKeys =None
    _revokations = None

    def GetFQDN(self):
        """The FQDN of this entity.  Usually its domain name. e.g. foo.com"""
        return self._fqdn

    def GetPrivateKeys(self):
        """Returns the secret private keys of this entity.
        As encryption algorithms and key lengths come and go,
        one would expect the private keys to be numerous and 
        go througha life-cycle in which they're added, used, 
        and retired."""
        return self._privateKeys.copy()

    def SetPrivateKeys(self, keys):
        """Sets the list of private keys. See GetPrivateKeys for more info.
        """
        assert isinstance(keys,list)
        self._privateKeys = keys

    def GetSignerName(self):
        return GetSignerName(self.GetFQDN())
        

    def SignMessage(self, msg):
        """digests the given message and signs it with each private key.
        Returns a list of Signature objects.  One for each private key.
        The signer for each will be in the form provided by GetSignerName at
        the module level.
        """
        ret = []
        for k in self._privateKeys:
            assert isinstance(k, fiepipelib.privatekey.legalentityprivatekey)
            ret.append(k.Sign(msg,self.GetSignerName()))

    def SignPublicKey(self,publicKey):
        """Signs public keys and stores the signatures in the public key.
        """
        for k in self._privateKeys:
            assert isinstance(k, fiepipelib.privatekey.legalentityprivatekey)
            k.SignPublicKey(publicKey,self.GetSignerName())


    def GetPublicKeys(self):
        """Returns a list of public keys.  One for each private key.
        These keys can be givne out freely as they're public."""
        ret = []
        for k in self._privateKeys:
            assert isinstance(k,fiepipelib.privatekey.legalentityprivatekey)
            ret.append(k.GetPublicKey())
        return ret

    def RevokeSignature(self, signature):
        """Adds a signature to the list of revoked signatures.  Note that this
        revokation list doesn't get distributed magically.  One must generate new
        registeredlegalentity objects and distribute them in order for
        the revokation list to propogate.
        """
        assert isinstance(signature, fiepipelib.signature.signature)
        _revokations.append(signature.GetSignature())

    def UnrevokeSignature(self, signature):
        """Removes the signature form the revokation list.  Usually because
        you made a mistake adding it in the first place.  Typically, a revoked signature
        should remain revoked forever becasue it has been compromised forever.
        """
        assert isinstance(signature, fiepipelib.signature.signature)
        _revokations.remove(signature.GetSignature())

    def CreateRegisteredLegalEntity(self):
        """Creates a registered legal entity from this authoredlegalentity.
        While this authored entity is considered private, the registered version
        derived from it by this method, is public.
        """
        return fiepipelib.registeredlegalentity.FromParameters(self._fqdn,self.GetPublicKeys(),self._revokations.copy())
