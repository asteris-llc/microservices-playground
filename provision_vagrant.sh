#!/usr/bin/env bash
ansible-playbook --private-key=~/.vagrant.d/insecure_private_key --user=vagrant --limit='all' --inventory-file=.vagrant/provisioners/ansible/inventory vagrant_playbook.yml
