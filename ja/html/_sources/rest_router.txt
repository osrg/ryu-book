.. _ch_rest_router:

rest_router.pyの使用例
======================

本章では、「 :ref:`ch_rest_api` 」を拡張して実装され、Ryuのソースツリーに登
録されているryu/app/rest_router.pyの使用方法について説明します。


シングルテナントでの動作例
--------------------------

まず、VLANによるテナント分けのされていない以下のようなトポロジを作成し、各ス
イッチ(ルータ)に対してアドレスやルートの追加・削除を行い、各ホスト間の疎通可
否を確認する例を紹介します。

.. only:: latex

  .. image:: images/rest_router/fig1.eps
     :scale: 80%
     :align: center

.. only:: not latex

  .. image:: images/rest_router/fig1.png
     :scale: 80%
     :align: center


環境構築
^^^^^^^^

まずはMininet上に環境を構築します。 ``mn`` コマンドのパラメータは以下のよう
になります。

============ ========== ===========================================
パラメータ   値         説明
============ ========== ===========================================
topo         linear,3   3台のスイッチが直列に接続されているトポロジ
mac          なし       自動的にホストのMACアドレスをセットする
switch       ovsk       Open vSwitchを使用する
controller   remote     OpenFlowコントローラは外部のものを利用する
x            なし       xtermを起動する
============ ========== ===========================================

実行例は以下のようになります。

.. rst-class:: console

::

    ryu@ryu-vm:~$ sudo mn --topo linear,3 --mac --switch ovsk --controller remote -x
    *** Creating network
    *** Adding controller
    Unable to contact the remote controller at 127.0.0.1:6633
    *** Adding hosts:
    h1 h2 h3
    *** Adding switches:
    s1 s2 s3
    *** Adding links:
    (h1, s1) (h2, s2) (h3, s3) (s1, s2) (s2, s3)
    *** Configuring hosts
    h1 h2 h3
    *** Running terms on localhost:10.0
    *** Starting controller
    *** Starting 3 switches
    s1 s2 s3

    *** Starting CLI:
    mininet>

また、コントローラ用のxtermをもうひとつ起動しておきます。

.. rst-class:: console

::

    mininet> xterm c0
    mininet>

続いて、各ルータで使用するOpenFlowのバージョンを1.3に設定します。

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13

switch: s2 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s2 protocols=OpenFlow13

switch: s3 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s3 protocols=OpenFlow13

.. ATTENTION::

    Ryu3.2に含まれているrest_router.pyはOpenFlow1.3以降に対応していませ
    ん。Ryu3.3以降をご利用ください。

その後、各ホストで自動的に割り当てられているIPアドレスを削除し、新たにIPア
ドレスを設定します。

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.1/8 dev h1-eth0
    root@ryu-vm:~# ip addr add 172.16.20.10/24 dev h1-eth0

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.2/8 dev h2-eth0
    root@ryu-vm:~# ip addr add 172.16.10.10/24 dev h2-eth0

host: h3:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.3/8 dev h3-eth0
    root@ryu-vm:~# ip addr add 192.168.30.10/24 dev h3-eth0

最後に、コントローラのxterm上でrest_routerを起動させます。

controller: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# cd ryu
    root@ryu-vm:~/ryu# ryu-manager ryu/app/rest_router.py
    loading app ryu/app/rest_router.py
    loading app ryu.controller.ofp_handler
    instantiating app None of DPSet
    creating context dpset
    creating context wsgi
    instantiating app ryu/app/rest_router.py of RestRouterAPI
    instantiating app ryu.controller.ofp_handler of OFPHandler
    (2447) wsgi starting up on http://0.0.0.0:8080/

Ryuとルータの間の接続に成功すると、次のメッセージが表示されます。

controller: c0 (root):

.. rst-class:: console

::

    [RT][INFO] switch_id=0000000000000003: Set SW config for TTL error packet in.
    [RT][INFO] switch_id=0000000000000003: Set ARP handling (packet in) flow [cookie=0x0]
    [RT][INFO] switch_id=0000000000000003: Set L2 switching (normal) flow [cookie=0x0]
    [RT][INFO] switch_id=0000000000000003: Set default route (drop) flow [cookie=0x0]
    [RT][INFO] switch_id=0000000000000003: Start cyclic routing table update.
    [RT][INFO] switch_id=0000000000000003: Join as router.
    ...

上記ログがルータ3台分表示されれば準備完了です。

この時点での各ルータのフローエントリは以下のようになっています。

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=10.988s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=drop
     cookie=0x0, duration=10.988s, table=0, n_packets=0, n_bytes=0, priority=1,arp actions=CONTROLLER:65535
     cookie=0x0, duration=10.988s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL

switch: s2 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s2
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=85.928s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=drop
     cookie=0x0, duration=85.928s, table=0, n_packets=0, n_bytes=0, priority=1,arp actions=CONTROLLER:65535
     cookie=0x0, duration=85.928s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL

switch: s3 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s3
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=117.248s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=drop
     cookie=0x0, duration=117.248s, table=0, n_packets=0, n_bytes=0, priority=1,arp actions=CONTROLLER:65535
     cookie=0x0, duration=117.248s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL


アドレスの設定
^^^^^^^^^^^^^^

各ルータにアドレスを設定します。

まず、ルータs1にアドレス「172.16.20.1/24」と「172.16.30.30/24」を設定しま
す。

.. NOTE::

    以降の説明で使用するREST APIの詳細は、章末の「 `REST API一覧`_ 」を参照
    してください。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"address":"172.16.20.1/24"}' http://localhost:8080/router/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"address": "172.16.30.30/24"}' http://localhost:8080/router/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]

.. NOTE::

    RESTコマンドの実行結果は見やすいように整形しています。

続いて、ルータs2にアドレス「172.16.10.1/24」「172.16.30.1/24」
「192.168.10.1/24」を設定します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"address":"172.16.10.1/24"}' http://localhost:8080/router/0000000000000002
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"address": "172.16.30.1/24"}' http://localhost:8080/router/0000000000000002
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"address": "192.168.10.1/24"}' http://localhost:8080/router/0000000000000002
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "details": "Add address [address_id=3]"
            }
          ]
        }
      ]

さらに、ルータs3にアドレス「192.168.30.1/24」と「192.168.10.20/24」を設定
します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"address": "192.168.30.1/24"}' http://localhost:8080/router/0000000000000003
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"address": "192.168.10.20/24"}' http://localhost:8080/router/0000000000000003
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]

この時点での各ルータのフローエントリを詳しく見ていきます。

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x2, duration=2959.014s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=172.16.30.30 actions=CONTROLLER:65535
     cookie=0x1, duration=2968.377s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=172.16.20.1 actions=CONTROLLER:65535
     cookie=0x1, duration=2968.377s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=172.16.20.0/24,nw_dst=172.16.20.0/24 actions=NORMAL
     cookie=0x2, duration=2959.013s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=172.16.30.0/24,nw_dst=172.16.30.0/24 actions=NORMAL
     cookie=0x0, duration=3264.839s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=drop
     cookie=0x0, duration=3264.839s, table=0, n_packets=4, n_bytes=168, priority=1,arp actions=CONTROLLER:65535
     cookie=0x0, duration=3264.839s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL
     cookie=0x1, duration=2968.378s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=172.16.20.0/24 actions=CONTROLLER:65535
     cookie=0x2, duration=2959.016s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=172.16.30.0/24 actions=CONTROLLER:65535

ルータs1には「172.16.20.1/24」と「172.16.30.30/24」というアドレスを設定し
ました。

1番めと2番めに登録されている優先度1037のフローエントリは、「ルータ宛のパケッ
トが到達したらPacket-Inメッセージを送信する」というものです。

3番めと4番めに登録されている優先度36のフローエントリは、「同じサブネット内宛
のパケットが到達したら通常のL2スイッチと同じように振る舞う」というものです。

一番下とその上の優先度2のフローエントリは、「 :ref:`ch_switching_hub` 」の
スイッチングハブと同等の機能です。

