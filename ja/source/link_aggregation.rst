.. _ch_link_aggregation:

リンク・アグリゲーション
========================

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
     :scale: 80%
     :align: center

.. only:: epub

  .. image:: images/link_aggregation/fig1.png
     :align: center

.. only:: not latex and not epub

  .. image:: images/link_aggregation/fig1.png
     :scale: 40%
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

.. literalinclude:: ../../ryu/app/simple_switch_lacp_13.py
    :lines: 16-


実験環境の構築
^^^^^^^^^^^^^^

OpenFlowスイッチとLinuxホストの間でリンク・アグリゲーションを構成してみましょう。

VMイメージ利用のための環境設定やログイン方法等は「 :ref:`ch_switching_hub` 」
を参照してください。

最初にMininetを利用して下図の様なトポロジを作成します。

.. only:: latex

   .. image:: images/link_aggregation/fig2.eps
      :scale: 80%
      :align: center

.. only:: epub

   .. image:: images/link_aggregation/fig2.png
      :align: center

.. only:: not latex and not epub

   .. image:: images/link_aggregation/fig2.png
      :scale: 40%
      :align: center

MininetのAPIを呼び出すスクリプトを作成し、必要なトポロジを構築
します。

ソース名： ``link_aggregation.py``

.. rst-class:: sourcecode

.. literalinclude:: ../../sources/link_aggregation.py

このスクリプトを実行することにより、ホストh1とスイッチs1の間に2本のリンクが
存在するトポロジが作成されます。netコマンドで作成されたトポロジを確認す
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


ホストh1でのリンク・アグリゲーションの設定
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ホストh1のLinuxに必要な事前設定を行いましょう。
本節
でのコマンド入力は、ホストh1のxterm上で行ってください。

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

論理インターフェースにIPアドレスを割り当てます。
ここでは10.0.0.1を割り当てることにします。また、h1-eth0にIPアドレス
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

以上でホストh1への事前設定は終了です。


OpenFlowバージョンの設定
^^^^^^^^^^^^^^^^^^^^^^^^

スイッチs1のOpenFlowの
バージョンを1.3に設定します。このコマンド入力は、スイッチs1のxterm上で行っ
てください。

Node: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13


スイッチングハブの実行
^^^^^^^^^^^^^^^^^^^^^^

準備が整ったので、冒頭で作成したRyuアプリケーションを実行します。

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

ホストh1は30秒に1回LACPデータユニットを送信しています。起動してからしば
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

ログは以下のことを表しています。

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

スイッチは、ホストh1からLACPデータユニットを受信の都度、応答用LACPデータユニットを送
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

フローエントリを確認してみましょう。

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
* 「 :ref:`ch_switching_hub` 」と同様のTable-missフローエントリ

の3つのフローエントリが登録されています。


リンク・アグリゲーション機能の確認
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

通信速度の向上
""""""""""""""

まずはリンク・アグリゲーションによる通信速度の向上を確認します。
通信に応じて複数のリンクを使い分ける様子を見てみましょう。

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

先ほど確認した時点から、2つのフローエントリが追加されています。
durationの値が小さい4番目と5番目のエントリです。

それぞれ、

* 3番ポート(s1-eth3、つまりh2の対向インターフェース)からh1のbond0宛のパ
  ケットを受信したら1番ポート(s1-eth1)から出力する
* 1番ポート(s1-eth1)からh2宛のパケットを受信したら3番ポート(s1-eth3)から
  出力する

というフローエントリです。h2とh1の間の通信にはs1-eth1が使用されていることがわかり
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

先ほど確認した時点から、2つのフローエントリが追加されています。
durationの値が小さい5番目と6番目のエントリです。

それぞれ、

* 2番ポート(s1-eth2)からh3宛のパケットを受信したら4番ポート(s1-eth4)から
  出力する
* 4番ポート(s1-eth4、つまりh3の対向インターフェース)からh1のbond0宛のパ
  ケットを受信したら2番ポート(s1-eth2)から出力する

というフローエントリです。h3とh1の間のの通信にはs1-eth2が使用されていることがわかり
ます。

もちろんホストh4からホストh1に対しても、pingを実行出来ます。
これまでと同様に新たなフローエントリが登録され、
h4とh1の間の通信にはs1-eth1が使用されます。

============ ============
宛先ホスト   使用ポート
============ ============
h2           1
h3           2
h4           1
============ ============

