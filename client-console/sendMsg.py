# tweak PYTHONPATH
import sys
sys.path.insert(0, '../server/lib')

from igeclient.IClient import IClient
import string
from getpass import getpass

def msgHandler(id, data):
	if id >= 0:
		print 'Message', id, data

if len(sys.argv) != 4:
	print "Usage: %s objID forum filename"
	sys.exit(1)

s = IClient('ospace.net:9080', None, msgHandler, None, 'IClient/sendMsg')
#s = IClient('localhost:9080', None, msgHandler, 'IClient/0.3.0')

password = getpass("Password: ")

s.connect('admin')
s.login('Alpha', 'admin', password)

_, objID, forum, filename = sys.argv

fh = open(filename)
data = fh.read()
data = unicode(data, "cp1250").split("\n")

message = {
	"sender": "Admin",
	"senderID": 10,
	"forum": forum,
	"topic": data[0],
	"language": "en",
	"text": string.join(data[1:], "\n")
}

s.sendAdminMsg(int(objID), message)

print "Message send."

s.logout()