.. NOTE::

    確認するタイミングによっては、idle_timeout=1800のフローエントリが登録さ
    れている場合があります。これは上記スイッチングハブ機能によって登録された
    ものです。REST APIによって明示的に登録したフローエントリではないため、
    ここでは説明を省略します。

s2とs3にも、s1と同様に3種類のフローエントリが追加されます。

switch: s2 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s2
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x3, duration=2088.278s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=192.168.10.1 actions=CONTROLLER:65535
     cookie=0x1, duration=2108.172s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=172.16.10.1 actions=CONTROLLER:65535
     cookie=0x2, duration=2099.929s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=172.16.30.1 actions=CONTROLLER:65535
     cookie=0x1, duration=2108.172s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=172.16.10.0/24,nw_dst=172.16.10.0/24 actions=NORMAL
     cookie=0x3, duration=2088.278s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=192.168.10.0/24,nw_dst=192.168.10.0/24 actions=NORMAL
     cookie=0x2, duration=2099.928s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=172.16.30.0/24,nw_dst=172.16.30.0/24 actions=NORMAL
     cookie=0x0, duration=2433.12s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=drop
     cookie=0x0, duration=2433.12s, table=0, n_packets=4, n_bytes=168, priority=1,arp actions=CONTROLLER:65535
     cookie=0x0, duration=2433.12s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL
     cookie=0x3, duration=2088.278s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=192.168.10.0/24 actions=CONTROLLER:65535
     cookie=0x1, duration=2108.173s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=172.16.10.0/24 actions=CONTROLLER:65535
     cookie=0x2, duration=2099.929s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=172.16.30.0/24 actions=CONTROLLER:65535

switch: s3 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s3
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x2, duration=3034.293s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=192.168.10.20 actions=CONTROLLER:65535
     cookie=0x1, duration=3047.037s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=192.168.30.1 actions=CONTROLLER:65535
     cookie=0x1, duration=3047.037s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=192.168.30.0/24,nw_dst=192.168.30.0/24 actions=NORMAL
     cookie=0x2, duration=3034.293s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=192.168.10.0/24,nw_dst=192.168.10.0/24 actions=NORMAL
     cookie=0x0, duration=3410.131s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=drop
     cookie=0x0, duration=3410.131s, table=0, n_packets=3, n_bytes=126, priority=1,arp actions=CONTROLLER:65535
     cookie=0x0, duration=3410.131s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL
     cookie=0x2, duration=3034.294s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=192.168.10.0/24 actions=CONTROLLER:65535
     cookie=0x1, duration=3047.038s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=192.168.30.0/24 actions=CONTROLLER:65535

この時点でのトポロジは、次のようなものになります。

.. only:: latex

  .. image:: images/rest_router/fig2.eps
     :scale: 80%
     :align: center

.. only:: not latex

  .. image:: images/rest_router/fig2.png
     :scale: 80%
     :align: center

各ルータにIPアドレスが割り当てられたので、各ホストのデフォルトゲートウェイを
登録します。各ホストは隣接するルータに割り当てられたIPアドレスのうち、サブ
ネットが等しいものをデフォルトゲートウェイとして設定します。

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ip route add default via 172.16.20.1

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# ip route add default via 172.16.10.1

host: h3:

.. rst-class:: console

::

    root@ryu-vm:~# ip route add default via 192.168.30.1

この時点でのトポロジは、次のようなものになります。

.. only:: latex

  .. image:: images/rest_router/fig3.eps
     :scale: 80%
     :align: center

.. only:: not latex

  .. image:: images/rest_router/fig3.png
     :scale: 80%
     :align: center


デフォルトルートの設定
^^^^^^^^^^^^^^^^^^^^^^

各ルータにデフォルトルートを設定します。

まず、ルータs1のデフォルトルートとしてルータs2を設定します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"gateway": "172.16.30.1"}' http://localhost:8080/router/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]

ルータs2のデフォルトルートにはルータs1を設定します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"gateway": "172.16.30.30"}' http://localhost:8080/router/0000000000000002
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]

ルータs3のデフォルトルートにはルータs2を設定します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"gateway": "192.168.10.1"}' http://localhost:8080/router/0000000000000003
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]

この時点での各ルータのフローエントリを詳しく見ていきます。

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x2, duration=300.558s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=172.16.30.30 actions=CONTROLLER:65535
     cookie=0x1, duration=347.48s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=172.16.20.1 actions=CONTROLLER:65535
     cookie=0x1, duration=347.48s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=172.16.20.0/24,nw_dst=172.16.20.0/24 actions=NORMAL
     cookie=0x2, duration=300.558s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=172.16.30.0/24,nw_dst=172.16.30.0/24 actions=NORMAL
     cookie=0x10000, duration=63.768s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=dec_ttl,set_field:ea:35:54:4a:f4:58->eth_src,set_field:f2:97:d6:37:76:4f->eth_dst,output:2
     cookie=0x0, duration=424.577s, table=0, n_packets=6, n_bytes=252, priority=1,arp actions=CONTROLLER:65535
     cookie=0x0, duration=424.577s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL
     cookie=0x1, duration=347.48s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=172.16.20.0/24 actions=CONTROLLER:65535
     cookie=0x2, duration=300.559s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=172.16.30.0/24 actions=CONTROLLER:65535

5番めに優先度1のフローエントリが追加されています。その内容は「送信元MACを
ルータs1、宛先MACをルータs2に書き換え、TTLを減らし、デフォルトルートに向け
て送信する」であり、一般的なルータの動作と同様のものです。

s2とs3にも、s1と同様のフローエントリが追加されます。

switch: s2 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s2
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x3, duration=320.843s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=192.168.10.1 actions=CONTROLLER:65535
     cookie=0x1, duration=366.178s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=172.16.10.1 actions=CONTROLLER:65535
     cookie=0x2, duration=344.069s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=172.16.30.1 actions=CONTROLLER:65535
     cookie=0x1, duration=366.178s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=172.16.10.0/24,nw_dst=172.16.10.0/24 actions=NORMAL
     cookie=0x3, duration=320.843s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=192.168.10.0/24,nw_dst=192.168.10.0/24 actions=NORMAL
     cookie=0x2, duration=344.069s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=172.16.30.0/24,nw_dst=172.16.30.0/24 actions=NORMAL
     cookie=0x10000, duration=134.406s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=dec_ttl,set_field:f2:97:d6:37:76:4f->eth_src,set_field:ea:35:54:4a:f4:58->eth_dst,output:2
     cookie=0x0, duration=516.45s, table=0, n_packets=7, n_bytes=294, priority=1,arp actions=CONTROLLER:65535
     cookie=0x0, duration=516.45s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL
     cookie=0x3, duration=320.844s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=192.168.10.0/24 actions=CONTROLLER:65535
     cookie=0x1, duration=366.179s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=172.16.10.0/24 actions=CONTROLLER:65535
     cookie=0x2, duration=344.069s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=172.16.30.0/24 actions=CONTROLLER:65535

switch: s3 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s3
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x2, duration=387.061s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=192.168.10.20 actions=CONTROLLER:65535
     cookie=0x1, duration=410.033s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=192.168.30.1 actions=CONTROLLER:65535
     cookie=0x1, duration=410.033s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=192.168.30.0/24,nw_dst=192.168.30.0/24 actions=NORMAL
     cookie=0x2, duration=387.061s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=192.168.10.0/24,nw_dst=192.168.10.0/24 actions=NORMAL
     cookie=0x10000, duration=223.636s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=dec_ttl,set_field:62:4f:3c:69:70:ef->eth_src,set_field:4a:5e:39:87:3c:14->eth_dst,output:2
     cookie=0x0, duration=623.403s, table=0, n_packets=5, n_bytes=210, priority=1,arp actions=CONTROLLER:65535
     cookie=0x0, duration=623.403s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL
     cookie=0x2, duration=387.061s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=192.168.10.0/24 actions=CONTROLLER:65535
     cookie=0x1, duration=410.034s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=192.168.30.0/24 actions=CONTROLLER:65535


静的ルートの設定
^^^^^^^^^^^^^^^^

