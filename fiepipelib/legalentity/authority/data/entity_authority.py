import typing

import fiepipelib.locallymanagedtypes.data.abstractmanager
import fiepipelib.encryption.public.privatekey
from fiepipelib.encryption.public.privatekey import legalentityprivatekey
from fiepipelib.encryption.public.publickey import legalentitypublickey
import fiepipelib.encryption.public.signature
from fiepipelib.legalentity.registry.data.registered_entity import RegisteredEntity


def CreateFromParameters(fqdn, privatekeys, revocations):
    """Creates an authored legal entity from the given parameters
    @param fqdn: the fully qualified domain name of the entity
    @param privatekeys: a list of legalentityprivatekey objects
    @param revocations: a list of signatures that have been revoked by this entity
    """
    ret = LegalEntityAuthority()
    ret._fqdn = fqdn
    ret._privateKeys = privatekeys
    ret._revocations = revocations
    return ret


def FromJSONData(data):
    ret = LegalEntityAuthority()
    ret._fqdn = data['fqdn']
    privateKeys = []
    for kd in data['private_keys']:
        key = legalentityprivatekey()
        fiepipelib.encryption.public.privatekey.FromJSONData(kd, key)
        privateKeys.append(key)
    ret._privateKeys = privateKeys
    ret._revocations = data['revocations']
    return ret


def ToJSONData(entity):
    assert isinstance(entity, LegalEntityAuthority)
    ret = {}
    ret['version'] = 1
    ret['fqdn'] = entity._fqdn
    privateKeys = []
    for key in entity._privateKeys:
        privateKeys.append(fiepipelib.encryption.public.privatekey.ToJSDONData(key))
    ret['private_keys'] = privateKeys
    ret['revocations'] = entity._revocations
    return ret


def get_signer_name(fqdn) -> str:
    """Gets the signer name for the given fqdn.

    When checking signatures for a signature by a authored legal entity,
    one should search for a signer that matches this name.
    """
    return 'legalentity:' + fqdn


class LegalEntityAuthority(object):
    """
    A legal entity that has been created by this user.

    A good amount of the information in this entity is private or secret.

    This kind of object should be very carefully guarded.

    It is typically stored on disk and managed by the legalentityauthority
    """

    _fqdn: str = None
    _privateKeys: typing.List[fiepipelib.encryption.public.privatekey.legalentityprivatekey] = None
    _revocations: typing.List[bytes] = None

    def get_fqdn(self):
        """The FQDN of this entity.  Usually its domain name. e.g. foo.com"""
        return self._fqdn

    def get_private_keys(self):
        """Returns the secret private keys of this entity.
        As encryption algorithms and key lengths come and go,
        one would expect the private keys to be numerous and
        go througha life-cycle in which they're added, used,
        and retired."""
        return self._privateKeys.copy()

    def set_private_keys(self, keys: typing.List[fiepipelib.encryption.public.privatekey.legalentityprivatekey]):
        """Sets the list of private keys. See GetPrivateKeys for more info.
        """
        self._privateKeys = keys

    def get_signer_name(self) -> str:
        return get_signer_name(self.get_fqdn())

    def sign_message(self, msg):
        """digests the given message and signs it with each private key.
        Returns a list of Signature objects.  One for each private key.
        The signer for each will be in the form provided by GetSignerName at
        the module level.
        """
        ret = []
        for k in self._privateKeys:
            assert isinstance(k, fiepipelib.encryption.public.privatekey.legalentityprivatekey)
            ret.append(k.Sign(msg, self.get_signer_name()))

    def sign_public_key(self, public_key: legalentitypublickey):
        """Signs public keys and stores the signatures in the public key.
        """
        for k in self._privateKeys:
            assert isinstance(k, fiepipelib.encryption.public.privatekey.legalentityprivatekey)
            k.SignPublicKey(public_key, self.get_signer_name())

    def get_public_keys(self) -> typing.List[legalentitypublickey]:
        """Returns a list of public keys.  One for each private key.
        These keys can be givne out freely as they're public."""
        ret = []
        for k in self._privateKeys:
            assert isinstance(k, fiepipelib.encryption.public.privatekey.legalentityprivatekey)
            ret.append(k.GetPublicKey())
        return ret

    def revoke_signature(self, signature: fiepipelib.encryption.public.signature.signature):
        """Adds a signature to the list of revoked signatures.  Note that this
        revokation list doesn't get distributed magically.  One must generate new
        registeredlegalentity objects and distribute them in order for
        the revocation list to propagate.
        """
        assert isinstance(signature, fiepipelib.encryption.public.signature.signature)
        self._revocations.append(signature.GetSignature())

    def unrevoke_signature(self, signature: fiepipelib.encryption.public.signature.signature):
        """Removes the signature form the revocation list.  Usually because
        you made a mistake adding it in the first place.  Typically, a revoked signature
        should remain revoked forever because it has been compromised forever.
        """
        self._revocations.remove(signature.GetSignature())

    def generate_registered_legal_entity(self) -> RegisteredEntity:
        """Creates a registered legal entity from this authoredlegalentity.
        While this authored entity is considered private, the registered version
        derived from it by this method, is public.
        """
        return fiepipelib.legalentity.registry.data.registered_entity.FromParameters(self._fqdn, self.get_public_keys(),
                                                                                     self._revocations.copy())


