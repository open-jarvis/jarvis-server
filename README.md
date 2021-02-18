# Jarvis Server

Jarvis backend and which handles incoming data from mobile phones and smart devices

## Installation Options

* [Jarvis Disk Image (TODO)](#TODO)
* [Jarvis Installer](https://github.com/open-jarvis/jarvis)
* [Plain Installation (This README)](#installation)

## Installation

### Upgrade your system

``` bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3 python3-pip
```

### Install the Database

```bash
# TAKEN FROM https://github.com/jguillod/couchdb-on-raspberry-pi
wget http://packages.erlang-solutions.com/debian/erlang_solutions.asc
sudo apt-key add erlang_solutions.asc
sudo apt-get update

# install essentials
sudo apt-get --no-install-recommends -y install build-essential \
pkg-config erlang libicu-dev \
libmozjs185-dev libcurl4-openssl-dev

# create couchdb user and directories
COUCHDB_DIR=/home/couchdb
sudo useradd -d $COUCHDB_DIR couchdb
sudo mkdir $COUCHDB_DIR
sudo chown couchdb:couchdb $COUCHDB_DIR
sudo chmod 1777 $COUCHDB_DIR
sudo mkdir $COUCHDB_DIR/logs
sudo touch $COUCHDB_DIR/logs/stdout.log
sudo touch $COUCHDB_DIR/logs/stderr.log

# install pip packages
sudo pip3 install --upgrade couchdb2

# install service file
sudo wget https://raw.githubusercontent.com/open-jarvis/jarvis/master/web/scripts/couchdb.service -q -O /etc/systemd/system/couchdb.service 

# Get source - need URL for mirror (see post instructions, above)
wget https://mirror.klaus-uwe.me/apache/couchdb/source/3.1.1/apache-couchdb-3.1.1.tar.gz
tar zxvf apache-couchdb-3.1.1.tar.gz
cd apache-couchdb-3.1.1

# configure build and make executable(s)
./configure
make release

# copy built release to couchdb user home directory
cd ./rel/couchdb/
sudo cp -Rp * $COUCHDB_DIR
sudo chown -R couchdb:couchdb $COUCHDB_DIR
cd $COUCHDB_DIR/etc

# change access rights
sudo chmod 666 $COUCHDB_DIR/etc/local.ini

# enable couchdb service
sudo systemctl daemon-reload
sudo systemctl enable couchdb.service
sudo systemctl start couchdb.service
```

### Install the Jarvis Code

``` bash
sudo pip3 install --upgrade open-jarvis

git clone https://github.com/open-jarvis/jarvis-server

sudo python3 jarvis-server/setup.py
# launch installer script
# and follow the instructions
```
