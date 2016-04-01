## Ryu-Book Dockerfile

This **Dockerfile** provides the Docker image for
[Ryu-Book](http://osrg.github.io/ryu-book/en/html/index.html) published to
the public [Docker Registry](https://index.docker.io/).


### Installation

1. Install [Docker](https://www.docker.io/).

1. Download from public Docker Registry:

    `$ docker pull osrg/ryu-book`


### Usage

1. Before running containers, please enable "root" user to open X11
applications for [Mininet](http://mininet.org/):

    `$ sudo xhost +si:localuser:root`

1. Run Ryu-Book container.

    - With `docker run` command:

        ```
        $ docker run -it --privileged -e DISPLAY=$DISPLAY \
                      -v /tmp/.X11-unix:/tmp/.X11-unix \
                      -v /lib/modules:/lib/modules \
                      osrg/ryu-book
        ```

    - If you have installed [Docker Compose](https://docs.docker.com/compose/),
      you can run Ryu-Book container with:

        ```
        $ wget https://github.com/osrg/ryu-book/raw/master/docker/docker-compose.yml

        $ docker-compose run --rm ryu-book
        ```


### Running containers via SSH

If your Docker host is on SSH server and you are accessing via SSH,
some X11 applications may not be able to open display though X11 forwarding
tunnels.
In this case, please try the following `docker run` option to open `xterm`
or other X11 applications on containers.

```
$ docker run -it --privileged -e DISPLAY=$DISPLAY \
                  -v $HOME/.Xauthority:/root/.Xauthority \
                  -v /lib/modules:/lib/modules \
                  --network host \
                  osrg/ryu-book
```
