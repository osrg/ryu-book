# Ryu-Book

FROM osrg/ryu
ARG user=osrg

MAINTAINER IWASE Yusuke <iwase.yusuke0@gmail.com>

COPY ENTRYPOINT.sh /

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    iproute2 \
    iputils-ping \
    mininet \
    net-tools \
    tcpdump \
    vim \
    x11-xserver-utils \
    xterm \
 && mv /usr/sbin/tcpdump /usr/bin/tcpdump \
 && rm -rf /var/lib/apt/lists/* \
 && chmod +x /ENTRYPOINT.sh

ENTRYPOINT ["/ENTRYPOINT.sh"]