ルータs2に対し、ルータs3配下のホスト(192.168.30.0/24)へのスタティックルート
を設定します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"destination": "192.168.30.0/24", "gateway": "192.168.10.20"}' http://localhost:8080/router/0000000000000002
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "details": "Add route [route_id=2]"
            }
          ]
        }
      ]

この時点でのルータs2のフローエントリを確認してみます。

switch: s2 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s2
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x3, duration=498.185s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=192.168.10.1 actions=CONTROLLER:65535
     cookie=0x1, duration=543.52s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=172.16.10.1 actions=CONTROLLER:65535
     cookie=0x2, duration=521.411s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=172.16.30.1 actions=CONTROLLER:65535
     cookie=0x1, duration=543.52s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=172.16.10.0/24,nw_dst=172.16.10.0/24 actions=NORMAL
     cookie=0x3, duration=498.185s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=192.168.10.0/24,nw_dst=192.168.10.0/24 actions=NORMAL
     cookie=0x2, duration=521.411s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=172.16.30.0/24,nw_dst=172.16.30.0/24 actions=NORMAL
     cookie=0x10000, duration=311.748s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=dec_ttl,set_field:f2:97:d6:37:76:4f->eth_src,set_field:ea:35:54:4a:f4:58->eth_dst,output:2
     cookie=0x0, duration=693.792s, table=0, n_packets=8, n_bytes=336, priority=1,arp actions=CONTROLLER:65535
     cookie=0x0, duration=693.792s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL
     cookie=0x3, duration=498.186s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=192.168.10.0/24 actions=CONTROLLER:65535
     cookie=0x1, duration=543.521s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=172.16.10.0/24 actions=CONTROLLER:65535
     cookie=0x20000, duration=14.78s, table=0, n_packets=0, n_bytes=0, priority=26,ip,nw_dst=192.168.30.0/24 actions=dec_ttl,set_field:4a:5e:39:87:3c:14->eth_src,set_field:62:4f:3c:69:70:ef->eth_dst,output:3
     cookie=0x2, duration=521.411s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=172.16.30.0/24 actions=CONTROLLER:65535

下から2番めのフローエントリが追加されています。その内容は「宛先IPアドレスが
192.168.30.0/24であれば、送信元MACをルータs2、宛先MACをルータs3に書き換え、
TTLを減らし、ルータs3に向けて送信する」というものです。

この時点でのトポロジは、次のようなものになります。

.. only:: latex

  .. image:: images/rest_router/fig4.eps
     :scale: 80%
     :align: center

.. only:: not latex

  .. image:: images/rest_router/fig4.png
     :scale: 80%
     :align: center


設定内容の確認
^^^^^^^^^^^^^

各ルータに設定された内容を確認します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl http://localhost:8080/router/0000000000000001
      [
        {
          "internal_network": [
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "172.16.30.1"
                }
              ],
              "address": [
                {
                  "address_id": 1,
                  "address": "172.16.20.1/24"
                },
                {
                  "address_id": 2,
                  "address": "172.16.30.30/24"
                }
              ]
            }
          ],
          "switch_id": "0000000000000001"
        }
      ]

    root@ryu-vm:~# curl http://localhost:8080/router/0000000000000002
      [
        {
          "internal_network": [
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "172.16.30.30"
                },
                {
                  "route_id": 2,
                  "destination": "192.168.30.0/24",
                  "gateway": "192.168.10.20"
                }
              ],
              "address": [
                {
                  "address_id": 2,
                  "address": "172.16.30.1/24"
                },
                {
                  "address_id": 3,
                  "address": "192.168.10.1/24"
                },
                {
                  "address_id": 1,
                  "address": "172.16.10.1/24"
                }
              ]
            }
          ],
          "switch_id": "0000000000000002"
        }
      ]

    root@ryu-vm:~# curl http://localhost:8080/router/0000000000000003
      [
        {
          "internal_network": [
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "192.168.10.1"
                }
              ],
              "address": [
                {
                  "address_id": 1,
                  "address": "192.168.30.1/24"
                },
                {
                  "address_id": 2,
                  "address": "192.168.10.20/24"
                }
              ]
            }
          ],
          "switch_id": "0000000000000003"
        }
      ]

この状態で、pingによる疎通を確認してみます。まず、h2からh3へpingを実行しま
す。正常に疎通できることが確認できます。

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# ping 192.168.30.10
    PING 192.168.30.10 (192.168.30.10) 56(84) bytes of data.
    64 bytes from 192.168.30.10: icmp_req=1 ttl=62 time=48.8 ms
    64 bytes from 192.168.30.10: icmp_req=2 ttl=62 time=0.402 ms
    64 bytes from 192.168.30.10: icmp_req=3 ttl=62 time=0.089 ms
    64 bytes from 192.168.30.10: icmp_req=4 ttl=62 time=0.065 ms
    ...

また、h2からh1へpingを実行します。こちらも正常に疎通できることが確認できま
す。

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# ping 172.16.20.10
    PING 172.16.20.10 (172.16.20.10) 56(84) bytes of data.
    64 bytes from 172.16.20.10: icmp_req=1 ttl=62 time=43.2 ms
    64 bytes from 172.16.20.10: icmp_req=2 ttl=62 time=0.306 ms
    64 bytes from 172.16.20.10: icmp_req=3 ttl=62 time=0.057 ms
    64 bytes from 172.16.20.10: icmp_req=4 ttl=62 time=0.048 ms
    ...


静的ルートの削除
^^^^^^^^^^^^^^^^

ルータs2に設定したルータs3へのスタティックルートを削除します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X DELETE -d '{"route_id": "2"}' http://localhost:8080/router/0000000000000002
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "details": "Delete route [route_id=2]"
            }
          ]
        }
      ]

ルータs2に設定された情報を確認してみます。ルータs3へのスタティックルートが
削除されていることがわかります。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl http://localhost:8080/router/0000000000000002
      [
        {
          "internal_network": [
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "172.16.30.30"
                }
              ],
              "address": [
                {
                  "address_id": 2,
                  "address": "172.16.30.1/24"
                },
                {
                  "address_id": 3,
                  "address": "192.168.10.1/24"
                },
                {
                  "address_id": 1,
                  "address": "172.16.10.1/24"
                }
              ]
            }
          ],
          "switch_id": "0000000000000002"
        }
      ]

この時点でのルータs2のフローエントリを確認してみます。
「 `静的ルートの設定`_ 」で追加されたcookie=0x20000のフローエントリが削除
されていることがわかります。

switch: s2 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s2
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x3, duration=966.583s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=192.168.10.1 actions=CONTROLLER:65535
     cookie=0x1, duration=1011.918s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=172.16.10.1 actions=CONTROLLER:65535
     cookie=0x2, duration=989.809s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=172.16.30.1 actions=CONTROLLER:65535
     cookie=0x1, duration=1011.918s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=172.16.10.0/24,nw_dst=172.16.10.0/24 actions=NORMAL
     cookie=0x3, duration=966.583s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=192.168.10.0/24,nw_dst=192.168.10.0/24 actions=NORMAL
     cookie=0x2, duration=989.809s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=172.16.30.0/24,nw_dst=172.16.30.0/24 actions=NORMAL
     cookie=0x10000, duration=780.146s, table=0, n_packets=3, n_bytes=294, priority=1,ip actions=dec_ttl,set_field:f2:97:d6:37:76:4f->eth_src,set_field:ea:35:54:4a:f4:58->eth_dst,output:2
     cookie=0x0, duration=1162.19s, table=0, n_packets=9, n_bytes=378, priority=1,arp actions=CONTROLLER:65535
     cookie=0x0, duration=1162.19s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL
     cookie=0x3, duration=966.584s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=192.168.10.0/24 actions=CONTROLLER:65535
     cookie=0x1, duration=1011.919s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=172.16.10.0/24 actions=CONTROLLER:65535
     cookie=0x2, duration=989.809s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=172.16.30.0/24 actions=CONTROLLER:65535

この状態で、pingによる疎通を確認してみます。h2からh3へはルート情報がなくなっ
たため、疎通できないことがわかります。

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# ping 192.168.30.10
    PING 192.168.30.10 (192.168.30.10) 56(84) bytes of data.
    ^C
    --- 192.168.30.10 ping statistics ---
    12 packets transmitted, 0 received, 100% packet loss, time 11088ms


