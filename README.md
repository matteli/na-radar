NA-Radar
========
NA-Radar is a website that allows you to follow the conditions (area, curfew) of aircraft takeoffs and landings at an airport.

Introduction
------------
This software is divided into 3 programs:
- na-radar is the program that detects and tracks airplanes and puts that into a sqlite database.
- na-dash-visualize is the program that allows you to see the charts in a browser. It uses Dash and has live tracking but it takes a long time to install because of the compilation of numpy and pandas and is hard to style.
- na-flask-visualize is the program that allows you to see the graphics in a browser. It does not use Dash and is very light but there is no live tracking.

Installation
------------
### with na-dash-visualize
You need some programs and library (python >= 3.8, git, libatlas-base-dev, poetry).
This commands is for debian 11 or ubuntu >= 20.04
```
apt install git libatlas-base-dev
curl -sSL https://install.python-poetry.org | python3 -
```
Copy files
```
git clone https://github.com/matteli/na-radar.git
```
Enter the directory and init
```
cd na-radar
poetry init
```
This takes a lot of time because of the compilation of numpy and pandas.

### without na-dash-visualize
You need some programs and library (python >= 3.8, git, poetry).
This commands is for debian 11 or ubuntu >= 20.04
```
apt install git libatlas-base-dev
curl -sSL https://install.python-poetry.org | python3 -
```
Copy files
```
git clone https://github.com/matteli/na-radar.git
```
Enter the directory, open the pyproject.toml
```
cd na-radar
nano pyproject.toml
```
Remove line with dash and pandas in [tool.poetry.dependencies] and init
```
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
Create a service for na-flask-visualize
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
ExecStart=/home/{user}/.cache/pypoetry/virtualenvs/{folder of env}/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 -m 007 na_visualize.na_flask_visualize:app

[Install]
WantedBy=multi-user.target
```
For using na_dash_visualize instead of na_flask_visualize, change the line ExecStart by
```
ExecStart=/home/{user}/.cache/pypoetry/virtualenvs/{folder of env}/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 -m 007 na_visualize.na_dash_visualize:application
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