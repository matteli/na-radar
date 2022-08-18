NA-Radar
========
Detect aircraft mouvement at Nantes-Atlantique Airport:
- take-off
- landing
- mouvement during the curfew
- by the south or by the north

Installation
------------
You need some programs and library (python >= 3.8, git, libatlas-base-dev, poetry).
On debian 11 or ubuntu >= 20.04 make :
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