アドレスの削除
^^^^^^^^^^^^^^

ルータs1に設定したアドレス「172.16.20.1/24」を削除します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X DELETE -d '{"address_id": "1"}' http://localhost:8080/router/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Delete address [address_id=1]"
            }
          ]
        }
      ]

ルータs1に設定された情報を確認してみます。ルータs1に設定されたIPアドレスの
うち、「172.16.20.1/24」が削除されていることがわかります。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl http://localhost:8080/router/0000000000000001
      [
        {
          "internal_network": [
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "172.16.30.1"
                }
              ],
              "address": [
                {
                  "address_id": 2,
                  "address": "172.16.30.30/24"
                }
              ]
            }
          ],
          "switch_id": "0000000000000001"
        }
      ]

この時点でのルータs1のフローエントリを確認してみます。IPアドレス
「172.16.20.1/24」が削除されたことにより、当該アドレスに関連するフローエン
トリが削除されていることがわかります。

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x2, duration=1672.897s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,nw_dst=172.16.30.30 actions=CONTROLLER:65535
     cookie=0x2, duration=1672.897s, table=0, n_packets=0, n_bytes=0, priority=36,ip,nw_src=172.16.30.0/24,nw_dst=172.16.30.0/24 actions=NORMAL
     cookie=0x10000, duration=1436.107s, table=0, n_packets=15, n_bytes=1470, priority=1,ip actions=dec_ttl,set_field:ea:35:54:4a:f4:58->eth_src,set_field:f2:97:d6:37:76:4f->eth_dst,output:2
     cookie=0x0, duration=1796.916s, table=0, n_packets=9, n_bytes=378, priority=1,arp actions=CONTROLLER:65535
     cookie=0x0, duration=1796.916s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL
     cookie=0x2, duration=1672.898s, table=0, n_packets=0, n_bytes=0, priority=2,ip,nw_dst=172.16.30.0/24 actions=CONTROLLER:65535

この状態で、pingによる疎通を確認してみます。h2からh1へは、h1の所属するサブ
ネットに関する情報がルータs1から削除されたため、疎通できないことがわかりま
す。

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# ping 172.16.20.10
    PING 172.16.20.10 (172.16.20.10) 56(84) bytes of data.
    ^C
    --- 172.16.20.10 ping statistics ---
    19 packets transmitted, 0 received, 100% packet loss, time 18004ms


マルチテナントでの動作例
------------------------

続いて、VLANによるテナント分けが行われている以下のようなトポロジを作成し、各
スイッチ(ルータ)に対してアドレスやルートの追加・削除を行い、各ホスト間の疎通
可否を確認する例を紹介します。

.. only:: latex

  .. image:: images/rest_router/fig5.eps
     :scale: 80%
     :align: center

.. only:: not latex

  .. image:: images/rest_router/fig5.png
     :scale: 80%
     :align: center

環境構築
^^^^^^^^

まずはMininet上に環境を構築します。 ``mn`` コマンドのパラメータは以下のよう
になります。

============ ============ ===========================================
パラメータ   値           説明
============ ============ ===========================================
topo         linear,3,2   3台のスイッチが直列に接続されているトポロジ

                          (各スイッチに2台のホストが接続される)
mac          なし         自動的にホストのMACアドレスをセットする
switch       ovsk         Open vSwitchを使用する
controller   remote       OpenFlowコントローラは外部のものを利用する
x            なし         xtermを起動する
============ ============ ===========================================


実行例は以下のようになります。

.. rst-class:: console

::

    ryu@ryu-vm:~$ sudo mn --topo linear,3,2 --mac --switch ovsk --controller remote -x
    *** Creating network
    *** Adding controller
    Unable to contact the remote controller at 127.0.0.1:6633
    *** Adding hosts:
    h1s1 h1s2 h1s3 h2s1 h2s2 h2s3
    *** Adding switches:
    s1 s2 s3
    *** Adding links:
    (h1s1, s1) (h1s2, s2) (h1s3, s3) (h2s1, s1) (h2s2, s2) (h2s3, s3) (s1, s2) (s2, s3)
    *** Configuring hosts
    h1s1 h1s2 h1s3 h2s1 h2s2 h2s3
    *** Running terms on localhost:10.0
    *** Starting controller
    *** Starting 3 switches
    s1 s2 s3
    *** Starting CLI:
    mininet>

.. ATTENTION::

    リニアトポロジでのホスト台数はMininet 2.1.0以降で指定可能です。

また、コントローラ用のxtermをもうひとつ起動しておきます。

.. rst-class:: console

::

    mininet> xterm c0
    mininet>

続いて、各ルータで使用するOpenFlowのバージョンを1.3に設定します。

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13

switch: s2 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s2 protocols=OpenFlow13

switch: s3 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s3 protocols=OpenFlow13

.. ATTENTION::

    Ryu3.2に含まれているrest_router.pyはOpenFlow1.3以降に対応していませ
    ん。Ryu3.3以降をご利用ください。

その後、各ホストのインターフェースに VLAN ID を設定し、新たにIPアドレスを設
定します。

host: h1s1:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.1/8 dev h1s1-eth0
    root@ryu-vm:~# ip link add link h1s1-eth0 name h1s1-eth0.2 type vlan id 2
    root@ryu-vm:~# ip addr add 172.16.10.10/24 dev h1s1-eth0.2
    root@ryu-vm:~# ip link set dev h1s1-eth0.2 up

host: h2s1:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.4/8 dev h2s1-eth0
    root@ryu-vm:~# ip link add link h2s1-eth0 name h2s1-eth0.110 type vlan id 110
    root@ryu-vm:~# ip addr add 172.16.10.11/24 dev h2s1-eth0.110
    root@ryu-vm:~# ip link set dev h2s1-eth0.110 up

host: h1s2:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.2/8 dev h1s2-eth0
    root@ryu-vm:~# ip link add link h1s2-eth0 name h1s2-eth0.2 type vlan id 2
    root@ryu-vm:~# ip addr add 192.168.30.10/24 dev h1s2-eth0.2
    root@ryu-vm:~# ip link set dev h1s2-eth0.2 up

host: h2s2:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.5/8 dev h2s2-eth0
    root@ryu-vm:~# ip link add link h2s2-eth0 name h2s2-eth0.110 type vlan id 110
    root@ryu-vm:~# ip addr add 192.168.30.11/24 dev h2s2-eth0.110
    root@ryu-vm:~# ip link set dev h2s2-eth0.110 up

host: h1s3:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.3/8 dev h1s3-eth0
    root@ryu-vm:~# ip link add link h1s3-eth0 name h1s3-eth0.2 type vlan id 2
    root@ryu-vm:~# ip addr add 172.16.20.10/24 dev h1s3-eth0.2
    root@ryu-vm:~# ip link set dev h1s3-eth0.2 up

host: h2s3:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.6/8 dev h2s3-eth0
    root@ryu-vm:~# ip link add link h2s3-eth0 name h2s3-eth0.110 type vlan id 110
    root@ryu-vm:~# ip addr add 172.16.20.11/24 dev h2s3-eth0.110
    root@ryu-vm:~# ip link set dev h2s3-eth0.110 up

最後に、コントローラのxterm上でrest_routerを起動させます。

controller: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# cd ryu
    root@ryu-vm:~/ryu# ryu-manager ryu/app/rest_router.py
    loading app ryu/app/rest_router.py
    loading app ryu.controller.ofp_handler
    instantiating app None of DPSet
    creating context dpset
    creating context wsgi
    instantiating app ryu/app/rest_router.py of RestRouterAPI
    instantiating app ryu.controller.ofp_handler of OFPHandler
    (2447) wsgi starting up on http://0.0.0.0:8080/

Ryuとルータの間の接続に成功すると、次のメッセージが表示されます。

controller: c0 (root):

.. rst-class:: console

