from ige import SecurityException
import hashlib
import time

# default method is set to MD5 for backward compatibility
# with version 0.5.68 (revision 308)
defaultMethod = "md5"

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
    raise SecurityException("Unsupported authentication method %s" % str(method))

def encode(password, challenge):
    """Encodes password using auth method specified in the challenge"""
    method = getMethod(challenge)
    if method == "plain":
        return password
    elif method == "md5" or challenge.startswith("IGEServer@"):
        return hashlib.md5(password + challenge).hexdigest()
    elif method == "sha256":
        return hashlib.sha256(password + challenge).hexdigest()
    raise SecurityException("Unsupported authentication method %s" % str(method))

def verify(encodedPassword, password, challenge):
    """Verifies password based on client encoded password and auth method"""
    method = getMethod(challenge)
    if method == "plain":
        return encodedPassword == password
    elif method == "md5" or challenge.startswith("IGEServer@"):
        return hashlib.md5(password + challenge).hexdigest() == encodedPassword
    elif method == "sha256":
        return hashlib.sha256(password + challenge).hexdigest() == encodedPassword
    raise SecurityException("Unsupported authentication method %s" % str(method))
