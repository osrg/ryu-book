.. _ch_link_aggregation:

リンク・アグリゲーションの実装
==============================

本章では、Ryuを用いたリンク・アグリゲーション機能の実装方法を解説していきま
す。


リンク・アグリゲーション
------------------------

リンク・アグリゲーションは、IEEE802.1AX-2008で規定されている、複数の物理的な
回線を束ねてひとつの論理的なリンクとして扱う技術です。リンク・アグリゲーション
機能により、特定のネットワーク機器間の通信速度を向上させることができ、また同時
に、冗長性を確保することで耐障害性を向上させることができます。

.. only:: latex

  .. image:: images/link_aggregation/fig1.eps
     :align: center

.. only:: epub

  .. image:: images/link_aggregation/fig1.png
     :align: center

.. only:: not latex and not epub

  .. image:: images/link_aggregation/fig1.png
     :scale: 80%
     :align: center

リンク・アグリゲーション機能を使用するには、それぞれのネットワーク機器において、
どのインターフェースをどのグループとして束ねるのかという設定を事前に行っておく
必要があります。

リンク・アグリゲーション機能を開始する方法には、それぞれのネットワーク機器に
対し直接指示を行うスタティックな方法と、LACP
(Link Aggregation Control Protocol)というプロトコルを使用することによって
動的に開始させるダイナミックな方法があります。

ダイナミックな方法を採用した場合、各ネットワーク機器は対向インターフェース同
士でLACPデータユニットを定期的に交換することにより、疎通不可能になっていない
ことをお互いに確認し続けます。LACPデータユニットの交換が途絶えた場合、故障が
発生したものとみなされ、当該ネットワーク機器は使用不可能となり、パケットの送
受信は残りのインターフェースによってのみ行われるようになります。この方法には、
ネットワーク機器間にメディアコンバータなどの中継装置が存在した場合にも、中継
装置の向こう側のリンクダウンを検知することができるというメリットがあります。
本章では、LACPを用いたダイナミックなリンク・アグリゲーション機能を取り扱いま
す。


Ryuアプリケーションの実行
-------------------------

ソースの説明は後回しにして、まずはRyuのリンク・アグリゲーション・アプリケー
ションを実行してみます。

Ryuのソースツリーに用意されているsimple_switch_lacp.pyはOpenFlow 1.0専用
のアプリケーションであるため、ここでは新たにOpenFlow 1.3に対応した
simple_switch_lacp_13.pyを作成することとします。このプログラムは、
「 :ref:`ch_switching_hub` 」のスイッチングハブにリンク・アグリゲーション機能を
追加したアプリケーションです。

ソース名： ``simple_switch_lacp_13.py``

.. rst-class:: sourcecode

.. literalinclude:: sources/simple_switch_lacp_13.py


実験環境の構築
^^^^^^^^^^^^^^

リンク・アグリゲーション・アプリケーションの動作確認を行う実験環境を構築します。

VMイメージ利用のための環境設定やログイン方法等は「 :ref:`ch_switching_hub` 」
を参照してください。

最初に「 :ref:`ch_switching_hub` 」と同様にMininetを実行しますが、下図の
ように「ホストh1とスイッチs1の間に2本のリンクが存在する」という特殊なトポロ
ジであるため、mnコマンドで作成することができません。

    .. only:: latex

       .. image:: images/link_aggregation/fig2.eps
          :scale: 80 %
          :align: center

    .. only:: epub

       .. image:: images/link_aggregation/fig2.png
          :align: center

    .. only:: not latex and not epub

       .. image:: images/link_aggregation/fig2.png
          :scale: 80 %
          :align: center

ここではMininetの低位クラスを直接使用するスクリプトを作成し、実験環境を構築
することにします。

ソース名： ``link_aggregation.py``

.. rst-class:: sourcecode

.. literalinclude:: sources/link_aggregation.py

このスクリプトを実行することにより、ホストh1とスイッチs1の間に2本のリンクが
存在するトポロジが作成されます。netコマンドを実行することでトポロジを確認す
ることができます。

.. rst-class:: console

::

    ryu@ryu-vm:~$ sudo ./link_aggregation.py
    Unable to contact the remote controller at 127.0.0.1:6633
    mininet> net
    c0
    s1 lo:  s1-eth1:h1-eth0 s1-eth2:h1-eth1 s1-eth3:h2-eth0 s1-eth4:h3-eth0 s1-eth5:h4-eth0
    h1 h1-eth0:s1-eth1 h1-eth1:s1-eth2
    h2 h2-eth0:s1-eth3
    h3 h3-eth0:s1-eth4
    h4 h4-eth0:s1-eth5
    mininet>

また、このスクリプトを実行することにより、コントローラc0、ホストh1～h4、およ
びスイッチs1のxtermが起動します。


ホストh1でのリンク・アグリゲーションの設定
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ホストh1のxtermで、ホスト側のリンク・アグリゲーションの設定を行います。本節
でのコマンド入力は、すべてホストh1のxterm上で行ってください。

まず、リンク・アグリゲーションを行うためのドライバモジュールをロードします。
Linuxではリンク・アグリゲーション機能をボンディングドライバが担当しています。
事前にドライバの設定ファイルを/etc/modprobe.d/bonding.confとして作成してお
きます。

ファイル名: ``/etc/modprobe.d/bonding.conf``

.. rst-class:: sourcecode

::

    alias bond0 bonding
    options bonding mode=4

Node: h1:

.. rst-class:: console

::

    root@ryu-vm:~# modprobe bonding

mode=4はLACPを用いたダイナミックなリンク・アグリゲーションを行うことを表しま
す。デフォルト値であるためここでは設定を省略していますが、LACPデータユニット
の交換間隔はSLOW（30秒間隔）、振り分けロジックは宛先MACアドレスを元に行うよ
うに設定されています。

続いて、bond0という名前の論理インターフェースを新たに作成します。また、bond0
のMACアドレスとして適当な値を設定します。

Node: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ip link add bond0 type bond
    root@ryu-vm:~# ip link set bond0 address 02:01:02:03:04:08

作成した論理インターフェースのグループに、h1-eth0とh1-eth1の物理インター
フェースを参加させます。このとき、物理インターフェースをダウンさせておく必要
があります。また、ランダムに決定された物理インターフェースのMACアドレスを
わかりやすい値に書き換えておきます。

Node: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ip link set h1-eth0 down
    root@ryu-vm:~# ip link set h1-eth0 address 00:00:00:00:00:11
    root@ryu-vm:~# ip link set h1-eth0 master bond0
    root@ryu-vm:~# ip link set h1-eth1 down
    root@ryu-vm:~# ip link set h1-eth1 address 00:00:00:00:00:12
    root@ryu-vm:~# ip link set h1-eth1 master bond0

論理インターフェースにIPアドレスを割り当てます。mnコマンドでホストを作成した
場合にならって、10.0.0.1を割り当てることにします。また、h1-eth0にIPアドレス
が割り当てられているので、これを削除します。

Node: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr add 10.0.0.1/8 dev bond0
    root@ryu-vm:~# ip addr del 10.0.0.1/8 dev h1-eth0