::

    [RT][INFO] switch_id=0000000000000003: Set SW config for TTL error packet in.
    [RT][INFO] switch_id=0000000000000003: Set ARP handling (packet in) flow [cookie=0x0]
    [RT][INFO] switch_id=0000000000000003: Set L2 switching (normal) flow [cookie=0x0]
    [RT][INFO] switch_id=0000000000000003: Set default route (drop) flow [cookie=0x0]
    [RT][INFO] switch_id=0000000000000003: Start cyclic routing table update.
    [RT][INFO] switch_id=0000000000000003: Join as router.
    ...

上記ログがルータ3台分表示されれば準備完了です。

この時点での各ルータのフローエントリは以下のようになっています。

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=10.988s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=drop
     cookie=0x0, duration=10.988s, table=0, n_packets=0, n_bytes=0, priority=1,arp actions=CONTROLLER:65535
     cookie=0x0, duration=10.988s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL

switch: s2 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s2
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=85.928s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=drop
     cookie=0x0, duration=85.928s, table=0, n_packets=0, n_bytes=0, priority=1,arp actions=CONTROLLER:65535
     cookie=0x0, duration=85.928s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL

switch: s3 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s3
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=117.248s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=drop
     cookie=0x0, duration=117.248s, table=0, n_packets=0, n_bytes=0, priority=1,arp actions=CONTROLLER:65535
     cookie=0x0, duration=117.248s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL


アドレスの設定
^^^^^^^^^^^^^^


各ルータにアドレスを設定します。

まず、ルータs1にアドレス「172.16.20.1/24」と「10.10.10.1/24」を設定しま
す。それぞれVLAN IDごとに設定する必要があります。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"address": "172.16.10.1/24"}' http://localhost:8080/router/0000000000000001/2
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"address": "10.10.10.1/24"}' http://localhost:8080/router/0000000000000001/2
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"address": "172.16.10.1/24"}' http://localhost:8080/router/0000000000000001/110
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"address": "10.10.10.1/24"}' http://localhost:8080/router/0000000000000001/110
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]

続いて、ルータs2にアドレス「192.168.30.1/24」と「10.10.10.2/24」を設定し
ます。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"address": "192.168.30.1/24"}' http://localhost:8080/router/0000000000000002/2
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"address": "10.10.10.2/24"}' http://localhost:8080/router/0000000000000002/2
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"address": "192.168.30.1/24"}' http://localhost:8080/router/0000000000000002/110
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"address": "10.10.10.2/24"}' http://localhost:8080/router/0000000000000002/110
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]

さらに、ルータs3にアドレス「172.16.20.1/24」と「10.10.10.3/24」を設定しま
す。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"address": "172.16.20.1/24"}' http://localhost:8080/router/0000000000000003/2
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"address": "10.10.10.3/24"}' http://localhost:8080/router/0000000000000003/2
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"address": "172.16.20.1/24"}' http://localhost:8080/router/0000000000000003/110
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"address": "10.10.10.3/24"}' http://localhost:8080/router/0000000000000003/110
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]

この時点での各ルータのフローエントリを詳しく見ていきます。

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x200000002, duration=138.463s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=2,nw_src=10.10.10.0/24,nw_dst=10.10.10.0/24 actions=NORMAL
     cookie=0x6e00000001, duration=131.325s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=110,nw_src=172.16.10.0/24,nw_dst=172.16.10.0/24 actions=NORMAL
     cookie=0x200000001, duration=149.877s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=2,nw_src=172.16.10.0/24,nw_dst=172.16.10.0/24 actions=NORMAL
     cookie=0x6e00000002, duration=127.795s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=110,nw_src=10.10.10.0/24,nw_dst=10.10.10.0/24 actions=NORMAL
     cookie=0x0, duration=193.556s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=drop
     cookie=0x0, duration=193.556s, table=0, n_packets=6, n_bytes=276, priority=1,arp actions=CONTROLLER:65535
     cookie=0x6e00000002, duration=127.796s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=110,nw_dst=10.10.10.0/24 actions=CONTROLLER:65535
     cookie=0x200000001, duration=149.878s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=2,nw_dst=172.16.10.0/24 actions=CONTROLLER:65535
     cookie=0x6e00000001, duration=131.326s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=110,nw_dst=172.16.10.0/24 actions=CONTROLLER:65535
     cookie=0x200000002, duration=138.464s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=2,nw_dst=10.10.10.0/24 actions=CONTROLLER:65535
     cookie=0x0, duration=193.556s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL
     cookie=0x6e00000001, duration=131.325s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=110,nw_dst=172.16.10.1 actions=CONTROLLER:65535
     cookie=0x6e00000002, duration=127.795s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=110,nw_dst=10.10.10.1 actions=CONTROLLER:65535
     cookie=0x200000001, duration=149.877s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=2,nw_dst=172.16.10.1 actions=CONTROLLER:65535
     cookie=0x200000002, duration=138.463s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=2,nw_dst=10.10.10.1 actions=CONTROLLER:65535
     cookie=0x200000000, duration=149.879s, table=0, n_packets=0, n_bytes=0, priority=1001,ip,dl_vlan=2 actions=drop
     cookie=0x6e00000000, duration=131.326s, table=0, n_packets=0, n_bytes=0, priority=1001,ip,dl_vlan=110 actions=drop

ルータs1には「172.16.10.1/24」と「10.10.10.1/24」というアドレスを設定し
ました。

下から3～6番めの優先度1037のフローエントリは、「ルータ宛のパケットが到達した
らPacket-Inメッセージを送信する」というものです。

先頭4件の優先度1036のフローエントリは、「同じサブネット内宛のパケットが到達
したら通常のL2スイッチと同じように振る舞う」というものです。

7～10番めに登録されている優先度1002のフローエントリは、
「 :ref:`ch_switching_hub` 」のスイッチングハブと同等の機能です。

末尾2件の優先度1001のフローエントリは「上記条件に合致しないVLANタグつきのパ
ケットは破棄する」というものです。

s2とs3にも、s1と同様に4種類のフローエントリが追加されます。

switch: s2 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s2
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x6e00000001, duration=249.861s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=110,nw_src=192.168.30.0/24,nw_dst=192.168.30.0/24 actions=NORMAL
     cookie=0x200000002, duration=253.507s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=2,nw_src=10.10.10.0/24,nw_dst=10.10.10.0/24 actions=NORMAL
     cookie=0x6e00000002, duration=246.929s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=110,nw_src=10.10.10.0/24,nw_dst=10.10.10.0/24 actions=NORMAL
     cookie=0x200000001, duration=266.336s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=2,nw_src=192.168.30.0/24,nw_dst=192.168.30.0/24 actions=NORMAL
     cookie=0x0, duration=357.916s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=drop
     cookie=0x0, duration=357.916s, table=0, n_packets=8, n_bytes=368, priority=1,arp actions=CONTROLLER:65535
     cookie=0x6e00000002, duration=246.93s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=110,nw_dst=10.10.10.0/24 actions=CONTROLLER:65535
     cookie=0x6e00000001, duration=249.861s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=110,nw_dst=192.168.30.0/24 actions=CONTROLLER:65535
     cookie=0x200000001, duration=266.337s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=2,nw_dst=192.168.30.0/24 actions=CONTROLLER:65535
     cookie=0x200000002, duration=253.507s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=2,nw_dst=10.10.10.0/24 actions=CONTROLLER:65535
     cookie=0x0, duration=357.916s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL
     cookie=0x6e00000002, duration=246.93s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=110,nw_dst=10.10.10.2 actions=CONTROLLER:65535
     cookie=0x200000001, duration=266.337s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=2,nw_dst=192.168.30.1 actions=CONTROLLER:65535
     cookie=0x6e00000001, duration=249.861s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=110,nw_dst=192.168.30.1 actions=CONTROLLER:65535
     cookie=0x200000002, duration=253.507s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=2,nw_dst=10.10.10.2 actions=CONTROLLER:65535
     cookie=0x200000000, duration=266.337s, table=0, n_packets=0, n_bytes=0, priority=1001,ip,dl_vlan=2 actions=drop
     cookie=0x6e00000000, duration=249.862s, table=0, n_packets=0, n_bytes=0, priority=1001,ip,dl_vlan=110 actions=drop

