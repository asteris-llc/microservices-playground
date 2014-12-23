#!/bin/bash

set -x 

sudo systemctl stop zookeeper
sudo docker ps -a | grep zoo | awk '{print $1}' | xargs docker rm 
sudo docker rmi asteris/zookeeper
sudo rm /etc/default/zookeeper
sudo systemctl disable zookeeper
sudo systemctl daemon-reload