.. only:: latex

   .. image:: images/link_aggregation/fig3.eps
      :scale: 80%
      :align: center

.. only:: epub

   .. image:: images/link_aggregation/fig3.png
      :align: center

.. only:: not latex and not epub

   .. image:: images/link_aggregation/fig3.png
      :scale: 40%
      :align: center

以上のように、通信に応じて複数リンクを使い分ける様子を確認できました。


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
ます。無通信監視時間の90秒が経過すると、コントローラの動作
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

「LACP exchange timeout has occurred.」は無通信監視時間に達し
たことを表します。
ここでは、学習した
MACアドレスと転送用のフローエントリをすべて削除することで、
スイッチを起動直後の状態に戻します。

新たな通信が発生すれば、新たにMACアドレスを学習し、
生きているリンクのみを利用したフローエントリが再び登録されます。

ホストh3とホストh1の間も新たなフローエントリが登録され、

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

ホストh3で停止していたpingが再開します。

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

以上のように、一部のリンクに故障が発生した場合でも、他のリンク
を用いて自動的に復旧できることが確認できました。


Ryuによるリンク・アグリゲーション機能の実装
-------------------------------------------

OpenFlowを用いてど
のようにリンク・アグリゲーション機能を実現しているかを見ていきます。

LACPを用いたリンク・アグリゲーションでは「LACPデータユ
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
* LACPデータユニット以外のパケットは「 :ref:`ch_switching_hub` 」と同様に
  学習・転送する

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


一定時間LACPデータユニットを受信しなかった場合に当該物理インターフェースを
無効にする、という処理は、LACPデータユニットをPacket-Inさせるフローエントリ
にidle_timeoutを設定し、時間切れの際にFlowRemovedメッセージを送信させること
により、OpenFlowコントローラで当該インターフェースが無効になった際の対処を
行うことができます。

無効となったインターフェースでLACPデータユニットの交換が再開された場合の処理
は、LACPデータユニット受信時のPacket-Inメッセージのハンドラで当該インター
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
ターフェースを使用するフローエントリを削除する、としています。

.. NOTE::

    振り分けロジックについては仕様で定められておらず、各機器の実装に委ねられ
    ています。Ryuのリンク・アグリゲーション・アプリケーションでは独自の振り
    分け処理を行わず、対向装置によって振り分けられた経路を使用していま
    す。

ここでは、次のような機能を実装します。

**LACPライブラリ**

* LACPデータユニットを受信したら応答を作成して送信する
* LACPデータユニットの受信が途絶えたら、対応する物理インターフェースを無効とみなし、
  スイッチングハブに通知する
* LACPデータユニットの受信が再開されたら、対応する物理
  インターフェースを有効とみなし、スイッチングハブに通知する

**スイッチングハブ**

* LACPライブラリからの通知を受け、初期化が必要なフローエントリを削除する
* LACPデータユニット以外のパケットは従来どおり学習・転送する


LACPライブラリおよびスイッチングハブのソースコードは、Ryuのソースツリーにあ
ります。

    ryu/lib/lacplib.py

    ryu/app/simple_switch_lacp.py

.. NOTE::

    simple_switch_lacp.pyはOpenFlow 1.0専用のアプリケーション
    であるため、本章では「 `Ryuアプリケーションの実行`_ 」に示した
    OpenFlow 1.3に対応したsimple_switch_lacp_13.pyを元にアプリケーションの
    詳細を説明します。


LACPライブラリの実装
^^^^^^^^^^^^^^^^^^^^

以降の節で、前述の機能がLACPライブラリにおいてどのように実装されてい
るかを見ていきます。なお、引用されているソースは抜粋です。全体像については実
際のソースをご参照ください。


論理インターフェースの作成
""""""""""""""""""""""""""

リンク・アグリゲーション機能を使用するには、どのネットワーク
機器においてどのインターフェースをどのグループとして束ねるのかという設定を事
前に行っておく必要があります。LACPライブラリでは、以下のメソッドでこの設定を
行います。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/lacplib.py
    :dedent: 4
    :pyobject: LacpLib.add

引数の内容は以下のとおりです。

dpid

    OpenFlowスイッチのデータパスIDを指定します。

ports

    グループ化したいポート番号のリストを指定します。