switch: s3 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s3
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x200000002, duration=387.391s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=2,nw_src=10.10.10.0/24,nw_dst=10.10.10.0/24 actions=NORMAL
     cookie=0x6e00000002, duration=380.962s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=110,nw_src=10.10.10.0/24,nw_dst=10.10.10.0/24 actions=NORMAL
     cookie=0x6e00000001, duration=383.831s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=110,nw_src=172.16.20.0/24,nw_dst=172.16.20.0/24 actions=NORMAL
     cookie=0x200000001, duration=402.138s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=2,nw_src=172.16.20.0/24,nw_dst=172.16.20.0/24 actions=NORMAL
     cookie=0x0, duration=551.808s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=drop
     cookie=0x0, duration=551.808s, table=0, n_packets=4, n_bytes=184, priority=1,arp actions=CONTROLLER:65535
     cookie=0x6e00000002, duration=380.963s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=110,nw_dst=10.10.10.0/24 actions=CONTROLLER:65535
     cookie=0x6e00000001, duration=383.831s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=110,nw_dst=172.16.20.0/24 actions=CONTROLLER:65535
     cookie=0x200000001, duration=402.142s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=2,nw_dst=172.16.20.0/24 actions=CONTROLLER:65535
     cookie=0x200000002, duration=387.393s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=2,nw_dst=10.10.10.0/24 actions=CONTROLLER:65535
     cookie=0x0, duration=551.808s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL
     cookie=0x200000001, duration=402.139s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=2,nw_dst=172.16.20.1 actions=CONTROLLER:65535
     cookie=0x6e00000001, duration=383.831s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=110,nw_dst=172.16.20.1 actions=CONTROLLER:65535
     cookie=0x6e00000002, duration=380.962s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=110,nw_dst=10.10.10.3 actions=CONTROLLER:65535
     cookie=0x200000002, duration=387.392s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=2,nw_dst=10.10.10.3 actions=CONTROLLER:65535
     cookie=0x200000000, duration=402.143s, table=0, n_packets=0, n_bytes=0, priority=1001,ip,dl_vlan=2 actions=drop
     cookie=0x6e00000000, duration=383.832s, table=0, n_packets=0, n_bytes=0, priority=1001,ip,dl_vlan=110 actions=drop

この時点でのトポロジは、次のようなものになります。

.. only:: latex

  .. image:: images/rest_router/fig6.eps
     :scale: 80%
     :align: center

.. only:: not latex

  .. image:: images/rest_router/fig6.png
     :scale: 80%
     :align: center

各ルータにIPアドレスが割り当てられたので、各ホストのデフォルトゲートウェイを
登録します。各ホストは隣接するルータに割り当てられたIPアドレスのうち、サブ
ネットが等しいものをデフォルトゲートウェイとして設定します。

host: h1s1:

.. rst-class:: console

::

    root@ryu-vm:~# ip route add default via 172.16.10.1

host: h2s1:

.. rst-class:: console

::

    root@ryu-vm:~# ip route add default via 172.16.10.1

host: h1s2:

.. rst-class:: console

::

    root@ryu-vm:~# ip route add default via 192.168.30.1

host: h2s2:

.. rst-class:: console

::

    root@ryu-vm:~# ip route add default via 192.168.30.1

host: h1s3:

.. rst-class:: console

::

    root@ryu-vm:~# ip route add default via 172.16.20.1

host: h2s3:

.. rst-class:: console

::

    root@ryu-vm:~# ip route add default via 172.16.20.1

この時点でのトポロジは、次のようなものになります。

.. only:: latex

  .. image:: images/rest_router/fig7.eps
     :scale: 80%
     :align: center

.. only:: not latex

  .. image:: images/rest_router/fig7.png
     :scale: 80%
     :align: center


デフォルトルートの設定
^^^^^^^^^^^^^^^^^^^^^^

各ルータにデフォルトルートを設定します。

まず、ルータs1のデフォルトルートとしてルータs2を設定します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"gateway": "10.10.10.2"}' http://localhost:8080/router/0000000000000001/2
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"gateway": "10.10.10.2"}' http://localhost:8080/router/0000000000000001/110
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]

ルータs2のデフォルトルートにはルータs1を設定します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"gateway": "10.10.10.1"}' http://localhost:8080/router/0000000000000002/2
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"gateway": "10.10.10.1"}' http://localhost:8080/router/0000000000000002/110
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]

ルータs3のデフォルトルートにはルータs2を設定します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"gateway": "10.10.10.2"}' http://localhost:8080/router/0000000000000003/2
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"gateway": "10.10.10.2"}' http://localhost:8080/router/0000000000000003/110
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]

この時点での各ルータのフローエントリを詳しく見ていきます。

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x200000002, duration=2639.984s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=2,nw_src=10.10.10.0/24,nw_dst=10.10.10.0/24 actions=NORMAL
     cookie=0x6e00000001, duration=2632.846s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=110,nw_src=172.16.10.0/24,nw_dst=172.16.10.0/24 actions=NORMAL
     cookie=0x200000001, duration=2651.398s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=2,nw_src=172.16.10.0/24,nw_dst=172.16.10.0/24 actions=NORMAL
     cookie=0x6e00000002, duration=2629.316s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=110,nw_src=10.10.10.0/24,nw_dst=10.10.10.0/24 actions=NORMAL
     cookie=0x0, duration=2695.077s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=drop
     cookie=0x0, duration=2695.077s, table=0, n_packets=10, n_bytes=460, priority=1,arp actions=CONTROLLER:65535
     cookie=0x6e00000002, duration=2629.317s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=110,nw_dst=10.10.10.0/24 actions=CONTROLLER:65535
     cookie=0x200000001, duration=2651.399s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=2,nw_dst=172.16.10.0/24 actions=CONTROLLER:65535
     cookie=0x6e00000001, duration=2632.847s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=110,nw_dst=172.16.10.0/24 actions=CONTROLLER:65535
     cookie=0x200000002, duration=2639.985s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=2,nw_dst=10.10.10.0/24 actions=CONTROLLER:65535
     cookie=0x0, duration=2695.077s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL
     cookie=0x6e00000001, duration=2632.846s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=110,nw_dst=172.16.10.1 actions=CONTROLLER:65535
     cookie=0x6e00000002, duration=2629.316s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=110,nw_dst=10.10.10.1 actions=CONTROLLER:65535
     cookie=0x200000001, duration=2651.398s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=2,nw_dst=172.16.10.1 actions=CONTROLLER:65535
     cookie=0x200000002, duration=2639.984s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=2,nw_dst=10.10.10.1 actions=CONTROLLER:65535
     cookie=0x200010000, duration=750.008s, table=0, n_packets=0, n_bytes=0, priority=1001,ip,dl_vlan=2 actions=dec_ttl,set_field:a2:a0:a0:cf:8c:71->eth_src,set_field:f2:c4:23:49:fe:99->eth_dst,output:3
     cookie=0x6e00010000, duration=747.398s, table=0, n_packets=0, n_bytes=0, priority=1001,ip,dl_vlan=110 actions=dec_ttl,set_field:a2:a0:a0:cf:8c:71->eth_src,set_field:f2:c4:23:49:fe:99->eth_dst,output:3

末尾2件の優先度1001のフローエントリが、「上記条件に合致しないVLANタグつきの
パケットは破棄する」という内容から「TTLを減らし、送信元MACをルータs1、
宛先MACをルータs2に書き換え、デフォルトルートに向けて送信する」という内容に
書き換わっています。これは一般的なルータの動作と同様のものです。

s2とs3にも、s1と同様のフローエントリが追加されます。

