import Crypto.PublicKey
import Crypto.Hash
import Crypto.Signature
import fiepipelib.signature

def ToJSONData (publicKey):
    assert isinstance(publicKey,abstractpublickey)
    ret = {}
    ret['algorithm'] = publicKey._algorithm
    ret['key'] = publicKey._key.hex()
    signatures = []
    for s in publicKey._signatures:
        signatures.append(fiepipelib.signature.ToJSDONData(s))
    ret['signatures'] = signatures
    return ret

def FromJSONData (data, publicKey):
    assert isinstance(publicKey,abstractpublickey)
    assert isinstance(data,dict)
    ret = publicKey
    ret._algorithm =data['algorithm']
    ret._key = bytes.fromhex(data['key'])
    signatures = []
    for s in data['signatures']:
        signatures.append(fiepipelib.signature.FromJSONData(s))
    ret._signatures = signatures
    return ret

def FromRSAKey(rawKey,publicKey,signatures = []):
    """Build a public key object from a key and optionally providing a list of signatures with which to authorize it."""
    assert isinstance(publicKey,abstractpublickey)
    ret = publicKey
    ret._algorithm = "RSA"
    ret._key = rawKey
    ret._signatures = signatures
    return ret


class abstractpublickey(object):
    """A public key for a legal entity"""

    _algorithm = None
    """The name of the public key algorithm used for this key.
    e.g. RSA
    """

    _key = None
    """The raw key.  As bytes.
    """

    _signatures = None
    """A list of Signature objects that represent signatures of this key.
    These signatures prove that the holder of the associated private keys
    in some way endorse or authorize this key.
    """

    def GetAlgorithm(self):
        return self._algorithm

    def GetLength(self):
        return len(self._key)

    def isEnabled(self):
        """
        Makes sure this key is enabled.  It may be diabled for securty reasons at runtime.
        For example, the algorithm might be determined to be insecure and hence disallowed
        for verification purposes.
        """
        return self._isAllowedAlgorithm()

    def GetSignatures(self):
        return self._signatures.copy()

    def _isAllowedAlgorithm(self):
        #TODO: update this whole system to support arbitrary signatures.  Start by allowing DSA.  Next, disallow some arbitrary older algorithm.
        return _algorithm == "RSA"

    def verify(self, msg, signature):
        """digests a message and verifies that the signature is valid.
        @param msg: the message to digest
        @param signature: the signature to verify
        """
        assert isinstance (signature, fiepipelib.signature.signature)
        
        if _isAllowedAlgorithm(self._algorithm):
            hasher = Crypto.Hash.SHA256.new()
            hasher.update(msg)
            digest = hasher.digest()
            key = Crypto.PublicKey.RSA.import_key(self._key)
            signer = Crypto.Signature.PKCS1_v1_5.new(key)
            return signer.verify(digest,signature.GetSignature())
        else:
            raise RuntimeError("This algorithm is disallowed: " + self._algorithm)

class legalentitypublickey(abstractpublickey):
    """A public key for a legal entity"""

class networkedsitepublickey(abstractpublickey):
    """a public key for a networked site"""
