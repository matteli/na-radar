NA-Radar
========
NA-Radar is a website that allows you to follow the conditions (area, curfew) of aircraft takeoffs and landings at an airport.

Introduction
------------
This software is divided into 2 programs:
- na-radar is the program that detects and tracks airplanes and puts that into a sqlite database.
- na-flask-visualize is the program that allows you to see the charts in a browser.

Installation
------------
You need some programs and library (python >= 3.8, git, poetry).
This commands is for debian 11 or ubuntu >= 20.04
```
apt install git
curl -sSL https://install.python-poetry.org | python3 -
```
Copy files
```
git clone https://github.com/matteli/na-radar.git
```
Enter the directory and init the app
```
cd na-radar
poetry init
```

Running
-------
Create a service for na-radar
```
nano /etc/systemd/system/na_radar.service
```
and put this in the file (replace {})
```
Unit]
Description=na-radar
After=network.target

[Service]
User={user}
Group={user}
WorkingDirectory=/home/{user}/na-radar/
Environment="PATH=/home/{user}/.cache/pypoetry/virtualenvs/{folder of env}/bin"
ExecStart=/home/{user}/.cache/pypoetry/virtualenvs/{folder of env}/bin/python3 na_radar/na_radar.py

[Install]
WantedBy=multi-user.target
```
Create a service for na-visualize
```
nano /etc/systemd/system/na_visualize.service
```
and put this in the file (replace {})
```
[Unit]
Description=na-visualize
After=network.target

[Service]
User={user}
Group={user}
WorkingDirectory=/home/{user}/na-radar/
Environment="PATH=/home/{user}/.cache/pypoetry/virtualenvs/{folder of env}/bin"
ExecStart=/home/{user}/.cache/pypoetry/virtualenvs/{folder of env}/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 -m 007 na_visualize.na_visualize:app

[Install]
WantedBy=multi-user.target
```
Reload systemd deamon
```
systemctl daemon-reload
```
Now you can start na-radar
```
systemctl start na_radar
```
and after start na-visualize
```
systemctl start na_visualize
```
The website is accessible at
```
http://localhost:5000
```