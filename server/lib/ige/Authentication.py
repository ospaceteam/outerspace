import binascii
from ige import SecurityException, log
import hashlib
import os
import rsa
import time

# default method is set to MD5 for backward compatibility
# with version 0.5.68 (revision 308)
defaultMethod = "md5"

# support for RSA keys
publicKey = None
privateKey = None

def createRSAKeys():
    """Load or generate and save RSA keys"""
    global publicKey, privateKey
    if os.path.exists("var/private.pem"):
        log.message("Loading PRIVATE RSA key")
        privateKey = rsa.PrivateKey.load_pkcs1(open("var/private.pem", "rb").read())
    if os.path.exists("var/public.pem"):
        log.message("Loading PUBLIC RSA key")
        publicKey = rsa.PublicKey.load_pkcs1(open("var/public.pem", "rb").read())
    if privateKey and publicKey:
        return
    # no keys, let's generate them
    log.message("Generating RSA keys, please wait...")
    publicKey, privateKey = rsa.newkeys(2048)
    open("var/public.pem", "w").write(publicKey.save_pkcs1())
    open("var/private.pem", "w").write(privateKey.save_pkcs1())
    
def getPublicKey():
    """Get current RSA public key"""
    global publicKey
    if not publicKey:
        createRSAKeys()
    return publicKey

def getPrivateKey():
    """Get current RSA private key"""
    global privateKey
    if not privateKey:
        createRSAKeys()
    return privateKey

# 
def getMethod(challenge):
    return challenge.split(":")[0]

def getWelcomeString(method = "md5"):
    """Return welcome string (typically a challenge)"""
    if method == "plain":
        return "plain:"       
    elif method == "md5":
        return "md5:" + hashlib.md5(str(time.time())).hexdigest()
    elif method == "sha256":
        return "sha256:" + hashlib.sha256(str(time.time())).hexdigest()
    elif method == "rsa":
        publicKey = getPublicKey()
        return "rsa:%s:%s" % (publicKey.n, publicKey.e)
    raise SecurityException("Unsupported authentication method %s" % str(method))

def encode(password, challenge):
    """Encode password using auth method specified in the challenge"""
    method = getMethod(challenge)
    if method == "plain":
        return password
    elif method == "md5" or challenge.startswith("IGEServer@"):
        return hashlib.md5(password + challenge).hexdigest()
    elif method == "sha256":
        return hashlib.sha256(password + challenge).hexdigest()
    elif method == "rsa":
        dummy, n, e = challenge.split(":")
        key = rsa.PublicKey(int(n), int(e))
        return binascii.hexlify(rsa.encrypt(password, key)) 
    raise SecurityException("Unsupported authentication method %s" % str(method))

def verify(encodedPassword, password, challenge):
    """Verify password based on client encoded password and auth method"""
    method = getMethod(challenge)
    return processUserPassword(encodedPassword, challenge) == processStoredPassword(password, challenge)

def processUserPassword(password, challenge):
    """Decode password according to auth method (if possible)"""
    method = getMethod(challenge)
    if method == "plain":
        return password
    elif method == "md5" or challenge.startswith("IGEServer@"):
        return password
    elif method == "sha256":
        return password
    elif method == "rsa":
        return rsa.decrypt(binascii.unhexlify(password), getPrivateKey())
    raise SecurityException("Unsupported authentication method %s" % str(method))

def processStoredPassword(password, challenge):
    """Encode stored password for comparison with user provided password"""
    method = getMethod(challenge)
    if method == "plain":
        return password
    elif method == "md5" or challenge.startswith("IGEServer@"):
        return hashlib.md5(password + challenge).hexdigest()
    elif method == "sha256":
        return hashlib.sha256(password + challenge).hexdigest()
    elif method == "rsa":
        return password
    raise SecurityException("Unsupported authentication method %s" % str(method))