最後に、論理インターフェースをアップさせます。

Node: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ip link set bond0 up

ここで各インターフェースの状態を確認しておきます。

Node: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ifconfig
    bond0     Link encap:Ethernet  HWaddr 02:01:02:03:04:08
              inet addr:10.0.0.1  Bcast:0.0.0.0  Mask:255.0.0.0
              UP BROADCAST RUNNING MASTER MULTICAST  MTU:1500  Metric:1
              RX packets:0 errors:0 dropped:0 overruns:0 frame:0
              TX packets:10 errors:0 dropped:0 overruns:0 carrier:0
              collisions:0 txqueuelen:0
              RX bytes:0 (0.0 B)  TX bytes:1240 (1.2 KB)

    h1-eth0   Link encap:Ethernet  HWaddr 02:01:02:03:04:08
              UP BROADCAST RUNNING SLAVE MULTICAST  MTU:1500  Metric:1
              RX packets:0 errors:0 dropped:0 overruns:0 frame:0
              TX packets:5 errors:0 dropped:0 overruns:0 carrier:0
              collisions:0 txqueuelen:1000
              RX bytes:0 (0.0 B)  TX bytes:620 (620.0 B)

    h1-eth1   Link encap:Ethernet  HWaddr 02:01:02:03:04:08
              UP BROADCAST RUNNING SLAVE MULTICAST  MTU:1500  Metric:1
              RX packets:0 errors:0 dropped:0 overruns:0 frame:0
              TX packets:5 errors:0 dropped:0 overruns:0 carrier:0
              collisions:0 txqueuelen:1000
              RX bytes:0 (0.0 B)  TX bytes:620 (620.0 B)

    lo        Link encap:Local Loopback
              inet addr:127.0.0.1  Mask:255.0.0.0
              UP LOOPBACK RUNNING  MTU:16436  Metric:1
              RX packets:0 errors:0 dropped:0 overruns:0 frame:0
              TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
              collisions:0 txqueuelen:0
              RX bytes:0 (0.0 B)  TX bytes:0 (0.0 B)

論理インターフェースbond0がMASTERに、物理インターフェースh1-eth0とh1-eth1が
SLAVEになっていることがわかります。また、bond0、h1-eth0、h1-eth1のMACアドレ
スがすべて同じものになっていることがわかります。

ボンディングドライバの状態も確認しておきます。

Node: h1:

.. rst-class:: console

::

    root@ryu-vm:~# cat /proc/net/bonding/bond0
    Ethernet Channel Bonding Driver: v3.7.1 (April 27, 2011)

    Bonding Mode: IEEE 802.3ad Dynamic link aggregation
    Transmit Hash Policy: layer2 (0)
    MII Status: up
    MII Polling Interval (ms): 100
    Up Delay (ms): 0
    Down Delay (ms): 0

    802.3ad info
    LACP rate: slow
    Min links: 0
    Aggregator selection policy (ad_select): stable
    Active Aggregator Info:
            Aggregator ID: 1
            Number of ports: 1
            Actor Key: 33
            Partner Key: 1
            Partner Mac Address: 00:00:00:00:00:00

    Slave Interface: h1-eth0
    MII Status: up
    Speed: 10000 Mbps
    Duplex: full
    Link Failure Count: 0
    Permanent HW addr: 00:00:00:00:00:11
    Aggregator ID: 1
    Slave queue ID: 0

    Slave Interface: h1-eth1
    MII Status: up
    Speed: 10000 Mbps
    Duplex: full
    Link Failure Count: 0
    Permanent HW addr: 00:00:00:00:00:12
    Aggregator ID: 2
    Slave queue ID: 0

LACPデータユニットの交換間隔(LACP rate: slow)や振り分けロジックの設定
(Transmit Hash Policy: layer2 (0))が確認できます。また、物理インター
フェースh1-eth0とh1-eth1のMACアドレスが確認できます。

以上でホストh1のリンク・アグリゲーションの設定は終了です。


OpenFlowバージョンの設定
^^^^^^^^^^^^^^^^^^^^^^^^

「 :ref:`ch_switching_hub` 」で行ったのと同じように、使用するOpenFlowの
バージョンを1.3に設定します。このコマンド入力は、スイッチs1のxterm上で行っ
てください。

Node: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13


スイッチングハブの実行
^^^^^^^^^^^^^^^^^^^^^^

準備が整ったので、冒頭で作成したRyuアプリケーションを実行します。

.. ATTENTION::

    本Ryuアプリケーションはライブラリとしてlacplib.pyを使用しますが、
    Ryu3.2に含まれているlacplib.pyには不具合があります。Ryu3.3以降をご利用
    ください。

ウインドウタイトルが「Node: c0 (root)」となっている xterm から次のコマンド
を実行します。

Node: c0:

.. rst-class:: console

::

    ryu@ryu-vm:~$ ryu-manager ./simple_switch_lacp_13.py
    loading app ./simple_switch_lacp_13.py
    loading app ryu.controller.ofp_handler
    creating context lacplib
    instantiating app ./simple_switch_lacp_13.py
    instantiating app ryu.controller.ofp_handler
    ...

ホストh1は30秒に1回LACPデータユニットを送信し続けています。起動してからしば
らくすると、スイッチはホストh1からのLACPデータユニットを受信し、動作ログに
出力します。

Node: c0:

.. rst-class:: console

::

    ...
    [LACP][INFO] SW=0000000000000001 PORT=1 LACP received.
    [LACP][INFO] SW=0000000000000001 PORT=1 the slave i/f has just been up.
    [LACP][INFO] SW=0000000000000001 PORT=1 the timeout time has changed.
    [LACP][INFO] SW=0000000000000001 PORT=1 LACP sent.
    slave state changed port: 1 enabled: True
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP received.
    [LACP][INFO] SW=0000000000000001 PORT=2 the slave i/f has just been up.
    [LACP][INFO] SW=0000000000000001 PORT=2 the timeout time has changed.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP sent.
    slave state changed port: 2 enabled: True
    ...

各ログは以下のことを表しています。

* LACP received.

    LACPデータユニットを受信しました。

* the slave i/f has just been up.

    無効状態だったポートが有効状態に変更されました。

* the timeout time has changed.

    LACPデータユニットの無通信監視時間が変更されました(今回の場合、初期状態
    の0秒からLONG_TIMEOUT_TIMEの90秒に変更されています)。

* LACP sent.

    応答用のLACPデータユニットを送信しました。

* slave state changed ...

    LACPライブラリからの ``EventSlaveStateChanged`` イベントをアプリケー
    ションが受信しました(イベントの詳細については後述します)。

その後は定期的にホストh1から送られてくるたび、応答用LACPデータユニットを送
信します。

Node: c0:

.. rst-class:: console

::

    ...
    [LACP][INFO] SW=0000000000000001 PORT=1 LACP received.
    [LACP][INFO] SW=0000000000000001 PORT=1 LACP sent.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP received.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP sent.
    ...

この時点でのフローエントリを確認します。

