.. _ch_inst_guide:

環境構築
========

本書では、`Ryu`_ 、`Open vSwitch`_ および `Mininet`_ の最新版が
インストールされている環境を想定しています。

本書のための環境を整えるには、`Docker <https://www.docker.com/>`_ を
利用する方法が最も簡単です。

- `Ryu-Book 用 Docker イメージ <https://hub.docker.com/r/osrg/ryu-book/>`_
  を使う方法

  .. rst-class:: console

  ::

    $ docker run -it --privileged -e DISPLAY=$DISPLAY \
                 -v /tmp/.X11-unix:/tmp/.X11-unix \
                 -v /lib/modules:/lib/modules \
                 osrg/ryu-book


もし手動で環境を整えたい場合は、下記を参照ください。
また、`Open vSwitch`_ および `Mininet`_ のインストール時に問題が起きた場合は、
それぞれのプロジェクトのHPを参照ください。

- `Ryu`_

  .. rst-class:: console

  ::

    $ sudo apt-get install git python-dev python-setuptools python-pip
    $ git clone https://github.com/osrg/ryu.git
    $ cd ryu
    $ sudo pip install .

- `Open vSwitch`_

  こちらの `Open vSwitch インストール手順 <https://github.com/openvswitch/ovs/blob/master/INSTALL.md>`_
  参照ください。

- `Mininet`_

  こちらの `Mininet インストール手順 <https://github.com/mininet/mininet/blob/master/INSTALL>`_
  参照ください。


.. _Ryu: https://github.com/osrg/ryu/

.. _Open vSwitch: http://openvswitch.org/

.. _Mininet: http://mininet.org/
