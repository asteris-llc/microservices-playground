#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
bootstrap a Mesos cluster.

Usage: ``./marathon.py --zk zk://your.host:2181/marathon --master zk://your.host:2181/mesos``

Note: please don't supply ``--ha`` or ``--http_port`` - this script depends on
their defaults. To get a highly-available cluster, please instead set
``MARATHON_INSTANCES`` greater than 1 (the default is 3), this script will add
the argument in the appropriate place.
"""
from __future__ import print_function, unicode_literals
import json
import os
from subprocess import Popen, PIPE, call
import sys
import time
import urllib
import urllib2


#: Image to use for Marathon - defaults to the official image at the latest
#: tag.
MARATHON_IMAGE = os.getenv('MARATHON_IMAGE', 'mesosphere/marathon:v0.7.5')

#: Number of instances to spin up after the initial bootstrap - it should be
#: greater than 1 if you want a highly available cluster (and in fact the
#: cluster will be marked as highly available if that condition is met.)
MARATHON_INSTANCES = int(os.getenv('MARATHON_INSTANCES', '3'))
USE_HA = MARATHON_INSTANCES > 1

#: Marathon's app ID when scheduling itself
MARATHON_APP_ID = os.getenv('MARATHON_APP_ID', '/marathon/marathon')


def run(command, stdin=None):
    """
    run, capturing stdin, stdout, and stderr.

    :param command: command to run
    :param str stdin: string to capture
    :returns: ``(stdout, stderr)``
    :rtype tuple:
    """
    cmd = Popen(command, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    return cmd.communicate(stdin)


def _wait_for_port(address):
    for i in range(1, 6):
        try:
            urllib.urlopen(address).read()
        except IOError:
            print('%s unavailable, trying in %ds...' % (
                address,
                2 ** i
            ))
            time.sleep(2 ** i)
            continue

        return

    sys.stderr.write(
        'Could not contact %s in a reasonable amount of time, exiting.' % address
    )
    sys.exit(1)


def main(args):
    """
    bootstrap a marathon cluster, using the environment variables specified in
    this file but otherwise passing all args supplied on the command line to
    Marathon.

    :param args: list of argument passed in on the command line
    """
    name = 'marathon_bootstrap'
    # start local Marathon daemon
    _, err = run(
        [
            'docker', 'run',
            '--detach',
            '--publish', '8080',
            '--name', name,
            MARATHON_IMAGE
        ] + args
    )
    if err:
        sys.stderr.write(err)
        sys.exit(1)

    info_raw, err = run(['docker', 'inspect', name])
    if err:
        sys.stderr.write(err)
        sys.exit(1)

    info = json.loads(info_raw)
    port_info = info[0]["NetworkSettings"]["Ports"]["8080/tcp"][0]

    print("Local marathon container launched, waiting for port.")

    _wait_for_port("http://{HostIp}:{HostPort}/ping".format(**port_info))

    # start more Marathon daemons via Marathon
    if USE_HA and '--ha' not in args:
        args.append('--ha')

    job_spec = json.dumps({
        "id": MARATHON_APP_ID,
        "container": {
            "docker": {
                "image": MARATHON_IMAGE,
                "network": "BRIDGE",
                "portMappings": [
                    {
                        "containerPort": 8080,
                        "servicePort": 8080,
                    },
                    {
                        "containerPort": 8443,
                        "servicePort": 8443,
                    },
                ],
                # TODO: volumes
            },
        },
        "instances": MARATHON_INSTANCES,

        "cpus": 0.5,
        "mem": "1024",

        "args": args,

        # TODO: environment, specifically consul tags
    })

    print("Marathon has become available, launching cluster.")
    resp = urllib2.urlopen(urllib2.Request(
        "http://{HostIp}:{HostPort}/v2/apps".format(**port_info),
        job_spec,
        {'Content-Type': 'application/json'}
    ))
    app = json.load(resp)

    while True:
        tasks_resp = urllib.urlopen(
            "http://{HostIp}:{HostPort}/v2/tasks".format(**port_info)
        )
        resp_raw = tasks_resp.read()
        tasks = json.loads(resp_raw)

        if not [t for t in tasks["tasks"] if t["appId"] == MARATHON_APP_ID]:
            print('No marathon tasks available, trying in 5s...')
            time.sleep(5)
            continue

        break

    print("Cluster launched, waiting for tasks to become available.")
    for task in [t for t in tasks["tasks"] if t["appId"] == MARATHON_APP_ID]:
        ports = dict(zip(task["servicePorts"], task["ports"]))
        url = "http://{host}:{port}/ping".format(
            port=ports[8080],
            **task
        )
        _wait_for_port(url)
        print("%s is available" % url)

    # finally, take down the original container, which we don't need anymore
    _, err = run(['docker', 'rm', '-f', name])
    if err:
        sys.stderr.write(err)
        sys.exit(1)

    print 'Cluster is up, have fun!'


if __name__ == '__main__':
    if not sys.argv[1:]:
        print(__doc__)
        sys.exit(1)

    main(sys.argv[1:])