Node: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=14.565s, table=0, n_packets=1, n_bytes=124, idle_timeout=90, send_flow_rem priority=65535,in_port=2,dl_src=00:00:00:00:00:12,dl_type=0x8809 actions=CONTROLLER:65509
     cookie=0x0, duration=14.562s, table=0, n_packets=1, n_bytes=124, idle_timeout=90, send_flow_rem priority=65535,in_port=1,dl_src=00:00:00:00:00:11,dl_type=0x8809 actions=CONTROLLER:65509
     cookie=0x0, duration=24.821s, table=0, n_packets=2, n_bytes=248, priority=0 actions=CONTROLLER:65535

スイッチには

* h1のh1-eth1(入力ポートがs1-eth2でMACアドレスが00:00:00:00:00:12)から
  LACPデータユニット(ethertypeが0x8809)が送られてきたらPacket-Inメッセージ
  を送信する
* h1のh1-eth0(入力ポートがs1-eth1でMACアドレスが00:00:00:00:00:11)から
  LACPデータユニット(ethertypeが0x8809)が送られてきたらPacket-Inメッセージ
  を送信する
* 「 :ref:`ch_switching_hub` 」でも登録しているTable-missフローエントリ

の3つのフローエントリが登録されていることがわかります。


リンク・アグリゲーション機能の確認
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

通信速度の向上
""""""""""""""

まずはリンク・アグリゲーションによる通信速度の向上を確認します。ただし、実際
に通信性能の確認を行おうとすると大量のデータを間断なく送受信し続ける必要があ
り、試験が煩雑になってしまいますので、ここでは「スイッチングハブの機能により
論理インターフェースを経由するフローエントリを複数登録し、その際特定の物理回
線にのみフローが集中しないこと」をもって動作の確認を行います。

まず、ホストh2からホストh1に対しpingを実行します。

Node: h2:

.. rst-class:: console

::

    root@ryu-vm:~# ping 10.0.0.1
    PING 10.0.0.1 (10.0.0.1) 56(84) bytes of data.
    64 bytes from 10.0.0.1: icmp_req=1 ttl=64 time=93.0 ms
    64 bytes from 10.0.0.1: icmp_req=2 ttl=64 time=0.266 ms
    64 bytes from 10.0.0.1: icmp_req=3 ttl=64 time=0.075 ms
    64 bytes from 10.0.0.1: icmp_req=4 ttl=64 time=0.065 ms
    ...

pingを送信し続けたまま、スイッチs1のフローエントリを確認します。

Node: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=22.05s, table=0, n_packets=1, n_bytes=124, idle_timeout=90, send_flow_rem priority=65535,in_port=2,dl_src=00:00:00:00:00:12,dl_type=0x8809 actions=CONTROLLER:65509
     cookie=0x0, duration=22.046s, table=0, n_packets=1, n_bytes=124, idle_timeout=90, send_flow_rem priority=65535,in_port=1,dl_src=00:00:00:00:00:11,dl_type=0x8809 actions=CONTROLLER:65509
     cookie=0x0, duration=33.046s, table=0, n_packets=6, n_bytes=472, priority=0 actions=CONTROLLER:65535
     cookie=0x0, duration=3.259s, table=0, n_packets=3, n_bytes=294, priority=1,in_port=3,dl_dst=02:01:02:03:04:08 actions=output:1
     cookie=0x0, duration=3.262s, table=0, n_packets=4, n_bytes=392, priority=1,in_port=1,dl_dst=00:00:00:00:00:22 actions=output:3

先ほど確認した時点から、4番めと5番めのフローエントリが追加されています。

.. rst-class:: sourcecode

::

     cookie=0x0, duration=3.259s, table=0, n_packets=3, n_bytes=294, priority=1,in_port=3,dl_dst=02:01:02:03:04:08 actions=output:1
     cookie=0x0, duration=3.262s, table=0, n_packets=4, n_bytes=392, priority=1,in_port=1,dl_dst=00:00:00:00:00:22 actions=output:3

それぞれ、

* 3番ポート(s1-eth3、つまりh2の対向インターフェース)からh1のbond0宛のパ
  ケットを受信したら1番ポート(s1-eth1)から出力する
* 1番ポート(s1-eth1)からh2宛のパケットを受信したら3番ポート(s1-eth3)から
  出力する

というフローエントリです。h2との通信にはs1-eth1が使用されていることがわかり
ます。

続いて、ホストh3からホストh1に対しpingを実行します。

Node: h3:

.. rst-class:: console

::

    root@ryu-vm:~# ping 10.0.0.1
    PING 10.0.0.1 (10.0.0.1) 56(84) bytes of data.
    64 bytes from 10.0.0.1: icmp_req=1 ttl=64 time=91.2 ms
    64 bytes from 10.0.0.1: icmp_req=2 ttl=64 time=0.256 ms
    64 bytes from 10.0.0.1: icmp_req=3 ttl=64 time=0.057 ms
    64 bytes from 10.0.0.1: icmp_req=4 ttl=64 time=0.073 ms
    ...

pingを送信し続けたまま、スイッチs1のフローエントリを確認します。

Node: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=99.765s, table=0, n_packets=4, n_bytes=496, idle_timeout=90, send_flow_rem priority=65535,in_port=2,dl_src=00:00:00:00:00:12,dl_type=0x8809 actions=CONTROLLER:65509
     cookie=0x0, duration=99.761s, table=0, n_packets=4, n_bytes=496, idle_timeout=90, send_flow_rem priority=65535,in_port=1,dl_src=00:00:00:00:00:11,dl_type=0x8809 actions=CONTROLLER:65509
     cookie=0x0, duration=110.761s, table=0, n_packets=10, n_bytes=696, priority=0 actions=CONTROLLER:65535
     cookie=0x0, duration=80.974s, table=0, n_packets=82, n_bytes=7924, priority=1,in_port=3,dl_dst=02:01:02:03:04:08 actions=output:1
     cookie=0x0, duration=2.677s, table=0, n_packets=2, n_bytes=196, priority=1,in_port=2,dl_dst=00:00:00:00:00:23 actions=output:4
     cookie=0x0, duration=2.675s, table=0, n_packets=1, n_bytes=98, priority=1,in_port=4,dl_dst=02:01:02:03:04:08 actions=output:2
     cookie=0x0, duration=80.977s, table=0, n_packets=83, n_bytes=8022, priority=1,in_port=1,dl_dst=00:00:00:00:00:22 actions=output:3

先ほど確認した時点から、5番めと6番めのフローエントリが追加されています。

.. rst-class:: sourcecode

::

     cookie=0x0, duration=2.675s, table=0, n_packets=1, n_bytes=98, priority=1,in_port=4,dl_dst=02:01:02:03:04:08 actions=output:2
     cookie=0x0, duration=2.677s, table=0, n_packets=2, n_bytes=196, priority=1,in_port=2,dl_dst=00:00:00:00:00:23 actions=output:4

それぞれ、

* 4番ポート(s1-eth4、つまりh3の対向インターフェース)からh1のbond0宛のパ
  ケットを受信したら2番ポート(s1-eth2)から出力する
