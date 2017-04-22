# Outer Space

Outer Space is turn-base 4X multiplayer on-line strategy game. Your goal is to get elected as an Imperator of the Galaxy, racing other human players for supremacy via diplomacy, strength of economy and research. And if all other means fail, you may subdue them with you powerful fleets and superior strategic thinking.

## Getting started
Setup of ```outerspace``` differs, whether you want to play on already running server, or you want to setup server of your own. 

### Running a game client
In case the server is running on ```remote machine```, you need to know IP address of the server, and ports on which the Server and Galaxer listen. Then you run the game with command

```
./outerspace.py client --server HOSTNAME:PORT_SERVER --galaxer http://HOSTNAME:PORT_GALAXER
```

By default both of these parameters points to localhost, so in case you want to login to your local Server and local Galaxer,
it's even simpler

```
./outerspace.py client
```

### Server side
To achieve full functionality, you have to start main Server, Galaxer for player queuing new galaxies, then you have to set up turn ticks of the server as well as periodic triggering of the AI subsystem.

#### Game server
Server can be simply run with command

```
./outerspace.py server
```
which will start server listening to default TCP port 9080 on all networks.

**NOTE:** if you are running it for the first time, you have to prepare database with
```
./outerspace.py server --reset
```
and then run it again without the ```--reset``` flag.

#### Galaxer
Next step is to run Galaxer, in very similar fashion. Most common scenario is Galaxer running on the same machine as main server, in which case no arguments are necessary.
```
./outerspace.py galaxer
```

In case server runs on remote machine, add parameter to define IP address and port
```
./outerspace.py client --server HOSTNAME:PORT_SERVER 
```

#### Ticking game server
For triggering a turn, you have to run
```
./tools/osclient_cli.py -t admin
```
on the server machine. For example official server had this as a cron job, one turn per hour of working day, and once per two hours during a weekends.

**NOTE:** if you have fresh server, and you want to play in the very moment, you'll want to start time in the first galaxy with ```--starttime``` option. 

#### AI
AI is implemented as a headless client, utilizing same API the graphics client does. That means it has to be triggered every turn to connect to the server and issue new commands based on current situation. Also ```./outerspace.py``` script provides two ways of running an AI. In this guide only ```ai-pool``` is interesting for us, as it goes through all AI players currently active in the game. Also running this on remote machine would be a bit tricky, as it consumes data dump in the server config directory.

```
./outerspace.py ai-pool
```

is all you need to execute for AI to get alive.


