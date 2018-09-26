def FromJSONData(data):
    ret = signature()
    ret._algorithm = data['algorithm']
    ret._signature = bytes.fromhex(data['signature'])
    ret._signer = data['signer']
    return ret

def ToJSDONData(signature):
    ret = {}
    ret['algorithm'] = signature._algorithm
    ret['signature'] = signature._signature.hex()
    ret['signer'] = signature._signer
    return ret

def FromParameters(algorithm, signature, signer):
    ret = signature()
    ret._algorithm = algorithm
    ret._signature = signature
    ret._signer = signer
    return ret

class signature(object):
    """A cryptographic signature"""

    _signer = None
    """Unqiue name or tracking information that identifies the singer.

    Good cryptographic hashes should never collide.
    But you can save processing time by filtering by the signer.
    
    Also, in some cases, a list of signers can help you find some kind
    of public quarum where a number of signatures from generally known
    public entities is good enough, without knowing ahead of time who
    might have signed the data.
    """

    _algorithm = None
    """The name of the algorithm used.  e.g. RSA"""

    _signature = None
    """The actual signature in binary form.  Bytes."""

    def GetAlgorithm(self):
        return self._algorithm

    def GetSignature(self):
        return self._signature

    def GetSigner(self):
        return self._signer