* 2番ポート(s1-eth2)からh3宛のパケットを受信したら4番ポート(s1-eth4)から
  出力する

というフローエントリです。h3との通信にはs1-eth2が使用されていることがわかり
ます。

同様にホストh4からホストh1に対しpingを実行します。

Node: h4:

.. rst-class:: console

::

    root@ryu-vm:~# ping 10.0.0.1
    PING 10.0.0.1 (10.0.0.1) 56(84) bytes of data.
    64 bytes from 10.0.0.1: icmp_req=1 ttl=64 time=86.3 ms
    64 bytes from 10.0.0.1: icmp_req=2 ttl=64 time=0.397 ms
    64 bytes from 10.0.0.1: icmp_req=3 ttl=64 time=0.136 ms
    64 bytes from 10.0.0.1: icmp_req=4 ttl=64 time=0.035 ms
    ...

pingを送信し続けたまま、スイッチs1のフローエントリを確認します。

Node: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=199.287s, table=0, n_packets=7, n_bytes=868, idle_timeout=90, send_flow_rem priority=65535,in_port=2,dl_src=00:00:00:00:00:12,dl_type=0x8809 actions=CONTROLLER:65509
     cookie=0x0, duration=199.283s, table=0, n_packets=7, n_bytes=868, idle_timeout=90, send_flow_rem priority=65535,in_port=1,dl_src=00:00:00:00:00:11,dl_type=0x8809 actions=CONTROLLER:65509
     cookie=0x0, duration=210.283s, table=0, n_packets=14, n_bytes=920, priority=0 actions=CONTROLLER:65535
     cookie=0x0, duration=2.807s, table=0, n_packets=3, n_bytes=294, priority=1,in_port=1,dl_dst=00:00:00:00:00:24 actions=output:5
     cookie=0x0, duration=180.496s, table=0, n_packets=185, n_bytes=17850, priority=1,in_port=3,dl_dst=02:01:02:03:04:08 actions=output:1
     cookie=0x0, duration=2.804s, table=0, n_packets=2, n_bytes=196, priority=1,in_port=5,dl_dst=02:01:02:03:04:08 actions=output:1
     cookie=0x0, duration=102.199s, table=0, n_packets=105, n_bytes=10122, priority=1,in_port=2,dl_dst=00:00:00:00:00:23 actions=output:4
     cookie=0x0, duration=102.197s, table=0, n_packets=104, n_bytes=10024, priority=1,in_port=4,dl_dst=02:01:02:03:04:08 actions=output:2
     cookie=0x0, duration=180.499s, table=0, n_packets=186, n_bytes=17948, priority=1,in_port=1,dl_dst=00:00:00:00:00:22 actions=output:3

追加されたフローエントリは以下のふたつです。

.. rst-class:: sourcecode

::

     cookie=0x0, duration=2.804s, table=0, n_packets=2, n_bytes=196, priority=1,in_port=5,dl_dst=02:01:02:03:04:08 actions=output:1
     cookie=0x0, duration=2.807s, table=0, n_packets=3, n_bytes=294, priority=1,in_port=1,dl_dst=00:00:00:00:00:24 actions=output:5

それぞれ、

* 5番ポート(s1-eth5、つまりh4の対向インターフェース)からh1のbond0宛のパ
  ケットを受信したら1番ポート(s1-eth1)から出力する
* 1番ポート(s1-eth1)からh4宛のパケットを受信したら5番ポート(s1-eth5)から
  出力する

というフローエントリです。h4との通信にはs1-eth1が使用されていることがわかり
ます。

============ ============
宛先ホスト   使用ポート
============ ============
h2           1
h3           2
h4           1
============ ============

    .. only:: latex

       .. image:: images/link_aggregation/fig3.eps
          :scale: 80 %
          :align: center

    .. only:: epub

       .. image:: images/link_aggregation/fig3.png
          :align: center

    .. only:: not latex and not epub

       .. image:: images/link_aggregation/fig3.png
          :scale: 80 %
          :align: center

以上のように、フローが分散することが確認できました。


耐障害性の向上
""""""""""""""

次に、リンク・アグリゲーションによる耐障害性の向上を確認します。現在の状況は、
h2とh4がh1と通信する際にはs1-eth2を、h3がh1と通信する際にはs1-eth1を使用し
ています。

ここで、s1-eth1の対向インターフェースであるh1-eth0をリンク・アグリゲーション
のグループから離脱させます。

Node: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ip link set h1-eth0 nomaster

h1-eth0が停止したことにより、ホストh3からホストh1へのpingが疎通不可能になり
ます。そのまま無通信監視時間の上限である90秒が経過すると、コントローラの動作
ログに次のようなメッセージが出力されます。

Node: c0:

.. rst-class:: console

::

    ...
    [LACP][INFO] SW=0000000000000001 PORT=1 LACP received.
    [LACP][INFO] SW=0000000000000001 PORT=1 LACP sent.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP received.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP sent.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP received.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP sent.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP received.
    [LACP][INFO] SW=0000000000000001 PORT=2 LACP sent.
    [LACP][INFO] SW=0000000000000001 PORT=1 LACP exchange timeout has occurred.
    slave state changed port: 1 enabled: False
    ...

「LACP exchange timeout has occurred.」は無通信監視時間の上限に達し、LACP
データユニットをPacket-Inするフローエントリが削除されたことを表します。
``EventSlaveStateChanged`` イベントを受信したスイッチングハブは、学習した
MACアドレスをすべて忘却し、転送用のフローエントリをすべて削除します。

すべての学習結果を忘れた状態でも、ホストh2～h4ではまだpingが実行されているた
め、通常のスイッチングハブの動作によって再度MACアドレスを学習し、転送用のフ
ローエントリを登録します。このとき、停止しているh1-eth0ではパケットの送受信
が行われないため、ホストh2～h4とホストh1との間の通信はすべてh1-eth1が使用
されます。

Node: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=364.265s, table=0, n_packets=13, n_bytes=1612, idle_timeout=90, send_flow_rem priority=65535,in_port=2,dl_src=00:00:00:00:00:12,dl_type=0x8809 actions=CONTROLLER:65509
     cookie=0x0, duration=374.521s, table=0, n_packets=25, n_bytes=1830, priority=0 actions=CONTROLLER:65535
     cookie=0x0, duration=5.738s, table=0, n_packets=5, n_bytes=490, priority=1,in_port=3,dl_dst=02:01:02:03:04:08 actions=output:2
     cookie=0x0, duration=6.279s, table=0, n_packets=5, n_bytes=490, priority=1,in_port=2,dl_dst=00:00:00:00:00:23 actions=output:5
     cookie=0x0, duration=6.281s, table=0, n_packets=5, n_bytes=490, priority=1,in_port=5,dl_dst=02:01:02:03:04:08 actions=output:2
     cookie=0x0, duration=5.506s, table=0, n_packets=5, n_bytes=434, priority=1,in_port=4,dl_dst=02:01:02:03:04:08 actions=output:2
     cookie=0x0, duration=5.736s, table=0, n_packets=5, n_bytes=490, priority=1,in_port=2,dl_dst=00:00:00:00:00:21 actions=output:3
     cookie=0x0, duration=6.504s, table=0, n_packets=6, n_bytes=532, priority=1,in_port=2,dl_dst=00:00:00:00:00:22 actions=output:4