このメソッドを呼び出すことにより、LACPライブラリは指定されたデータパスIDの
OpenFlowスイッチの指定されたポートをひとつのグループとみなします。
複数のグループを作成したい場合は繰り返しadd()メソッドを呼び出し
ます。なお、論理インターフェースに割り当てられるMACアドレスは、OpenFlow
スイッチの持つLOCALポートと同じものが自動的に使用されます。

.. TIP::

    OpenFlowスイッチの中には、スイッチ自身の機能としてリンク・アグリゲー
    ション機能を提供しているものもあります（Open vSwitchなど）。ここではそ
    うしたスイッチ独自の機能は使用せず、OpenFlowコントローラによる制御に
    よってリンク・アグリゲーション機能を実現します。


Packet-In処理
"""""""""""""

「 :ref:`ch_switching_hub` 」は、宛先のMACアドレスが未学
習の場合、受信したパケットをフラッディングします。LACPデータユニットは隣接す
るネットワーク機器間でのみ交換されるべきもので、他の機器に転送してしまうとリ
ンク・アグリゲーション機能が正しく動作しません。そこで、「Packet-Inで受信し
たパケットがLACPデータユニットであれば横取りし、LACPデータユニット
以外のパケットであればスイッチングハブの動作に委ねる」という処理を行い、
スイッチングハブにはLACPデータユニットを見せないようにします。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/lacplib.py
    :dedent: 4
    :prepend: @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    :pyobject: LacpLib.packet_in_handler

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

.. literalinclude:: ../../ryu/lib/lacplib.py
    :pyobject: EventPacketIn

ユーザ定義イベントは、ryu.controller.event.EventBaseクラスを継承して作成
します。イベントクラスに内包するデータに制限はありません。 ``EventPacketIn``
クラスでは、Packet-Inメッセージで受信したryu.ofproto.OFPPacketInインスタン
スをそのまま使用しています。

ユーザ定義イベントの受信方法については後述します。