switch: s2 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s2
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x6e00000001, duration=2968.749s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=110,nw_src=192.168.30.0/24,nw_dst=192.168.30.0/24 actions=NORMAL
     cookie=0x200000002, duration=2972.395s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=2,nw_src=10.10.10.0/24,nw_dst=10.10.10.0/24 actions=NORMAL
     cookie=0x6e00000002, duration=2965.817s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=110,nw_src=10.10.10.0/24,nw_dst=10.10.10.0/24 actions=NORMAL
     cookie=0x200000001, duration=2985.224s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=2,nw_src=192.168.30.0/24,nw_dst=192.168.30.0/24 actions=NORMAL
     cookie=0x0, duration=3076.804s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=drop
     cookie=0x0, duration=3076.804s, table=0, n_packets=14, n_bytes=644, priority=1,arp actions=CONTROLLER:65535
     cookie=0x6e00000002, duration=2965.818s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=110,nw_dst=10.10.10.0/24 actions=CONTROLLER:65535
     cookie=0x6e00000001, duration=2968.749s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=110,nw_dst=192.168.30.0/24 actions=CONTROLLER:65535
     cookie=0x200000001, duration=2985.225s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=2,nw_dst=192.168.30.0/24 actions=CONTROLLER:65535
     cookie=0x200000002, duration=2972.395s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=2,nw_dst=10.10.10.0/24 actions=CONTROLLER:65535
     cookie=0x0, duration=3076.804s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL
     cookie=0x6e00000002, duration=2965.818s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=110,nw_dst=10.10.10.2 actions=CONTROLLER:65535
     cookie=0x6e00000001, duration=2968.749s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=110,nw_dst=192.168.30.1 actions=CONTROLLER:65535
     cookie=0x200000001, duration=2985.225s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=2,nw_dst=192.168.30.1 actions=CONTROLLER:65535
     cookie=0x200000002, duration=2972.395s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=2,nw_dst=10.10.10.2 actions=CONTROLLER:65535
     cookie=0x200010000, duration=828.691s, table=0, n_packets=0, n_bytes=0, priority=1001,ip,dl_vlan=2 actions=dec_ttl,set_field:f2:c4:23:49:fe:99->eth_src,set_field:a2:a0:a0:cf:8c:71->eth_dst,output:3
     cookie=0x6e00010000, duration=826.537s, table=0, n_packets=0, n_bytes=0, priority=1001,ip,dl_vlan=110 actions=dec_ttl,set_field:f2:c4:23:49:fe:99->eth_src,set_field:a2:a0:a0:cf:8c:71->eth_dst,output:3

switch: s3 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s3
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x200000002, duration=3025.871s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=2,nw_src=10.10.10.0/24,nw_dst=10.10.10.0/24 actions=NORMAL
     cookie=0x6e00000002, duration=3019.442s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=110,nw_src=10.10.10.0/24,nw_dst=10.10.10.0/24 actions=NORMAL
     cookie=0x6e00000001, duration=3022.311s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=110,nw_src=172.16.20.0/24,nw_dst=172.16.20.0/24 actions=NORMAL
     cookie=0x200000001, duration=3040.618s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=2,nw_src=172.16.20.0/24,nw_dst=172.16.20.0/24 actions=NORMAL
     cookie=0x0, duration=3190.288s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=drop
     cookie=0x0, duration=3190.288s, table=0, n_packets=8, n_bytes=368, priority=1,arp actions=CONTROLLER:65535
     cookie=0x6e00000002, duration=3019.443s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=110,nw_dst=10.10.10.0/24 actions=CONTROLLER:65535
     cookie=0x6e00000001, duration=3022.311s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=110,nw_dst=172.16.20.0/24 actions=CONTROLLER:65535
     cookie=0x200000001, duration=3040.622s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=2,nw_dst=172.16.20.0/24 actions=CONTROLLER:65535
     cookie=0x200000002, duration=3025.873s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=2,nw_dst=10.10.10.0/24 actions=CONTROLLER:65535
     cookie=0x0, duration=3190.288s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL
     cookie=0x200000001, duration=3040.619s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=2,nw_dst=172.16.20.1 actions=CONTROLLER:65535
     cookie=0x6e00000001, duration=3022.311s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=110,nw_dst=172.16.20.1 actions=CONTROLLER:65535
     cookie=0x6e00000002, duration=3019.442s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=110,nw_dst=10.10.10.3 actions=CONTROLLER:65535
     cookie=0x200000002, duration=3025.872s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=2,nw_dst=10.10.10.3 actions=CONTROLLER:65535
     cookie=0x200010000, duration=686.337s, table=0, n_packets=0, n_bytes=0, priority=1001,ip,dl_vlan=2 actions=dec_ttl,set_field:f2:a5:5c:7f:8d:01->eth_src,set_field:9e:1a:e9:0d:51:a0->eth_dst,output:3
     cookie=0x6e00010000, duration=683.707s, table=0, n_packets=0, n_bytes=0, priority=1001,ip,dl_vlan=110 actions=dec_ttl,set_field:f2:a5:5c:7f:8d:01->eth_src,set_field:9e:1a:e9:0d:51:a0->eth_dst,output:3


静的ルートの設定
^^^^^^^^^^^^^^^^

ルータs2に対し、ルータs3配下のホスト(172.16.20.0/24)へのスタティックルート
を設定します。vlan_id=2の場合のみ設定し、vlan_id=110では設定しません。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"destination": "172.16.20.0/24", "gateway": "10.10.10.3"}' http://localhost:8080/router/0000000000000002/2
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add route [route_id=2]"
            }
          ]
        }
      ]

この時点でのルータs2のフローエントリを確認してみます。

switch: s2 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s2
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x6e00000001, duration=3546.819s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=110,nw_src=192.168.30.0/24,nw_dst=192.168.30.0/24 actions=NORMAL
     cookie=0x200000002, duration=3550.465s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=2,nw_src=10.10.10.0/24,nw_dst=10.10.10.0/24 actions=NORMAL
     cookie=0x6e00000002, duration=3543.887s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=110,nw_src=10.10.10.0/24,nw_dst=10.10.10.0/24 actions=NORMAL
     cookie=0x200000001, duration=3563.294s, table=0, n_packets=0, n_bytes=0, priority=1036,ip,dl_vlan=2,nw_src=192.168.30.0/24,nw_dst=192.168.30.0/24 actions=NORMAL
     cookie=0x0, duration=3654.874s, table=0, n_packets=0, n_bytes=0, priority=1,ip actions=drop
     cookie=0x0, duration=3654.874s, table=0, n_packets=22, n_bytes=1012, priority=1,arp actions=CONTROLLER:65535
     cookie=0x6e00000002, duration=3543.888s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=110,nw_dst=10.10.10.0/24 actions=CONTROLLER:65535
     cookie=0x6e00000001, duration=3546.819s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=110,nw_dst=192.168.30.0/24 actions=CONTROLLER:65535
     cookie=0x200020000, duration=59.814s, table=0, n_packets=0, n_bytes=0, priority=1026,ip,dl_vlan=2,nw_dst=172.16.20.0/24 actions=dec_ttl,set_field:9e:1a:e9:0d:51:a0->eth_src,set_field:f2:a5:5c:7f:8d:01->eth_dst,output:4
     cookie=0x200000001, duration=3563.295s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=2,nw_dst=192.168.30.0/24 actions=CONTROLLER:65535
     cookie=0x200000002, duration=3550.465s, table=0, n_packets=0, n_bytes=0, priority=1002,ip,dl_vlan=2,nw_dst=10.10.10.0/24 actions=CONTROLLER:65535
     cookie=0x0, duration=3654.874s, table=0, n_packets=0, n_bytes=0, priority=0 actions=NORMAL
     cookie=0x6e00000002, duration=3543.888s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=110,nw_dst=10.10.10.2 actions=CONTROLLER:65535
     cookie=0x6e00000001, duration=3546.819s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=110,nw_dst=192.168.30.1 actions=CONTROLLER:65535
     cookie=0x200000001, duration=3563.295s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=2,nw_dst=192.168.30.1 actions=CONTROLLER:65535
     cookie=0x200000002, duration=3550.465s, table=0, n_packets=0, n_bytes=0, priority=1037,ip,dl_vlan=2,nw_dst=10.10.10.2 actions=CONTROLLER:65535
     cookie=0x200010000, duration=1406.761s, table=0, n_packets=0, n_bytes=0, priority=1001,ip,dl_vlan=2 actions=dec_ttl,set_field:f2:c4:23:49:fe:99->eth_src,set_field:a2:a0:a0:cf:8c:71->eth_dst,output:3
     cookie=0x6e00010000, duration=1404.607s, table=0, n_packets=0, n_bytes=0, priority=1001,ip,dl_vlan=110 actions=dec_ttl,set_field:f2:c4:23:49:fe:99->eth_src,set_field:a2:a0:a0:cf:8c:71->eth_dst,output:3