フローエントリが再登録されたことにより、ホストh3で停止していたpingが再開され
ます。

Node: h3:

.. rst-class:: console

::


    ...
    64 bytes from 10.0.0.1: icmp_req=144 ttl=64 time=0.193 ms
    64 bytes from 10.0.0.1: icmp_req=145 ttl=64 time=0.081 ms
    64 bytes from 10.0.0.1: icmp_req=146 ttl=64 time=0.095 ms
    64 bytes from 10.0.0.1: icmp_req=237 ttl=64 time=44.1 ms
    64 bytes from 10.0.0.1: icmp_req=238 ttl=64 time=2.52 ms
    64 bytes from 10.0.0.1: icmp_req=239 ttl=64 time=0.371 ms
    64 bytes from 10.0.0.1: icmp_req=240 ttl=64 time=0.103 ms
    64 bytes from 10.0.0.1: icmp_req=241 ttl=64 time=0.067 ms
    ...

以上のように、一部の物理インターフェースに故障が発生した場合でも、他の物理
インターフェースを用いて自動的に復旧できることが確認できました。


Ryuによるリンク・アグリゲーション機能の実装
-------------------------------------------

Ryuのリンク・アグリゲーション・アプリケーションにおいて、OpenFlowを用いてど
のようにリンク・アグリゲーション機能を実現しているかを見ていきます。

冒頭でも述べたとおり、LACPを用いたリンク・アグリゲーションでは「LACPデータユ
ニットの交換が正常に行われている間は当該物理インターフェースは有効」「LACP
データユニットの交換が途絶えたら当該物理インターフェースは無効」という振る舞
いをします。物理インターフェースが無効ということは、そのインターフェースを使
用するフローエントリが存在しないということでもあります。従って、

* LACPデータユニットを受信したら応答を作成して送信する
* LACPデータユニットが一定時間受信できなかったら当該物理インターフェースを
  使用するフローエントリを削除し、以降そのインターフェースを使用するフロー
  エントリを登録しない
* 無効とされた物理インターフェースでLACPデータユニットを受信した場合、当該
  インターフェースを再度有効化する
* LACPデータユニット以外のパケットは「 :ref:`ch_switching_hub` 」のスイッ
  チングハブ機能で学習・転送する

という処理を実装すれば、リンク・アグリゲーションの基本的な動作が可能となりま
す。LACPに関わる部分とそうでない部分が明確に分かれているので、LACPに関わる
部分をLACPライブラリとして切り出し、そうでない部分は
「 :ref:`ch_switching_hub` 」のスイッチングハブを拡張するかたちで実装しま
す。

LACPデータユニット受信時の応答作成・送信はフローエントリだけでは実現不可能
であるため、Packet-Inメッセージを使用してOpenFlowコントローラ側で処理を行い
ます。

.. NOTE::

    LACPデータユニットを交換する物理インターフェースは、その役割によって
    ACTIVEとPASSIVEに分類されます。ACTIVEは一定時間ごとにLACPデータユニット
    を送信し、疎通を能動的に確認します。PASSIVEはACTIVEから送信されたLACP
    データユニットを受信した際に応答を返すことにより、疎通を受動的に確認しま
    す。

    Ryuのリンク・アグリゲーション・アプリケーションは、PASSIVEモードのみ実
    装しています。

    ACTIVEの実装には定期送信のためのタイマー処理が必要となります。リンク・ア
    グリゲーションとは本来無関係な処理が増えてしまうのを避けるため、ACTIVE
    モードを非対応としています。

一定時間LACPデータユニットを受信しなかった場合に当該物理インターフェースを
無効にする、という処理は、LACPデータユニットをPacket-Inさせるフローエントリ
にidle_timeoutを設定し、時間切れの際にFlowRemovedメッセージを送信させること
により、OpenFlowコントローラで当該インターフェースが無効になった際の対処を
行うことができます。

無効となったインターフェースでLACPデータユニットの交換が再開された場合の処理
は、LACPデータユニット受信時のPacket-Inメッセージ処理中で当該インター
フェースの有効/無効状態を判別・変更することで実現します。

物理インターフェースが無効となったとき、OpenFlowコントローラの処理としては
「当該インターフェースを使用するフローエントリを削除する」だけでよさそうに思
えますが、それでは不充分です。

たとえば3つの物理インターフェースをグループ化して使用している論理インター
フェースがあり、振り分けロジックが「有効なインターフェース数によるMACアドレ
スの剰余」となっている場合を仮定します。

====================  ====================  =================
インターフェース1     インターフェース2     インターフェース3
====================  ====================  =================
MACアドレスの剰余:0   MACアドレスの剰余:1   MACアドレスの剰余:2
====================  ====================  =================

そして、各物理インターフェースを使用するフローエントリが以下のように3つずつ
登録されていたとします。

=======================  =======================  ====================
インターフェース1        インターフェース2        インターフェース3
=======================  =======================  ====================
宛先:00:00:00:00:00:00   宛先:00:00:00:00:00:01   宛先:00:00:00:00:00:02
宛先:00:00:00:00:00:03   宛先:00:00:00:00:00:04   宛先:00:00:00:00:00:05
宛先:00:00:00:00:00:06   宛先:00:00:00:00:00:07   宛先:00:00:00:00:00:08
=======================  =======================  ====================

ここでインターフェース1が無効になった場合、「有効なインターフェース数による
MACアドレスの剰余」という振り分けロジックに従うと、次のように振り分けられな
ければなりません。

====================  ====================  =================
インターフェース1     インターフェース2     インターフェース3
====================  ====================  =================
無効                  MACアドレスの剰余:0   MACアドレスの剰余:1
====================  ====================  =================

=======================  =======================  ====================
インターフェース1        インターフェース2        インターフェース3
=======================  =======================  ====================
\                        宛先:00:00:00:00:00:00   宛先:00:00:00:00:00:01
\                        宛先:00:00:00:00:00:02   宛先:00:00:00:00:00:03
\                        宛先:00:00:00:00:00:04   宛先:00:00:00:00:00:05
\                        宛先:00:00:00:00:00:06   宛先:00:00:00:00:00:07
\                        宛先:00:00:00:00:00:08
=======================  =======================  ====================

インターフェース1を使用していたフローエントリだけではなく、インターフェース2や
インターフェース3のフローエントリも書き換える必要があることがわかります。これ
は物理インターフェースが無効になったときだけでなく、有効になったときも同様で
す。

従って、ある物理インターフェースの有効/無効状態が変更された場合の処理は、当該
物理インターフェースが所属する論理インターフェースに含まれるすべての物理イン
ターフェースを使用するフローエントリを削除する、ということになります。

.. NOTE::

    振り分けロジックについては仕様で定められておらず、各機器の実装に委ねられ
    ています。Ryuのリンク・アグリゲーション・アプリケーションでは独自の振り
    分け処理を行わず、対向装置によって振り分けられた経路を使用するものとしま
    す。

