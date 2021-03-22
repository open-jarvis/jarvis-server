# Jarvis Server

Jarvis backend and which handles incoming data from mobile phones and smart devices

## Installation Options

* [Jarvis Disk Image (TODO)](#TODO)
* [Jarvis Installer](https://github.com/open-jarvis/jarvis)
* [Source Installation](#source-installation)
    - [Raspberry PI](#rasperry-pi)
    - [Ubuntu](#ubuntu)

## Source Installation

### Raspberry Pi

#### Upgrade your system

``` bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3 python3-pip
sudo -H pip3 install --upgrade open-jarvis
```

#### Install the Database

``` bash
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

echo "########## MODIFY /home/couchdb/etc/local.ini ##########"
echo "change ';admin = password' to 'jarvis = jarvis'"
echo "change ';bind_address = 127.0.0.1' to 'bind_address = 0.0.0.0'"
echo "########################################################"
sleep 20

# enable couchdb service
sudo systemctl daemon-reload
sudo systemctl enable couchdb.service
sudo systemctl start couchdb.service

# install NLU
sudo -H pip3 install snips-nlu
```

#### Install the Jarvis Code

``` bash
git clone https://github.com/open-jarvis/server

cd server
sudo python3 setup.py
# Follow the instructions
```

### Ubuntu

#### Upgrade the system

``` bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl python3 python3-pip
```

#### Install the Database inside a Docker container
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
su - $USER

mkdir .couchdb-data
docker pull couchdb
docker run \
    --restart=always \
    -p 5984:5984 \
    -v /home/$USER/.couchdb-data:/opt/couchdb/data \
    -e COUCHDB_USER="jarvis" \
    -e COUCHDB_PASSWORD="jarvis" \
    -d couchdb
```

#### Install the Jarvis code
```bash
sudo apt install -y mosquitto python3-paho-mqtt
sudo -H pip3 install --upgrade open-jarvis
git clone https://github.com/open-jarvis/server
cd server
sudo python3 setup.py
```

The Jarvis server is now up and running.  
You should now think about installing an <a href="https://github.com/open-jarvis/web">assistant</a>