9番めに優先度1026のフローエントリが追加されています。その内容は「宛先IPアド
レスが172.16.20.0/24であれば、送信元MACをルータs2、宛先MACをルータs3に書き
換え、TTLを減らし、ルータs3に向けて送信する」というものです。


設定内容の確認
^^^^^^^^^^^^^

各ルータに設定された内容を確認します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl http://localhost:8080/router/all/all
      [
        {
          "internal_network": [
            {},
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "10.10.10.2"
                }
              ],
              "vlan_id": 2,
              "address": [
                {
                  "address_id": 2,
                  "address": "10.10.10.1/24"
                },
                {
                  "address_id": 1,
                  "address": "172.16.10.1/24"
                }
              ]
            },
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "10.10.10.2"
                }
              ],
              "vlan_id": 110,
              "address": [
                {
                  "address_id": 2,
                  "address": "10.10.10.1/24"
                },
                {
                  "address_id": 1,
                  "address": "172.16.10.1/24"
                }
              ]
            }
          ],
          "switch_id": "0000000000000001"
        },
        {
          "internal_network": [
            {},
            {
              "route": [
                {
                  "route_id": 2,
                  "destination": "172.16.20.0/24",
                  "gateway": "10.10.10.3"
                },
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "10.10.10.1"
                }
              ],
              "vlan_id": 2,
              "address": [
                {
                  "address_id": 2,
                  "address": "10.10.10.2/24"
                },
                {
                  "address_id": 1,
                  "address": "192.168.30.1/24"
                }
              ]
            },
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "10.10.10.1"
                }
              ],
              "vlan_id": 110,
              "address": [
                {
                  "address_id": 2,
                  "address": "10.10.10.2/24"
                },
                {
                  "address_id": 1,
                  "address": "192.168.30.1/24"
                }
              ]
            }
          ],
          "switch_id": "0000000000000002"
        },
        {
          "internal_network": [
            {},
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "10.10.10.2"
                }
              ],
              "vlan_id": 2,
              "address": [
                {
                  "address_id": 1,
                  "address": "172.16.20.1/24"
                },
                {
                  "address_id": 2,
                  "address": "10.10.10.3/24"
                }
              ]
            },
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "10.10.10.2"
                }
              ],
              "vlan_id": 110,
              "address": [
                {
                  "address_id": 1,
                  "address": "172.16.20.1/24"
                },
                {
                  "address_id": 2,
                  "address": "10.10.10.3/24"
                }
              ]
            }
          ],
          "switch_id": "0000000000000003"
        }
      ]

各ルータの設定内容を表にすると、下記のようになります。

.. csv-table:: 設定内容
    :header: "ルータ", "VLAN ID", "IPアドレス", "デフォルトルート", "静的ルート"

    "s1", 2, "172.16.10.1/24, 10.10.10.1/24", "10.10.10.2(s2)"
    "s1", 110, "172.16.10.1/24, 10.10.10.1/24", "10.10.10.2(s2)"
    "s2", 2, "192.168.30.1/24, 10.10.10.2/24", "10.10.10.1(s1)", "宛先:172.16.20.0/24, ゲートウェイ:10.10.10.3(s3)"
    "s2", 110, "192.168.30.1/24, 10.10.10.2/24", "10.10.10.1(s1)"
    "s3", 2, "172.16.20.1/24, 10.10.10.3/24", "10.10.10.2(s2)"
    "s3", 110, "172.16.20.1/24, 10.10.10.3/24", "10.10.10.2(s2)"

h1s1からh1s3に対しpingを送信してみます。同じvlan_id=2のホストであり、
ルータs2にs3宛の静的ルートが設定されているため、疎通が可能です。

host: h1s1:

.. rst-class:: console

::

    root@ryu-vm:~# ping 172.16.20.10
    PING 172.16.20.10 (172.16.20.10) 56(84) bytes of data.
    64 bytes from 172.16.20.10: icmp_req=1 ttl=61 time=45.9 ms
    64 bytes from 172.16.20.10: icmp_req=2 ttl=61 time=0.257 ms
    64 bytes from 172.16.20.10: icmp_req=3 ttl=61 time=0.059 ms
    64 bytes from 172.16.20.10: icmp_req=4 ttl=61 time=0.182 ms

h2s1からh2s3に対しpingを送信してみます。同じvlan_id=110のホストですが、
ルータs2にs3宛の静的ルートが設定されていないため、疎通が不可能です。

host: h2s1:

.. rst-class:: console

::

    root@ryu-vm:~# ping 172.16.20.11
    PING 172.16.20.11 (172.16.20.11) 56(84) bytes of data.
    ^C
    --- 172.16.20.11 ping statistics ---
    8 packets transmitted, 0 received, 100% packet loss, time 7009ms

.. only:: latex

  .. image:: images/rest_router/fig8.eps
     :scale: 80%
     :align: center

.. only:: not latex

  .. image:: images/rest_router/fig8.png
     :scale: 80%
     :align: center


REST API一覧
------------

本章で紹介したrest_routerのREST API一覧です。


登録済み情報の取得
^^^^^^^^^^^^^^^^^^

=============  ========================================
**メソッド**   GET
**URL**        /router/{**switch**}[/{**vlan**}]

               --**switch**: [ "all" \| *スイッチID* ]

               --**vlan**: [ "all" \| *VLAN ID* ]
**備考**        VLAN IDの指定はオプションです。
=============  ========================================


アドレスの設定
^^^^^^^^^^^^^^

=============  ================================================
**メソッド**   POST
**URL**        /router/{**switch**}[/{**vlan**}]

               --**switch**: [ "all" \| *スイッチID* ]

               --**vlan**: [ "all" \| *VLAN ID* ]
**データ**     **address**:"<xxx.xxx.xxx.xxx/xx>"

**備考**       アドレス設定はルート設定前に行ってください。

               VLAN IDの指定はオプションです。
=============  ================================================


固定ルートの設定
^^^^^^^^^^^^^^^^

=============  ================================================
**メソッド**   POST
**URL**        /router/{**switch**}[/{**vlan**}]

               --**switch**: [ "all" \| *スイッチID* ]

               --**vlan**: [ "all" \| *VLAN ID* ]
**データ**     **destination**:"<xxx.xxx.xxx.xxx/xx>"

               **gateway**:"<xxx.xxx.xxx.xxx>"
**備考**        VLAN IDの指定はオプションです。
=============  ================================================


デフォルトルートの設定
^^^^^^^^^^^^^^^^^^^^^^

=============  ================================================
**メソッド**   POST
**URL**        /router/{**switch**}[/{**vlan**}]

               --**switch**: [ "all" \| *スイッチID* ]

               --**vlan**: [ "all" \| *VLAN ID* ]
**データ**     **gateway**:"<xxx.xxx.xxx.xxx>"
**備考**        VLAN IDの指定はオプションです。
=============  ================================================


アドレスの削除
^^^^^^^^^^^^^^

=============  ==========================================
**メソッド**   DELETE
**URL**        /router/{**switch**}[/{**vlan**}]

               --**switch**: [ "all" \| *スイッチID* ]

               --**vlan**: [ "all" \| *VLAN ID* ]
**データ**     **address_id**:[ 1 - ... ]
**備考**        VLAN IDの指定はオプションです。
=============  ==========================================


固定ルート/デフォルトルートの削除
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

=============  ==========================================
**メソッド**   DELETE
**URL**        /router/{**switch**}[/{**vlan**}]

               --**switch**: [ "all" \| *スイッチID* ]

               --**vlan**: [ "all" \| *VLAN ID* ]
**データ**     **route_id**:[ 1 - ... ]
**備考**        VLAN IDの指定はオプションです。
=============  ==========================================