LACPデータユニット以外のフローエントリは「 :ref:`ch_switching_hub` 」のス
イッチングハブ機能で登録しているため、それらのフローエントリを削除するのも
スイッチングハブで行うべきです。

以上のことを整理すると、リンク・アグリゲーション機能として実装すべき項目は

**LACPライブラリ**

* LACPデータユニットを受信したら応答を作成して送信する
* FlowRemovedメッセージ受信時、当該物理インターフェースを無効とみなし、所属
  する論理インターフェースのフローエントリをスイッチングハブに削除させる
* 無効状態の物理インターフェースでLACPデータユニットを受信した場合、当該物理
  インターフェースを有効とみなし、所属する論理インターフェースのフローエント
  リをスイッチングハブに削除させる

**スイッチングハブ**

* LACPデータユニット以外を受信したら従来どおり学習・転送する
* LACPライブラリの指示により、登録済みのフローエントリを削除する

となります。

LACPライブラリおよびスイッチングハブのソースコードは、Ryuのソースツリーにあ
ります。

    ryu/lib/lacliblib.py

    ryu/app/simple_switch_lacp.py

.. NOTE::

    前述のとおり、simple_switch_lacp.pyはOpenFlow 1.0専用のアプリケーション
    であるため、本章では「 `Ryuアプリケーションの実行`_ 」に示した
    OpenFlow 1.3に対応したsimple_switch_lacp_13.pyを元にアプリケーションの
    詳細を説明します。

.. ATTENTION::

    Ryu3.2に含まれているlacplib.pyには不具合があります。Ryu3.3以降をご利用
    ください。


LACPライブラリの実装
^^^^^^^^^^^^^^^^^^^^

以降の節で、前述の機能がLACPライブラリにおいて具体的にどのように実装されてい
るかを見ていきます。なお、引用されているソースは抜粋です。全体像については実
際のソースをご参照ください。


論理インターフェースの作成
""""""""""""""""""""""""""

前述のとおり、リンク・アグリゲーション機能を使用するには、どのネットワーク
機器においてどのインターフェースをどのグループとして束ねるのかという設定を事
前に行っておく必要があります。LACPライブラリでは、以下のメソッドでこの設定を
行います。

.. rst-class:: sourcecode

::

    def add(self, dpid, ports):
        # ...
        assert isinstance(ports, list)
        assert 2 <= len(ports)
        ifs = {}
        for port in ports:
            ifs[port] = {'enabled': False, 'timeout': 0}
        bond = {}
        bond[dpid] = ifs
        self._bonds.append(bond)

引数の内容は以下のとおりです。

dpid

    OpenFlowスイッチのデータパスIDを指定します。

ports

    グループ化したいポート番号のリストを指定します。

このメソッドを呼び出すことにより、LACPライブラリは指定されたデータパスIDの
OpenFlowスイッチの指定されたポートをひとつのインターフェースとして扱うよう
になります。複数のグループを作成したい場合、その都度add()メソッドを呼び出し
ます。なお、論理インターフェースに割り当てられるMACアドレスは、OpenFlow
スイッチの持つLOCALポートと同じものが自動的に使用されます。

.. TIP::

    OpenFlowスイッチの中には、スイッチ自身の機能としてリンク・アグリゲー
    ション機能を提供しているものもあります（Open vSwitchなど）。ここではそ
    うしたスイッチ独自の機能は使用せず、OpenFlowコントローラによる制御に
    よってリンク・アグリゲーション機能を実現します。


Packet-In処理
"""""""""""""

「 :ref:`ch_switching_hub` 」のスイッチングハブは、宛先のMACアドレスが未学
習の場合、受信したパケットをフラッディングします。LACPデータユニットは隣接す
るネットワーク機器間でのみ交換されるべきもので、他の機器に転送してしまうとリ
ンク・アグリゲーション機能が正しく動作しません。そこで、「Packet-Inで受信し
たパケットがLACPデータユニットであれば専用の動作を行い、LACPデータユニット
以外のパケットであればスイッチングハブの動作に委ねる」という処理分岐を行い、
スイッチングハブにLACPデータユニットを処理させないようにします。

.. rst-class:: sourcecode

::

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, evt):
        """PacketIn event handler. when the received packet was LACP,
        proceed it. otherwise, send a event."""
        req_pkt = packet.Packet(evt.msg.data)
        if slow.lacp in req_pkt:
            (req_lacp, ) = req_pkt.get_protocols(slow.lacp)
            (req_eth, ) = req_pkt.get_protocols(ethernet.ethernet)
            self._do_lacp(req_lacp, req_eth.src, evt.msg)
        else:
            self.send_event_to_observers(EventPacketIn(evt.msg))

イベントハンドラ自体は「 :ref:`ch_switching_hub` 」と同様です。受信したメッ
セージにLACPデータユニットが含まれているかどうかで処理を分岐させています。

LACPデータユニットが含まれていた場合はLACPライブラリのLACPデータユニット受
信処理を行います。LACPデータユニットが含まれていなかった場合、
send_event_to_observers()というメソッドを呼んでいます。これは
ryu.base.app_manager.RyuAppクラスで定義されている、イベントを送信するため
のメソッドです。

「 :ref:`ch_switching_hub` 」ではRyuで定義されたOpenFlowメッセージ受信イ
ベントについて触れましたが、ユーザが独自にイベントを定義することもできます。
上記ソースで送信している ``EventPacketIn`` というイベントは、LACPライブラ
リ内で作成したユーザ定義イベントです。

.. rst-class:: sourcecode

::

    class EventPacketIn(event.EventBase):
        """a PacketIn event class using except LACP."""
        def __init__(self, msg):
            """initialization."""
            super(EventPacketIn, self).__init__()
            self.msg = msg

ユーザ定義イベントは、ryu.controller.event.EventBaseクラスを継承して作成
します。イベントクラスに内包するデータに制限はありません。 ``EventPacketIn``
クラスでは、Packet-Inメッセージで受信したryu.ofproto.OFPPacketInインスタン
スをそのまま使用しています。

ユーザ定義イベントの受信方法については後述します。


