import Crypto.PublicKey.RSA
import Crypto.Hash
import Crypto.Signature

import fiepipelib.publickey
import fiepipelib.signature

def ToJSDONData(key):
    assert isinstance(key, abstractprivatekey)
    ret = {}
    ret['version'] = 1
    ret['algorithm'] = key._algorithm
    ret['key'] = key._key.hex()
    return ret

def FromJSONData(data, key):
    assert isinstance(key, abstractprivatekey)
    ret = key
    ret._algorithm = data['algorithm']
    ret._key = bytes.fromhex(data['key'])
    return ret

def GenerateRSA3072(key):
    assert isinstance(key, abstractprivatekey)
    ret = key
    ret._algorithm = "RSA"
    key = Crypto.PublicKey.RSA.generate(bits=3072)
    ret._key = key.exportKey()
    return ret


class abstractprivatekey(object):
    """A private key"""

    _algorithm = None
    _key = None

    def Sign(self, msg, signername):
        """Signs the given message
        @rtype Signature
        @return: returns a Signature object"""
        key = Crypto.PublicKey.RSA.import_key(self._key)
        hasher = Crypto.Hash.SHA256.new()
        hasher.update(msg)
        digest = hasher.digest()
        signer = Crypto.Signature.PKCS1_v1_5.new(key)
        signature = signer.sign(digest)
        ret = fiepipelib.signature.FromParameters('RSA',signature,signername)
        return ret

    def SignPublicKey(self, publicKey, signer):
        """Given a public key, we sign it and then add the signature to the public key's ledger of signatures.

        This signature proves to anyone who trusts this private key (via the public key), that the public key we've signed was trusted
        by this private key.

        Revokations of signatures are handled at a higher level.

        @param publicKey: The public key to sign
        @param signer: The text to burn into the signature as the identified 'signer.'
        Answers the question: who signed this?
        Typically, you'll want to lookup signatures using this text field in order to validate the signature.
        @type signer: str
        """
        assert isinstance(publicKey, fiepipelib.publickey.abstractpublickey)
        if publicKey._signatures == None:
            publicKey._signatures = []
        newsig = self.Sign(publicKey._key,signer)

        #if this signer and algorithm already exists, remove it first.  It's obsolete
        toRemove = []
        for sig in publicKey._signatures:
            if sig._signer == newsig._signer:
                if sig._algorithm == newsig._algorithm:
                    toRemove.append(sig)
        for sig in toRemove:
            publicKey._signatures.remove(sig)
        
        #add the sig
        publicKey._signatures.append(newsig)

    def createemptypublickey(self):
        """Return an empty public key for this private key type.
        """
        #needs to be implemented by subclass
        raise NotImplementedError()

    def GetPublicKey(self):
        """Creates the public key object for this private key object.
        @rtype fiepipelib.legalengitypublickey
        """
        ret = self.createemptypublickey()
        key = Crypto.PublicKey.RSA.import_key(self._key)
        fiepipelib.publickey.FromRSAKey(key.publickey().exportKey(),ret)
        return ret

class networkedsiteprivatekey(abstractprivatekey):
    """A private key for a networked site"""

    def createemptypublickey(self):
        return fiepipelib.publickey.networkedsitepublickey()

class legalentityprivatekey(abstractprivatekey):
    """A private key for a legal entity"""

    def createemptypublickey(self):
        return fiepipelib.publickey.legalentitypublickey()
