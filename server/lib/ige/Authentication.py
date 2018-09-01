import binascii
from ige import SecurityException, log
import hashlib
import os
import rsa
import time

defaultMethod = "rsa"

# support for RSA keys
publicKey = None
privateKey = None

def init(authMethod, size=2048):
    # RSA needs init
    if authMethod == "rsa":
        initRSAKeys(size)

def _generateKeys(size):
    global publicKey, privateKey
    # no keys, let's generate them
    log.message("Generating RSA keys of size {0}, please wait...".format(size))
    publicKey, privateKey = rsa.newkeys(size)

def initRSAKeys(size):
    """Load or generate and save RSA keys"""
    _generateKeys(size)

def getPublicKey():
    """Get current RSA public key"""
    assert publicKey is not None
    return publicKey

def getPrivateKey():
    """Get current RSA private key"""
    assert privateKey is not None
    return privateKey

#
def getMethod(challenge):
    return challenge.split(":")[0]

def getWelcomeString(method = "rsa"):
    """Return welcome string (typically a challenge)"""
    if method == "sha256":
        return "sha256:" + hashlib.sha256(str(time.time())).hexdigest()
    elif method == "rsa":
        publicKey = getPublicKey()
        return "rsa:%s:%s" % (publicKey.n, publicKey.e)
    raise SecurityException("Unsupported authentication method %s" % str(method))

def encode(password, challenge):
    """Encode password using auth method specified in the challenge"""
    method = getMethod(challenge)
    if method == "sha256":
        return hashlib.sha256(password + challenge).hexdigest()
    elif method == "rsa":
        dummy, n, e = challenge.split(":")
        key = rsa.PublicKey(int(n), int(e))
        return binascii.hexlify(rsa.encrypt(password.encode('utf-8'), key))
    raise SecurityException("Unsupported authentication method %s" % str(method))

def unwrapUserPassword(password, challenge):
    """Decode password according to auth method (if possible)"""
    method = getMethod(challenge)
    if method == "sha256":
        return password
    elif method == "rsa":
        return rsa.decrypt(binascii.unhexlify(password), getPrivateKey())
    raise SecurityException("Unsupported authentication method %s" % str(method))