ポートの有効/無効状態変更に伴う処理
"""""""""""""""""""""""""""""""""""

LACPライブラリのLACPデータユニット受信処理は、以下の処理からなっています。

1. LACPデータユニットを受信したポートが無効状態であれば有効状態に変更
   し、状態が変更したことをイベントで通知します。
2. 無通信タイムアウトの待機時間が変更された場合、LACPデータユニット受信時に
   Packet-Inを送信するフローエントリを再登録します。
3. 受信したLACPデータユニットに対する応答を作成し、送信します。

2.の処理については後述の
「 `LACPデータユニットをPacket-Inさせるフローエントリの登録`_ 」
で、3.の処理については後述の
「 `LACPデータユニットの送受信処理`_ 」
で、それぞれ説明します。ここでは1.の処理について説明します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/lacplib.py
    :dedent: 4
    :prepend: def _do_lacp(self, req_lacp, src, msg):
              # ...
    :pyobject: LacpLib._do_lacp
    :start-after: self.logger.debug(str(req_lacp))
    :end-before: # set the idle_timeout time using the actor state of the
    :append: # ...

_get_slave_enabled()メソッドは、指定したスイッチの指定したポートが有効か否
かを取得します。_set_slave_enabled()メソッドは、指定したスイッチの指定した
ポートの有効/無効状態を設定します。

上記のソースでは、無効状態のポートでLACPデータユニットを受信した場合、ポート
の状態が変更されたということを示す ``EventSlaveStateChanged`` というユーザ
定義イベントを送信しています。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/lacplib.py
    :pyobject: EventSlaveStateChanged

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
が定義されています。リンク・アグリゲーションの仕様では、交換間隔の3倍の時間無通
信状態が続いた場合、そのインターフェースはリンク・アグリゲーションのグループ
から除外され、パケットの転送には使用されなくなります。

LACPライブラリでは、LACPデータユニット受信時にPacket-Inさせるフローエントリ
に対し、交換間隔の3倍の時間（SHORT_TIMEOUT_TIMEは3秒、LONG_TIMEOUT_TIMEは
90秒）をidle_timeoutとして設定することにより、無通信の監視を行っています。

交換間隔が変更された場合、idle_timeoutの時間も再設定する必要があるため、
LACPライブラリでは以下のような実装をしています。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/lacplib.py
    :dedent: 4
    :prepend: def _do_lacp(self, req_lacp, src, msg):
              # ...
    :pyobject: LacpLib._do_lacp
    :start-after: EventSlaveStateChanged(datapath, port, True))
    :end-before: # create a response packet.
    :append: # ...

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

.. literalinclude:: ../../ryu/lib/lacplib.py
    :dedent: 4
    :pyobject: LacpLib._add_flow_v1_2

上記ソースで、「対向インターフェースからLACPデータユニットを受信した場合は
Packet-Inする」というフローエントリを、無通信監視時間つき最高優先度で設定
しています。


LACPデータユニットの送受信処理
""""""""""""""""""""""""""""""

LACPデータユニット受信時、「 `ポートの有効/無効状態変更に伴う処理`_ 」や
「 `LACPデータユニットをPacket-Inさせるフローエントリの登録`_ 」を行った
後、応答用のLACPデータユニットを作成し、送信します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/lacplib.py
    :dedent: 4
    :prepend: def _do_lacp(self, req_lacp, src, msg):
              # ...
    :pyobject: LacpLib._do_lacp
    :start-after: func(src, port, idle_timeout, datapath)

上記ソースで呼び出されている_create_response()メソッドは応答用パケット作成
処理です。その中で呼び出されている_create_lacp()メソッドで応答用のLACPデー
タユニットを作成しています。作成した応答用パケットは、LACPデータユニットを
受信したポートからPacket-Outさせます。

LACPデータユニットには送信側（Actor）の情報と受信側（Partner）の情報を設定
します。受信したLACPデータユニットの送信側情報には対向インターフェースの情報
が記載されているので、OpenFlowスイッチから応答を返すときにはそれを受信側情報
として設定します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/lacplib.py
    :dedent: 4
    :prepend: @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    :pyobject: LacpLib._create_lacp

FlowRemovedメッセージの受信処理
"""""""""""""""""""""""""""""""

指定された時間の間LACPデータユニットの交換が行われなかった場合、OpenFlowス
イッチはFlowRemovedメッセージをOpenFlowコントローラに送信します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/lacplib.py
    :dedent: 4
    :prepend: @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    :pyobject: LacpLib.flow_removed_handler

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

.. literalinclude:: ../../ryu/app/simple_switch_lacp_13.py
    :prepend: from ryu.lib import lacplib
              # ...
    :pyobject: SimpleSwitchLacp13
    :end-before: __init__
    :append: # ...

「_CONTEXTS」に設定したアプリケーションは、__init__()メソッドのkwargsから
インスタンスを取得することができます。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_lacp_13.py
    :dedent: 4
    :pyobject: SimpleSwitchLacp13.__init__
    :end-before: self._lacp.add
    :append: # ...

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

.. literalinclude:: ../../ryu/app/simple_switch_lacp_13.py
    :dedent: 4
    :prepend: def __init__(self, *args, **kwargs):
              # ...
    :pyobject: SimpleSwitchLacp13.__init__
    :start-after: self.mac_to_port = {}

ユーザ定義イベントの受信方法
""""""""""""""""""""""""""""

`LACPライブラリの実装`_ で説明したとおり、LACPライブラリはLACPデータユニッ
トの含まれないPacket-Inメッセージを ``EventPacketIn`` というユーザ定義イ
ベントとして送信します。ユーザ定義イベントのイベントハンドラも、Ryuが提供す
るイベントハンドラと同じように ``ryu.controller.handler.set_ev_cls`` デコ
レータで装飾します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_lacp_13.py
    :dedent: 4
    :prepend: @set_ev_cls(lacplib.EventPacketIn, MAIN_DISPATCHER)
    :pyobject: SimpleSwitchLacp13._packet_in_handler
    :end-before: pkt = packet.Packet(msg.data)
    :append: # ...

また、LACPライブラリはポートの有効/無効状態が変更されると
``EventSlaveStateChanged`` イベントを送信しますので、こちらもイベントハンド
ラを作成しておきます。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_lacp_13.py
    :dedent: 4
    :prepend: @set_ev_cls(lacplib.EventSlaveStateChanged, MAIN_DISPATCHER)
    :pyobject: SimpleSwitchLacp13._slave_state_changed_handler

本節の冒頭で説明したとおり、ポートの有効/無効状態が変更され
ると、論理インターフェースを通
過するパケットが実際に使用する物理インターフェースが変更になる可能性がありま
す。そのため、登録されているフローエントリを全て削除
しています。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_lacp_13.py
    :dedent: 4
    :pyobject: SimpleSwitchLacp13.del_flow

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
