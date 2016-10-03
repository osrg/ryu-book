.. _ch_inst_guide:

Installation Guide
==================

This document supposes and requires the latest version of `Ryu`_,
`Open vSwitch`_ and `Mininet`_ should have been installed on your machine.

For the easiest way to build the environment for this document, you can use
the `Docker <https://www.docker.com/>`_ image for Ryu-Book.

- Using `the Docker image for Ryu-Book <https://hub.docker.com/r/osrg/ryu-book/>`_

  .. rst-class:: console

  ::

    $ docker run -it --privileged -e DISPLAY=$DISPLAY \
                 -v /tmp/.X11-unix:/tmp/.X11-unix \
                 -v /lib/modules:/lib/modules \
                 osrg/ryu-book


If you want to build the Ryu-Book environment manually, please refer to the
following.
And if you have some trouble when installing `Open vSwitch`_ and `Mininet`_,
please find more information on each project homepage.

- `Ryu`_

  .. rst-class:: console

  ::

    $ sudo apt-get install git python-dev python-setuptools python-pip
    $ git clone https://github.com/osrg/ryu.git
    $ cd ryu
    $ sudo pip install .

- `Open vSwitch`_

  See this `INSTALL.md of Open vSwitch <https://github.com/openvswitch/ovs/blob/master/INSTALL.md>`_

- `Mininet`_

  See this `INSTALL of Mininet <https://github.com/mininet/mininet/blob/master/INSTALL>`_


.. _Ryu: https://github.com/osrg/ryu/

.. _Open vSwitch: http://openvswitch.org/

.. _Mininet: http://mininet.org/