ポートの有効/無効状態変更に伴う処理
"""""""""""""""""""""""""""""""""""

LACPライブラリのLACPデータユニット受信処理は、以下の処理からなっています。

1. LACPデータユニットを受信したポートが利用不能状態であれば利用可能状態に変更
   し、状態が変更したことをイベントで通知します。
2. 無通信タイムアウトの待機時間が変更された場合、LACPデータユニット受信時に
   Packet-Inを送信するフローエントリを登録します。
3. 受信したLACPデータユニットに対する応答を作成し、送信します。

2.の処理については後述の
「 `LACPデータユニットをPacket-Inさせるフローエントリの登録`_ 」
で、3.の処理については後述の
「 `LACPデータユニットの送受信処理`_ 」
で、それぞれ説明します。ここでは1.の処理について説明します。

.. rst-class:: sourcecode

::

    def _do_lacp(self, req_lacp, src, msg):
        # ...

        # when LACP arrived at disabled port, update the status of
        # the slave i/f to enabled, and send a event.
        if not self._get_slave_enabled(dpid, port):
            self.logger.info(
                "SW=%s PORT=%d the slave i/f has just been up.",
                dpid_to_str(dpid), port)
            self._set_slave_enabled(dpid, port, True)
            self.send_event_to_observers(
                EventSlaveStateChanged(datapath, port, True))

_get_slave_enabled()メソッドは、指定したスイッチの指定したポートが有効か否
かを取得します。_set_slave_enabled()メソッドは、指定したスイッチの指定した
ポートの有効/無効状態を設定します。

上記のソースでは、無効状態のポートでLACPデータユニットを受信した場合、ポート
の状態が変更されたということを示す ``EventSlaveStateChanged`` というユーザ
定義イベントを送信しています。

.. rst-class:: sourcecode

::

    class EventSlaveStateChanged(event.EventBase):
        """a event class that notifies the changes of the statuses of the
        slave i/fs."""
        def __init__(self, datapath, port, enabled):
            """initialization."""
            super(EventSlaveStateChanged, self).__init__()
            self.datapath = datapath
            self.port = port
            self.enabled = enabled

``EventSlaveStateChanged`` イベントは、ポートが有効化したときの他に、ポート
が無効化したときにも送信されます。無効化したときの処理は
「 `FlowRemovedメッセージの受信処理`_ 」で実装されています。

``EventSlaveStateChanged`` クラスには以下の情報が含まれます。

* ポートの有効/無効状態変更が発生したOpenFlowスイッチ
* 有効/無効状態変更が発生したポート番号
* 変更後の状態


LACPデータユニットをPacket-Inさせるフローエントリの登録
"""""""""""""""""""""""""""""""""""""""""""""""""""""""

LACPデータユニットの交換間隔には、FAST（1秒ごと）とSLOW（30秒ごと）の2種類
があります。リンク・アグリゲーションの仕様によれば、交換間隔の3倍の時間無通
信状態が続いた場合、そのインターフェースはリンク・アグリゲーションのグループ
から除外され、パケットの転送には使用されなくなります。

LACPライブラリでは、LACPデータユニット受信時にPacket-Inさせるフローエントリ
に対し、交換間隔の3倍の時間（SHORT_TIMEOUT_TIMEは3秒、LONG_TIMEOUT_TIMEは
90秒）をidle_timeoutとして設定することにより、無通信の監視を行っています。

交換間隔が変更された場合、idle_timeoutの時間も再設定する必要があるため、
LACPライブラリでは以下のような実装をしています。

.. rst-class:: sourcecode

::

    def _do_lacp(self, req_lacp, src, msg):
        # ...

        # set the idle_timeout time using the actor state of the
        # received packet.
        if req_lacp.LACP_STATE_SHORT_TIMEOUT == \
           req_lacp.actor_state_timeout:
            idle_timeout = req_lacp.SHORT_TIMEOUT_TIME
        else:
            idle_timeout = req_lacp.LONG_TIMEOUT_TIME

        # when the timeout time has changed, update the timeout time of
        # the slave i/f and re-enter a flow entry for the packet from
        # the slave i/f with idle_timeout.
        if idle_timeout != self._get_slave_timeout(dpid, port):
            self.logger.info(
                "SW=%s PORT=%d the timeout time has changed.",
                dpid_to_str(dpid), port)
            self._set_slave_timeout(dpid, port, idle_timeout)
            func = self._add_flow.get(ofproto.OFP_VERSION)
            assert func
            func(src, port, idle_timeout, datapath)

        # ...

_get_slave_timeout()メソッドは、指定したスイッチの指定したポートにおける現
在のidle_timeout値を取得します。_set_slave_timeout()メソッドは、指定したス
イッチの指定したポートにおけるidle_timeout値を登録します。初期状態および
リンク・アグリゲーション・グループから除外された場合にはidle_timeout値は0に
設定されているため、新たにLACPデータユニットを受信した場合、交換間隔がどちら
であってもフローエントリを登録します。

使用するOpenFlowのバージョンにより ``OFPFlowMod`` クラスのコンストラクタの
引数が異なるため、バージョンに応じたフローエントリ登録メソッドを取得していま
す。以下はOpenFlow 1.2以降で使用するフローエントリ登録メソッドです。

.. rst-class:: sourcecode

::

    def _add_flow_v1_2(self, src, port, timeout, datapath):
        """enter a flow entry for the packet from the slave i/f
        with idle_timeout. for OpenFlow ver1.2 and ver1.3."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(
            in_port=port, eth_src=src, eth_type=ether.ETH_TYPE_SLOW)
        actions = [parser.OFPActionOutput(
            ofproto.OFPP_CONTROLLER, ofproto.OFPCML_MAX)]
        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, command=ofproto.OFPFC_ADD,
            idle_timeout=timeout, priority=65535,
            flags=ofproto.OFPFF_SEND_FLOW_REM, match=match,
            instructions=inst)
        datapath.send_msg(mod)

上記ソースで、「対向インターフェースからLACPデータユニットを受信した場合は
Packet-Inする」というフローエントリを、無通信監視時間つき最高優先度で設定
しています。


LACPデータユニットの送受信処理
""""""""""""""""""""""""""""""

LACPデータユニット受信時、「 `ポートの有効/無効状態変更に伴う処理`_ 」や
「 `LACPデータユニットをPacket-Inさせるフローエントリの登録`_ 」を行った
後、応答用のLACPデータユニットを作成し、送信します。

.. rst-class:: sourcecode

::

    def _do_lacp(self, req_lacp, src, msg):
        # ...

        # create a response packet.
        res_pkt = self._create_response(datapath, port, req_lacp)

        # packet-out the response packet.
        out_port = ofproto.OFPP_IN_PORT
        actions = [parser.OFPActionOutput(out_port)]
        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
            data=res_pkt.data, in_port=port, actions=actions)
        datapath.send_msg(out)

上記ソースで呼び出されている_create_response()メソッドは応答用パケット作成
処理です。その中で呼び出されている_create_lacp()メソッドで応答用のLACPデー
タユニットを作成しています。作成した応答用パケットは、LACPデータユニットを
受信したポートからPacket-Outさせます。

LACPデータユニットには送信側（Actor）の情報と受信側（Partner）の情報を設定
します。受信したLACPデータユニットの送信側情報には対向インターフェースの情報
が記載されているので、OpenFlowスイッチから応答を返すときにはそれを受信側情報
として設定します。

.. rst-class:: sourcecode

::

    def _create_lacp(self, datapath, port, req):
        """create a LACP packet."""
        actor_system = datapath.ports[datapath.ofproto.OFPP_LOCAL].hw_addr
        res = slow.lacp(
            # ...
            partner_system_priority=req.actor_system_priority,
            partner_system=req.actor_system,
            partner_key=req.actor_key,
            partner_port_priority=req.actor_port_priority,
            partner_port=req.actor_port,
            partner_state_activity=req.actor_state_activity,
            partner_state_timeout=req.actor_state_timeout,
            partner_state_aggregation=req.actor_state_aggregation,
            partner_state_synchronization=req.actor_state_synchronization,
            partner_state_collecting=req.actor_state_collecting,
            partner_state_distributing=req.actor_state_distributing,
            partner_state_defaulted=req.actor_state_defaulted,
            partner_state_expired=req.actor_state_expired,
            collector_max_delay=0)
        self.logger.info("SW=%s PORT=%d LACP sent.",
                         dpid_to_str(datapath.id), port)
        self.logger.debug(str(res))
        return res


