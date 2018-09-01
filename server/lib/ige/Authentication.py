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

def init(configDir, authMethod, size=2048):
    # RSA needs init
    if authMethod == "rsa":
        initRSAKeys(configDir, size)

def _generateKeys(privatePath, publicPath, size):
    global publicKey, privateKey
    # no keys, let's generate them
    log.message("Generating RSA keys of size {0}, please wait...".format(size))
    publicKey, privateKey = rsa.newkeys(size)
    with open(privatePath, 'w') as privKeyFile:
        privKeyFile.write(privateKey.save_pkcs1())
    with open(publicPath, 'w') as pubKeyFile:
        pubKeyFile.write(publicKey.save_pkcs1())

def initRSAKeys(configDir, size):
    """Load or generate and save RSA keys"""
    global publicKey, privateKey
    privatePath = os.path.join(configDir, 'private.pem')
    publicPath = os.path.join(configDir, 'public.pem')
    try:
        log.message("Loading PRIVATE RSA key")
        with open(privatePath, 'rb') as privKeyFile:
            privateKey = rsa.PrivateKey.load_pkcs1(privKeyFile.read())
        log.message("Loading PUBLIC RSA key")
        with open(publicPath, 'rb') as pubKeyFile:
            publicKey = rsa.PublicKey.load_pkcs1(pubKeyFile.read())
    except ValueError:
        _generateKeys(privatePath, publicPath, size)
    except IOError:
        _generateKeys(privatePath, publicPath, size)

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

