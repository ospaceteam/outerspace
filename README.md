# About Outer Space

Outer Space is turn-base 4X multiplayer on-line strategy game. Your goal is to become an Imperator of the Galaxy, racing other human players for supremacy via diplomacy, economic strength of you empire and research. And if all other means fail, you may subdue your neighbours with you powerful fleets and superior strategic thinking.

## Getting started
The ```outerspace``` project consists of two big parts. One is graphic client, providing everything player needs to enjoy the game. Then there is a server side, with game server itself, plus Galaxer (daemon for starting a galaxies on-demand) and AI framework.

### Installation
#### Requirements
* ```python-2.7```
* ```pygame-1.9.1``` (for game client only)

#### Python
Outerspace is written in Python2, specifically ```Python 2.7``` is the supported version. You can grab it on [official pages](https://www.python.org/downloads/release/python-2713/), or in the repositories of you linux distributions.

*NOTE (Windows):* It is highly advisable to follow steps described in [Using Python on Windows guide](https://docs.python.org/2.7/using/windows.html).

#### PyGame
For proper function of game client, ```pygame``` library is also required, in version at least```pygame-1.9.1```. You can install it following a [GettingStarted guide](https://www.pygame.org/wiki/GettingStarted#Pygame%20Installation). Python3 used in the guide is not mandatory - you can use Python2 instead.

#### Getting the Outer Space code
The Outer Space itself has no specific needs, all you have to do is to clone git repository, or download [ZIP file with the latest version](https://github.com/dahaic/outerspace/archive/master.zip) and unpack it in directory of you choice.


### Running a game client
In case the server is running on ```remote machine```, you need to know IP address of the server, and ports on which the Server and Galaxer listen. Then you run the game with command

```
python2 ./outerspace.py client --server HOSTNAME:PORT_SERVER --galaxer http://HOSTNAME:PORT_GALAXER
```

By default both of these parameters points to localhost, so in case you want to login to your local Server and local Galaxer,
it's even simpler

```
python2 ./outerspace.py client
```

### Server side
To achieve full functionality, you have to start main Server, Galaxer for player queuing new galaxies, then you have to set up turn ticks of the server as well as periodic triggering of the AI subsystem.

#### Game server
Server can be simply run with command

```
python2 ./outerspace.py server
```
which will start server listening to default TCP port 9080 on all networks.

*NOTE:* if you are running it for the first time, you have to prepare database with
```
python2 ./outerspace.py server --reset
```
and then run it again without the ```--reset``` flag.

#### Galaxer
Next step is to run Galaxer, in very similar fashion. Most common scenario is Galaxer running on the same machine as main server, in which case no arguments are necessary.
```
python2 ./outerspace.py galaxer
```

In case server runs on remote machine, add parameter to define IP address and port
```
python2 ./outerspace.py client --server HOSTNAME:PORT_SERVER 
```

#### Ticking game server
For triggering one turn, you have to run
```
python2 ./tools/osclient_cli.py --turns=1 admin
```
on the server machine. For example official server had this as a cron job, one turn per hour of working day, and once per two hours during a weekends.

*NOTE:* In case you want faster gaming modes, it is suggested to combine shorter ticks with bigger batches of turns evaluated at once by altering the command above. For usability reasons, it is not recommended to have ticks shorter than three minutes.

If you have fresh server, and you want to start playing, you'll want to skip grace period with command
```
python2 ./tools/osclient_cli.py --starttime admin
```

#### Setting up AI
AI is implemented as a headless client, utilizing same API the graphics client does. That means it has to be triggered every turn to connect to the server and issue new commands based on current situation. Also ```./outerspace.py``` script provides two ways of running an AI. In this guide only ```ai-pool``` is interesting for us, as it goes through all AI players currently active in the game. Also running this on remote machine would be a bit tricky, as it consumes data dump in the server config directory.

```
python2 ./outerspace.py ai-pool
```

is all you need to execute for AI to get alive.