FlowRemovedメッセージの受信処理
"""""""""""""""""""""""""""""""

指定された時間の間LACPデータユニットの交換が行われなかった場合、OpenFlowス
イッチはFlowRemovedメッセージをOpenFlowコントローラに送信します。

.. rst-class:: sourcecode

::

    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def flow_removed_handler(self, evt):
        """FlowRemoved event handler. when the removed flow entry was
        for LACP, set the status of the slave i/f to disabled, and
        send a event."""
        msg = evt.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        dpid = datapath.id
        match = msg.match
        if ofproto.OFP_VERSION == ofproto_v1_0.OFP_VERSION:
            port = match.in_port
            dl_type = match.dl_type
        else:
            port = match['in_port']
            dl_type = match['eth_type']
        if ether.ETH_TYPE_SLOW != dl_type:
            return
        self.logger.info(
            "SW=%s PORT=%d LACP exchange timeout has occurred.",
            dpid_to_str(dpid), port)
        self._set_slave_enabled(dpid, port, False)
        self._set_slave_timeout(dpid, port, 0)
        self.send_event_to_observers(
            EventSlaveStateChanged(datapath, port, False))

FlowRemovedメッセージを受信すると、OpenFlowコントローラは
_set_slave_enabled()メソッドを使用してポートの無効状態を設定し、
_set_slave_timeout()メソッドを使用してidle_timeout値を0に設定し、
send_event_to_observers()メソッドを使用して ``EventSlaveStateChanged``
イベントを送信します。


アプリケーションの実装
^^^^^^^^^^^^^^^^^^^^^^

「 `Ryuアプリケーションの実行`_ 」に示したOpenFlow 1.3対応のリンク・アグリ
ゲーション・アプリケーション (simple_switch_lacp_13.py) と、
「 :ref:`ch_switching_hub` 」のスイッチングハブとの差異を順に説明していき
ます。


「_CONTEXTS」の設定
"""""""""""""""""""

ryu.base.app_manager.RyuAppを継承したRyuアプリケーションは、「_CONTEXTS」
ディクショナリに他のRyuアプリケーションを設定することにより、他のアプリケー
ションを別スレッドで起動させることができます。ここではLACPライブラリの
LacpLibクラスを「lacplib」という名前で「_CONTEXTS」に設定しています。

.. rst-class:: sourcecode

::

    from ryu.lib import lacplib

    # ...

    class SimpleSwitchLacp13(app_manager.RyuApp):
        OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
        _CONTEXTS = {'lacplib': lacplib.LacpLib}

        # ...


「_CONTEXTS」に設定したアプリケーションは、__init__()メソッドのkwargsから
インスタンスを取得することができます。


.. rst-class:: sourcecode

::

        # ...
        def __init__(self, *args, **kwargs):
            super(SimpleSwitchLacp13, self).__init__(*args, **kwargs)
            self.mac_to_port = {}
            self._lacp = kwargs['lacplib']
        # ...


ライブラリの初期設定
""""""""""""""""""""

「_CONTEXTS」に設定したLACPライブラリの初期設定を行います。初期設定には
LACPライブラリの提供するadd()メソッドを実行します。ここでは以下の値を設定し
ます。

============ ================================= ==============================
パラメータ   値                                説明
============ ================================= ==============================
dpid         str_to_dpid('0000000000000001')   データパスID
ports        [1, 2]                            グループ化するポートのリスト
============ ================================= ==============================

この設定により、データパスID「0000000000000001」のOpenFlowスイッチのポート1と
ポート2がひとつのリンク・アグリゲーション・グループとして動作します。


.. rst-class:: sourcecode

::

        # ...
            self._lacp = kwargs['lacplib']
            self._lacp.add(
                dpid=str_to_dpid('0000000000000001'), ports=[1, 2])
        # ...


ユーザ定義イベントの受信方法
""""""""""""""""""""""""""""

`LACPライブラリの実装`_ で説明したとおり、LACPライブラリはLACPデータユニッ
トの含まれないPacket-Inメッセージを ``EventPacketIn`` というユーザ定義イ
ベントとして送信します。ユーザ定義イベントのイベントハンドラも、Ryuが提供す
るイベントハンドラと同じように ``ryu.controller.handler.set_ev_cls`` デコ
レータで装飾します。

.. rst-class:: sourcecode

::

    @set_ev_cls(lacplib.EventPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        # ...

また、LACPライブラリはポートの有効/無効状態が変更されると
``EventSlaveStateChanged`` イベントを送信しますので、こちらもイベントハンド
ラを作成しておきます。

.. rst-class:: sourcecode

::

    @set_ev_cls(lacplib.EventSlaveStateChanged, lacplib.LAG_EV_DISPATCHER)
    def _slave_state_changed_handler(self, ev):
        datapath = ev.datapath
        dpid = datapath.id
        port_no = ev.port
        enabled = ev.enabled
        self.logger.info("slave state changed port: %d enabled: %s",
                         port_no, enabled)
        if dpid in self.mac_to_port:
            for mac in self.mac_to_port[dpid]:
                match = datapath.ofproto_parser.OFPMatch(eth_dst=mac)
                self.del_flow(datapath, match)
            del self.mac_to_port[dpid]
        self.mac_to_port.setdefault(dpid, {})

本節の冒頭で整理したとおり、ポートの有効/無効状態が変更され、パケットの転送
に使用可能な物理インターフェースの個数が増減すると、論理インターフェースを通
過するパケットが実際に使用する物理インターフェースが変更になる可能性がありま
す。パケットの経路が変更される場合、すでに登録されているフローエントリを削除
し、新たにフローエントリを登録する必要があります。この例では処理を簡略化する
ため、「ポートの有効/無効状態が変更された場合、当該OpenFlowスイッチの全学習
結果を削除する」という実装となっています。

.. rst-class:: sourcecode

::

    def del_flow(self, datapath, match):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        mod = parser.OFPFlowMod(datapath=datapath,
                                command=ofproto.OFPFC_DELETE,
                                match=match)
        datapath.send_msg(mod)

フローエントリの削除は ``OFPFlowMod`` クラスのインスタンスで行います。

以上のように、リンク・アグリゲーション機能を提供するライブラリと、ライブラリ
を利用するアプリケーションによって、リンク・アグリゲーション機能を持つスイッ
チングハブのアプリケーションを実現しています。


まとめ
------

本章では、リンク・アグリゲーションライブラリの利用を題材として、以下の項目に
ついて説明しました。

* 「_CONTEXTS」を用いたライブラリの使用方法
* ユーザ定義イベントの定義方法とイベントトリガーの発生方法
