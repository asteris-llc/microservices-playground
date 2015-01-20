microservices-playground
========================

An opinionated framework for prototyping new ideas.

Vagrant
-------

Vagrant is set to create 3 nodes and bootstrap consul on each of them. To use
this, make sure [vagrant]() and [virtualbox]() are installed, and run `vagrant
up`. By default, the consul nodes on each host are not connected (although this
will change in the future.) You may connect them by logging into one of the
boxes and running the following:

```
$ docker run -i -t --entrypoint=/bin/bash --link consul:consul progrium/consul
bash-4.3# consul join 10.0.33.11 --rpc-addr=$CONSUL_PORT_8400_TCP_ADDR:$CONSUL_PORT_8400_TCP_PORT
bash-4.3# consul join 10.0.33.12 --rpc-addr=$CONSUL_PORT_8400_TCP_ADDR:$CONSUL_PORT_8400_TCP_PORT
bash-4.3# consul join 10.0.33.13 --rpc-addr=$CONSUL_PORT_8400_TCP_ADDR:$CONSUL_PORT_8400_TCP_PORT
```

(removing the address of the box you're running the command from, of course.)
