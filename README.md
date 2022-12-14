NA-Radar
========
NA-Radar is a website that allows you to follow the conditions (area, curfew) of aircraft takeoffs and landings at an airport.  
*NA-Radar uses data from [Flightradar24](https://www.flightradar24.com/). As stated in the [Terms of Service](https://www.flightradar24.com/terms-and-conditions), a [business account](https://www.flightradar24.com/premium?utm_source=website&utm_medium=nav&utm_campaign=menu_subs) is required for any commercial use **or** any public display.*

Introduction
------------
This software is divided into 2 programs:
- na-radar is the program that detects and tracks airplanes and puts that into a sqlite database.
- na-visualize is the program that allows you to see the charts in a browser.

Installation
------------
In the followings lines, %user% is the curret user and it is a sudo user.  
You need some programs (python >= 3.8, git, poetry).  
This commands is for debian 11 or ubuntu >= 20.04
```
sudo apt install git
curl -sSL https://install.python-poetry.org | python3 -
```
Copy files
```
git clone https://github.com/matteli/na-radar.git
```
Enter the directory and install the app
```
cd na-radar
poetry install
```

Running
-------
Create a service for na-radar
```
sudo nano /etc/systemd/system/na_radar.service
```
and put this in the file
```
[Unit]
Description=na-radar
After=network.target

[Service]
User=%user%
Group=%user%
WorkingDirectory=/home/%user%/na-radar/
Environment="PATH=/home/%user%/.cache/pypoetry/virtualenvs/%folder of env%/bin"
ExecStart=/home/%user%/.cache/pypoetry/virtualenvs/%folder of env%/bin/python3 na_radar/na_radar.py

[Install]
WantedBy=multi-user.target
```
Create a service for na-visualize
```
sudo nano /etc/systemd/system/na_visualize.service
```
and put this in the file (replace {})
```
[Unit]
Description=na-visualize
After=network.target na_radar.service

[Service]
User=%user%
Group=%user%
WorkingDirectory=/home/%user%/na-radar/
Environment="PATH=/home/%user%/.cache/pypoetry/virtualenvs/%folder of env%/bin"
ExecStart=/home/%user%/.cache/pypoetry/virtualenvs/%folder of env%/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 -m 007 na_visualize.na_visualize:app

[Install]
WantedBy=multi-user.target
```
Reload systemd deamon
```
sudo systemctl daemon-reload
```
Now you can start na-radar
```
sudo systemctl start na_radar
```
and after start na-visualize
```
sudo systemctl start na_visualize
```
The website is accessible at
```
http://localhost:5000
```

Updating
--------
In the na-radar directory
```
git pull
poetry install
```
Restart the service
```
sudo systemctl restart na_radar
sudo systemctl restart na_visualize
```