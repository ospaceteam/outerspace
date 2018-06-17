[![Build Status](https://travis-ci.org/ospaceteam/outerspace.svg?branch=master)](https://travis-ci.org/ospaceteam/outerspace)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/ospaceteam/outerspace/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/ospaceteam/outerspace/issues/master)

# About Outer Space

Outer Space is turn-base 4X multiplayer on-line strategy game. Your goal is to become an Imperator of the Galaxy, racing other human players for supremacy via diplomacy, economic strength of you empire and research. And if all other means fail, you may subdue your neighbours with you powerful fleets and superior strategic thinking.

## Getting started
The ```outerspace``` project consists of two big parts. One is graphic client, providing everything player needs to enjoy the game. Then there is a server side, with game server itself and AI framework.

### Installation
#### Requirements
* ```python-2.7```
* ```pygame-1.9.2``` (for game client only)

#### Python
Outerspace is written in Python2, ```Python 2.7``` to be more specific. You can grab it on [official pages](https://www.python.org/downloads/release/python-2713/), or in the repositories of you linux distributions. While selecting components during installation, make sure to have ```pip``` component enabled. On Windows machines, for advanced use of ```outerspace```, it is also helpful to select ```Add python.exe to Path```.

#### PyGame
*Outer Space client is able to install the PyGame requirement automatically. It will be installed  for active user only, so no administrator rights are needed.*

#### Getting the Outer Space code
The Outer Space itself has no specific needs, all you have to do is to clone git repository, or download [ZIP file with the latest version](https://github.com/ospaceteam/outerspace/releases/latest) and unpack it in directory of you choice.

### Running Outer Space

For playing on official (default) server, all you have to do is to run ```outerspace.py``` script without any parameters (On *Windows*, it should be enough to execute the script from a file browser.) In case of running game from command line, all needed is

```
python2 ./outerspace.py
```

*NOTE:* If Outer Space fails during installation of ```PyGame``` (might occur during first run), it is most likely caused by ```pip``` package being too old. You can update it with command

```
python2 -m pip install -U pip
```
this will require administrator access, though.

## Non-default configuration

*NOTE (Windows):* It is highly advisable to follow steps described in [Using Python on Windows guide](https://docs.python.org/2.7/using/windows.html).

### Running a game client
In case the Server is running on ```non-default remote machine```, you need to know IP address of the Server and port on which the Server listens. Then you run the game with command

```
python2 ./outerspace.py client --server HOSTNAME:PORT_SERVER
```

In case you want to login to your local Server, you can do it easily by using.

```
python2 ./outerspace.py client --local
```

### Server side
To achieve full functionality, you have to start main Server, then you have to set up turn ticks of the server as well as periodic triggering of the AI subsystem.

#### Game server
Server can be simply run with command

```
python2 ./outerspace.py server
```
which will start server listening to default TCP port 9080 on all networks.


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


