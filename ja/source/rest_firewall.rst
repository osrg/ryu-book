.. _ch_rest_firewall:

rest_firewall.pyの使用例
========================

本章では、「 :ref:`ch_rest_api` 」を使用して作成され、Ryuのソースツリーに登
録されているryu/app/rest_firewall.pyの使用方法について説明します。


RESTインターフェース
--------------------

RyuはOpenflowスイッチをfirewallとして機能・操作するためのRESTインター
フェースを持っています。rest_firewallを操作するためのコマンドを以下に示しま
す。


全スイッチの有効無効状態の取得
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

=============  ========================
**メソッド**   GET
**URL**        /firewall/module/status
=============  ========================


各スイッチの有効無効状態の変更
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

=============  ================================================
**メソッド**   PUT
**URL**        /firewall/module/{**op**}/{**switch**}

               --**op**: [ "enable" \| "disable" ]

               --**switch**: [ "all" \| *スイッチID* ]
**備考**       各スイッチの初期状態は"disable"になっています。
=============  ================================================


全ルールの取得
^^^^^^^^^^^^^^

=============  ==========================================
**メソッド**   GET
**URL**        /firewall/rules/{**switch**}[/{**vlan**}]

               --**switch**: [ "all" \| *スイッチID* ]

               --**vlan**: [ "all" \| *VLAN ID* ]
**備考**        VLAN IDの指定はオプションです。
=============  ==========================================


新規ルールの追加
^^^^^^^^^^^^^^^^

=============  =========================================================
**メソッド**   POST
**URL**        /firewall/rules/{**switch**}[/{**vlan**}]

               --**switch**: [ "all" \| *スイッチID* ]

               --**vlan**: [ "all" \| *VLAN ID* ]
**データ**     **priority**:[ 0 - 65535 ]

               **in_port**:[ 0 - 65535 ]

               **dl_src**:"<xx:xx:xx:xx:xx:xx>"

               **dl_dst**:"<xx:xx:xx:xx:xx:xx>"

               **dl_type**:[ "ARP" \| "IPv4" ]

               **nw_src**:"<xxx.xxx.xxx.xxx/xx>"

               **nw_dst**:"<xxx.xxx.xxx.xxx/xx">

               **nw_proto**":[ "TCP" \| "UDP" \| "ICMP" ]

               **tp_src**:[ 0 - 65535 ]

               **tp_dst**:[ 0 - 65535 ]

               **actions**: [ "ALLOW" \| "DENY" ]
**備考**       登録に成功するとルールIDが生成され、応答に記載されます。

               VLAN IDの指定はオプションです。
=============  =========================================================


既存ルールの削除
^^^^^^^^^^^^^^^^

=============  ==========================================
**メソッド**   DELETE
**URL**        /firewall/rules/{**switch**}[/{**vlan**}]

               --**switch**: [ "all" \| *スイッチID* ]

               --**vlan**: [ "all" \| *VLAN ID* ]
**データ**     **rule_id**:[ "all" \| 1 - ... ]
**備考**        VLAN IDの指定はオプションです。
=============  ==========================================


全スイッチのログ出力状態の取得
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

=============  ====================
**メソッド**   GET
**URL**        /firewall/log/status
=============  ====================


各スイッチのログ出力状態の変更
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

=============  ===============================================
**メソッド**   PUT
**URL**        /firewall/log/{**op**}/{**switch**}

               --**op**: [ "enable" \| "disable" ]

               --**switch**: [ "all" \| *スイッチID* ]
**備考**       各スイッチの初期状態は"enable"になっています。
=============  ===============================================


シングルテナントでの動作例
--------------------------

ここでは下記のような環境で"switch_id:000000000000001"に対してルールを追加・
削除し、各ホスト間の疎通可否を確認する例を紹介します。

.. only:: latex

  .. image:: images/rest_firewall/fig1.eps
     :scale: 60%
     :align: center

.. only:: not latex

  .. image:: images/rest_firewall/fig1.png
     :scale: 60%
     :align: center


環境構築
^^^^^^^^

まずはmininet上に環境を構築します。

.. rst-class:: console

::

    ryu@ryu-vm:~$ sudo mn --controller remote -x
    *** Creating network
    *** Adding controller
    Unable to contact the remote controller at 127.0.0.1:6633
    *** Adding hosts:
    h1 h2
    *** Adding switches:
    s1
    *** Adding links:
    (h1, s1) (h2, s1)
    *** Configuring hosts
    h1 h2
    *** Running terms on localhost:10.0
    *** Starting controller
    *** Starting 1 switches
    s1

    *** Starting CLI:
    mininet>

また、コントローラ用のxtermをもうひとつ起動しておきます。

.. rst-class:: console

::

    mininet> xterm c0
    mininet>

続いて、各ホストのIPアドレスを変更し、デフォルトゲートウェイを設定します。

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.1/8 dev h1-eth0
    root@ryu-vm:~# ip addr add 172.16.10.10/24 dev h1-eth0
    root@ryu-vm:~# ip route add default via 172.16.10.10

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.2/8 dev h2-eth0
    root@ryu-vm:~# ip addr add 192.168.30.10/24 dev h2-eth0
    root@ryu-vm:~# ip route add default via 192.168.30.10

さらに、使用するOpenFlowのバージョンを1.3に設定します。

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13

.. ATTENTION::

    Ryu3.2に含まれているrest_firewall.pyはOpenFlow1.3以降に対応していませ
    ん。Ryu3.4以降をご利用ください。

最後に、コントローラのxterm上でrest_firewallを起動させます。

controller: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# cd ryu
    root@ryu-vm:~/ryu# ryu-manager ryu/app/rest_firewall.py
    loading app ryu/app/rest_firewall.py
    loading app ryu.controller.ofp_handler
    instantiating app None of DPSet
    creating context dpset
    creating context wsgi
    instantiating app ryu/app/rest_firewall.py of RestFirewallAPI
    instantiating app ryu.controller.ofp_handler of OFPHandler
    (1433) wsgi starting up on http://0.0.0.0:8080/

Ryuとスイッチの間の接続に成功すると、次のメッセージが表示されます。

controller: c0 (root):

.. rst-class:: console

::

    [FW][INFO] switch_id=0000000000000001: Join as firewall


初期状態の確認
^^^^^^^^^^^^^^

firewallの状態を確認します。初期状態は無効(disable)になっています。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl http://localhost:8080/firewall/module/status
      [
        {
          "status": "disable",
          "switch_id": "0000000000000001"
        }
      ]

.. NOTE::

    RESTコマンドの実行結果は見やすいように整形しています。

この時点でのフローエントリは以下のようになっています。最高優先度で破棄が指定
されていることがわかります。

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=3.159s, table=0, n_packets=0, n_bytes=0, priority=65534,arp actions=NORMAL
     cookie=0x0, duration=3.196s, table=0, n_packets=0, n_bytes=0, priority=65535 actions=drop
     cookie=0x0, duration=3.159s, table=0, n_packets=0, n_bytes=0, priority=0 actions=CONTROLLER:0


初期状態の変更
^^^^^^^^^^^^^^

firewallを有効(enable)にします。無効のままだと、ルール追加をしてもすべての
パケットが遮断されます。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X PUT http://localhost:8080/firewall/module/enable/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": {
            "result": "success",
            "details": "firewall running."
          }
        }
      ]

    root@ryu-vm:~# curl http://localhost:8080/firewall/module/status
      [
        {
          "status": "enable",
          "switch_id": "0000000000000001"
        }
      ]

firewallを有効にしたことにより、最高優先度で登録されていた破棄の指示が削除さ
れます。

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=162.958s, table=0, n_packets=0, n_bytes=0, priority=65534,arp actions=NORMAL
     cookie=0x0, duration=162.958s, table=0, n_packets=0, n_bytes=0, priority=0 actions=CONTROLLER:0


ルール追加
^^^^^^^^^^

一例として、IPアドレス 10.0.0.4へのフローを通すルールを追加します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"nw_dst": "10.0.0.4/32"}' http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Rule added. : rule_id=1"
            }
          ]
        }
      ]

追加したルールがフローエントリとしてスイッチに登録されます。

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x1, duration=5.398s, table=0, n_packets=0, n_bytes=0, priority=1,ip,nw_dst=10.0.0.4 actions=NORMAL
     cookie=0x0, duration=517.45s, table=0, n_packets=0, n_bytes=0, priority=65534,arp actions=NORMAL
     cookie=0x0, duration=517.45s, table=0, n_packets=0, n_bytes=0, priority=0 actions=CONTROLLER:0

また、MACアドレス 00:00:00:00:00:01からMACアドレス 00:00:00:00:00:02への
フローを通すルールを追加します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"dl_src": "00:00:00:00:00:01", "dl_dst": "00:00:00:00:00:02"}' http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Rule added. : rule_id=2"
            }
          ]
        }
      ]

追加したルールがフローエントリとしてスイッチに登録されます。

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x2, duration=2.906s, table=0, n_packets=0, n_bytes=0, priority=1,dl_src=00:00:00:00:00:01,dl_dst=00:00:00:00:00:02 actions=NORMAL
     cookie=0x1, duration=103.524s, table=0, n_packets=0, n_bytes=0, priority=1,ip,nw_dst=10.0.0.4 actions=NORMAL
     cookie=0x0, duration=615.576s, table=0, n_packets=0, n_bytes=0, priority=65534,arp actions=NORMAL
     cookie=0x0, duration=615.576s, table=0, n_packets=0, n_bytes=0, priority=0 actions=CONTROLLER:0

さらに、172.16.10.0/24のping(ICMPパケット)を許可するルールを追加します。双
方向にルールを設定をする必要がありますので、ルールをふたつ追加します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"nw_src": "172.16.10.0/24", "nw_proto": "ICMP"}' http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Rule added. : rule_id=3"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"nw_dst": "172.16.10.0/24", "nw_proto": "ICMP"}' http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Rule added. : rule_id=4"
            }
          ]
        }
      ]

追加したルールがフローエントリとしてスイッチに登録されます。

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x2, duration=167.232s, table=0, n_packets=0, n_bytes=0, priority=1,dl_src=00:00:00:00:00:01,dl_dst=00:00:00:00:00:02 actions=NORMAL
     cookie=0x4, duration=5.529s, table=0, n_packets=0, n_bytes=0, priority=1,icmp,nw_dst=172.16.10.0/24 actions=NORMAL
     cookie=0x1, duration=267.85s, table=0, n_packets=0, n_bytes=0, priority=1,ip,nw_dst=10.0.0.4 actions=NORMAL
     cookie=0x0, duration=779.902s, table=0, n_packets=0, n_bytes=0, priority=65534,arp actions=NORMAL
     cookie=0x3, duration=54.709s, table=0, n_packets=0, n_bytes=0, priority=1,icmp,nw_src=172.16.10.0/24 actions=NORMAL
     cookie=0x0, duration=779.902s, table=0, n_packets=0, n_bytes=0, priority=0 actions=CONTROLLER:0


ルール確認
^^^^^^^^^^

設定されているルールを確認します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "access_control_list": [
            {
              "rules": [
                {
                  "priority": 1,
                  "dl_type": "IPv4",
                  "rule_id": 1,
                  "actions": "ALLOW",
                  "nw_dst": "10.0.0.4"
                },
                {
                  "priority": 1,
                  "dl_type": "IPv4",
                  "nw_proto": "ICMP",
                  "nw_src": "172.16.10.0/24",
                  "rule_id": 3,
                  "actions": "ALLOW"
                },
                {
                  "priority": 1,
                  "dl_dst": "00:00:00:00:00:02",
                  "rule_id": 2,
                  "actions": "ALLOW",
                  "dl_src": "00:00:00:00:00:01"
                },
                {
                  "priority": 1,
                  "dl_type": "IPv4",
                  "nw_proto": "ICMP",
                  "nw_dst": "172.16.10.0/24",
                  "rule_id": 4,
                  "actions": "ALLOW"
                }
              ]
            }
          ],
          "switch_id": "0000000000000001"
        }
      ]

実際にpingで確認します。設定したルールにより、pingが疎通できることがわかり
ます。

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ping 192.168.30.10
    PING 192.168.30.10 (192.168.30.10) 56(84) bytes of data.
    64 bytes from 192.168.30.10: icmp_req=1 ttl=64 time=0.865 ms
    64 bytes from 192.168.30.10: icmp_req=2 ttl=64 time=0.111 ms
    64 bytes from 192.168.30.10: icmp_req=3 ttl=64 time=0.082 ms
    64 bytes from 192.168.30.10: icmp_req=4 ttl=64 time=0.043 ms
    ...


ルール削除
^^^^^^^^^^

"rule_id:3"のルールを削除します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X DELETE -d '{"rule_id": "3"}' http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Rule deleted. : ruleID=3"
            }
          ]
        }
      ]

再度ルールを確認します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "access_control_list": [
            {
              "rules": [
                {
                  "priority": 1,
                  "dl_type": "IPv4",
                  "rule_id": 1,
                  "actions": "ALLOW",
                  "nw_dst": "10.0.0.4"
                },
                {
                  "priority": 1,
                  "dl_dst": "00:00:00:00:00:02",
                  "rule_id": 2,
                  "actions": "ALLOW",
                  "dl_src": "00:00:00:00:00:01"
                },
                {
                  "priority": 1,
                  "dl_type": "IPv4",
                  "nw_proto": "ICMP",
                  "nw_dst": "172.16.10.0/24",
                  "rule_id": 4,
                  "actions": "ALLOW"
                }
              ]
            }
          ],
          "switch_id": "0000000000000001"
        }
      ]

フローを確認すると、"rule_id:3"に該当するフローエントリが削除されていること
がわかります。

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x2, duration=170.801s, table=0, n_packets=0, n_bytes=0, priority=1,dl_src=00:00:00:00:00:01,dl_dst=00:00:00:00:00:02 actions=NORMAL
     cookie=0x4, duration=92.269s, table=0, n_packets=4, n_bytes=392, priority=1,icmp,nw_dst=172.16.10.0/24 actions=NORMAL
     cookie=0x1, duration=213.21s, table=0, n_packets=0, n_bytes=0, priority=1,ip,nw_dst=10.0.0.4 actions=NORMAL
     cookie=0x0, duration=304.626s, table=0, n_packets=4, n_bytes=168, priority=65534,arp actions=NORMAL
     cookie=0x0, duration=304.626s, table=0, n_packets=0, n_bytes=0, priority=0 actions=CONTROLLER:0

実際にpingで確認します。172.16.10.0/24を送信元とするICMPパケットを許可する
ルールが削除されたため、pingが疎通できないことがわかります。

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ping 192.168.30.10
    PING 192.168.30.10 (192.168.30.10) 56(84) bytes of data.
    ^C
    --- 192.168.30.10 ping statistics ---
    4 packets transmitted, 0 received, 100% packet loss, time 3000ms

firewallでパケットが遮断されるとログが出力されます。

controller: c0 (root):

.. rst-class:: console

::

    [FW][INFO] dpid=0000000000000001: Blocked packet = ethernet(dst='7e:1a:c0:2f:2b:27',ethertype=2048,src='f2:da:3c:af:56:84'), ipv4(csum=42460,dst='192.168.30.10',flags=2,header_length=5,identification=0,offset=0,option=None,proto=1,src='172.16.10.10',tos=0,total_length=84,ttl=64,version=4), icmp(code=0,csum=25541,data=echo(data='\x85j\xa5R\x00\x00\x00\x00\x9c\xb1\x00\x00\x00\x00\x00\x00\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./01234567',id=3540,seq=37),type=8)
    ...


ログ出力機能の設定変更
^^^^^^^^^^^^^^^^^^^^^^

firewallのログ出力を無効にします。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X PUT http://localhost:8080/firewall/log/disable/0000000000000001
      [
        [
          "command_result", {
            "result": "success",
            "details": "Log collection stopped."
          }
        ]
      ]

    root@ryu-vm:~# curl http://localhost:8080/firewall/log/status
      [
        {
          "log status": "disable",
          "switch_id": "0000000000000001"
        }
      ]

この状態で先ほどと同様にpingを送信し、遮断されることを確認します。

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ping 192.168.30.10
    PING 192.168.30.10 (192.168.30.10) 56(84) bytes of data.
    ^C
    --- 192.168.30.10 ping statistics ---
    4 packets transmitted, 0 received, 100% packet loss, time 3000ms

ログ出力を無効にしたため、パケットを遮断した旨のログが出力されないことがわか
ります。


マルチテナントでの動作例
------------------------

続いて、下記のような環境で"switch_id=000000000000001"に対してルールを追加・
削除し、各ホスト間の疎通可否を確認する例を紹介します。

.. only:: latex

  .. image:: images/rest_firewall/fig2.eps
     :scale: 60%
     :align: center

.. only:: not latex

  .. image:: images/rest_firewall/fig2.png
     :scale: 60%
     :align: center


環境構築
^^^^^^^^

シングルテナントでの例と同様、mininet上に環境を構築し、コントローラ用のxterm
をもうひとつ起動しておきます。

.. rst-class:: console

::

    ryu@ryu-vm:~$ sudo mn --topo single,4 --controller remote -x
    *** Creating network
    *** Adding controller
    Unable to contact the remote controller at 127.0.0.1:6633
    *** Adding hosts:
    h1 h2 h3 h4
    *** Adding switches:
    s1
    *** Adding links:
    (h1, s1) (h2, s1) (h3, s1) (h4, s1)
    *** Configuring hosts
    h1 h2 h3 h4
    *** Running terms on localhost:10.0
    *** Starting controller
    *** Starting 1 switches
    s1

    *** Starting CLI:
    mininet> xterm c0
    mininet>

続いて、各ホストのインターフェースにVLAN IDを設定した上でIPアドレスを変更し、
デフォルトゲートウェイを設定します。

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.1/8 dev h1-eth0
    root@ryu-vm:~# ip link add link h1-eth0 name h1-eth0.2 type vlan id 2
    root@ryu-vm:~# ip addr add 172.16.10.10/24 dev h1-eth0.2
    root@ryu-vm:~# ip link set dev h1-eth0.2 up
    root@ryu-vm:~# ip route add default via 172.16.10.10

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.2/8 dev h2-eth0
    root@ryu-vm:~# ip link add link h2-eth0 name h2-eth0.110 type vlan id 110
    root@ryu-vm:~# ip addr add 172.16.10.11/24 dev h2-eth0.110
    root@ryu-vm:~# ip link set dev h2-eth0.110 up
    root@ryu-vm:~# ip route add default via 172.16.10.11

host: h3:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.3/8 dev h3-eth0
    root@ryu-vm:~# ip link add link h3-eth0 name h3-eth0.2 type vlan id 2
    root@ryu-vm:~# ip addr add 192.168.30.10/24 dev h3-eth0.2
    root@ryu-vm:~# ip link set dev h3-eth0.2 up
    root@ryu-vm:~# ip route add default via 192.168.30.10

host: h4:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.4/8 dev h4-eth0
    root@ryu-vm:~# ip link add link h4-eth0 name h4-eth0.110 type vlan id 110
    root@ryu-vm:~# ip addr add 192.168.30.11/24 dev h4-eth0.110
    root@ryu-vm:~# ip link set dev h4-eth0.110 up
    root@ryu-vm:~# ip route add default via 192.168.30.11

さらに、使用するOpenFlowのバージョンを1.3に設定します。

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13

.. ATTENTION::

    Ryu3.2に含まれているrest_firewall.pyはOpenFlow1.3以降に対応していませ
    ん。Ryu3.4以降をご利用ください。

最後に、コントローラのxterm上でrest_firewallを起動させます。

controller: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# cd ryu
    root@ryu-vm:~/ryu# ryu-manager ryu/app/rest_firewall.py
    loading app ryu/app/rest_firewall.py
    loading app ryu.controller.ofp_handler
    instantiating app None of DPSet
    creating context dpset
    creating context wsgi
    instantiating app ryu/app/rest_firewall.py of RestFirewallAPI
    instantiating app ryu.controller.ofp_handler of OFPHandler
    (13419) wsgi starting up on http://0.0.0.0:8080/

Ryuとスイッチの間の接続に成功すると、次のメッセージが表示されます。

controller: c0 (root):

.. rst-class:: console

::

    [FW][INFO] switch_id=0000000000000001: Join as firewall


初期状態の変更
^^^^^^^^^^^^^^

firewallを有効(enable)にします。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X PUT http://localhost:8080/firewall/module/enable/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": {
            "result": "success",
            "details": "firewall running."
          }
        }
      ]

    root@ryu-vm:~# curl http://localhost:8080/firewall/module/status
      [
        {
          "status": "enable",
          "switch_id": "0000000000000001"
        }
      ]


ルール追加(vlan_id=2)
^^^^^^^^^^^^^^^^^^^^^

vlan_id=2に172.16.10.0/24のping(ICMPパケット)を許可するルールを追加します。
双方向にルールを設定をする必要がありますので、ルールをふたつ追加します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"nw_src": "172.16.10.0/24", "nw_proto": "ICMP"}' http://localhost:8080/firewall/rules/0000000000000001/2
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Rule added. : rule_id=1"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"nw_dst": "172.16.10.0/24", "nw_proto": "ICMP"}' http://localhost:8080/firewall/rules/0000000000000001/2
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Rule added. : rule_id=2"
            }
          ]
        }
      ]


ルール確認(vlan_id=2)
^^^^^^^^^^^^^^^^^^^^^

設定されているルールを確認します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl http://localhost:8080/firewall/rules/0000000000000001/all
      [
        {
          "access_control_list": [
            {
              "rules": [
                {
                  "priority": 1,
                  "dl_type": "IPv4",
                  "nw_proto": "ICMP",
                  "dl_vlan": 2,
                  "nw_src": "172.16.10.0/24",
                  "rule_id": 1,
                  "actions": "ALLOW"
                },
                {
                  "priority": 1,
                  "dl_type": "IPv4",
                  "nw_proto": "ICMP",
                  "nw_dst": "172.16.10.0/24",
                  "dl_vlan": 2,
                  "rule_id": 2,
                  "actions": "ALLOW"
                }
              ],
              "vlan_id": 2
            }
          ],
          "switch_id": "0000000000000001"
        }
      ]

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x200000001, duration=290.515s, table=0, n_packets=0, n_bytes=0, priority=1,icmp,dl_vlan=2,nw_src=172.16.10.0/24 actions=NORMAL
     cookie=0x0, duration=359.367s, table=0, n_packets=0, n_bytes=0, priority=65534,arp actions=NORMAL
     cookie=0x0, duration=359.406s, table=0, n_packets=0, n_bytes=0, priority=65535 actions=drop
     cookie=0x0, duration=359.367s, table=0, n_packets=0, n_bytes=0, priority=0 actions=CONTROLLER:0
     cookie=0x200000002, duration=248.801s, table=0, n_packets=0, n_bytes=0, priority=1,icmp,dl_vlan=2,nw_dst=172.16.10.0/24 actions=NORMAL

実際にpingで確認します。

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ping 192.168.30.10
    PING 192.168.30.10 (192.168.30.10) 56(84) bytes of data.
    64 bytes from 192.168.30.10: icmp_req=1 ttl=64 time=1.22 ms
    64 bytes from 192.168.30.10: icmp_req=2 ttl=64 time=0.029 ms
    64 bytes from 192.168.30.10: icmp_req=3 ttl=64 time=0.049 ms
    64 bytes from 192.168.30.10: icmp_req=4 ttl=64 time=0.052 ms
    ...

ルール追加をしていないので、vlan_id=110のホストではpingが遮断されます。

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# ping 192.168.30.11
    PING 192.168.30.11 (192.168.30.11) 56(84) bytes of data.
    ^C
    --- 192.168.30.11 ping statistics ---
    5 packets transmitted, 0 received, 100% packet loss, time 3999ms

firewallでパケットが遮断されるとログが出力されます。

controller: c0 (root):

.. rst-class:: console

::

    [FW][INFO] dpid=0000000000000001: Blocked packet = ethernet(dst='82:08:38:50:9a:ae',ethertype=33024,src='42:8c:34:85:fa:39'), vlan(cfi=0,ethertype=2048,pcp=0,vid=110), ipv4(csum=31934,dst='192.168.30.11',flags=2,header_length=5,identification=10524,offset=0,option=None,proto=1,src='172.16.10.11',tos=0,total_length=84,ttl=64,version=4), icmp(code=0,csum=49103,data=echo(data='\xd2\x97\xa6R\x00\x00\x00\x00\xbe|\x05\x00\x00\x00\x00\x00\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./01234567',id=15601,seq=5),type=8)
    ...


ルール追加(vlan_id=110)
^^^^^^^^^^^^^^^^^^^^^^^

vlan_id=110に172.16.10.11のwebサーバへの通信を許可するルールを追加します。
双方向にルールを設定をする必要がありますので、ルールをふたつ追加します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"nw_dst": "172.16.10.11", "nw_proto": "TCP", "tp_src": "80"}' http://localhost:8080/firewall/rules/0000000000000001/110
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Rule added. : rule_id=1"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"nw_src": "172.16.10.11", "nw_proto": "TCP", "tp_dst": "80"}' http://localhost:8080/firewall/rules/0000000000000001/110
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Rule added. : rule_id=2"
            }
          ]
        }
      ]

設定されているルールを確認します。

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl http://localhost:8080/firewall/rules/0000000000000001/all
      [
        {
          "access_control_list": [
            {
              "rules": [
                {
                  "priority": 1,
                  "dl_type": "IPv4",
                  "nw_proto": "ICMP",
                  "dl_vlan": 2,
                  "nw_src": "172.16.10.0/24",
                  "rule_id": 1,
                  "actions": "ALLOW"
                },
                {
                  "priority": 1,
                  "dl_type": "IPv4",
                  "nw_proto": "ICMP",
                  "nw_dst": "172.16.10.0/24",
                  "dl_vlan": 2,
                  "rule_id": 2,
                  "actions": "ALLOW"
                }
              ],
              "vlan_id": 2
            },
            {
              "rules": [
                {
                  "priority": 1,
                  "dl_type": "IPv4",
                  "nw_proto": "TCP",
                  "tp_dst": 80,
                  "dl_vlan": 110,
                  "nw_src": "172.16.10.11",
                  "rule_id": 2,
                  "actions": "ALLOW"
                },
                {
                  "priority": 1,
                  "dl_type": "IPv4",
                  "nw_proto": "TCP",
                  "nw_dst": "172.16.10.11",
                  "tp_src": 80,
                  "dl_vlan": 110,
                  "rule_id": 1,
                  "actions": "ALLOW"
                }
              ],
              "vlan_id": 110
            }
          ],
          "switch_id": "0000000000000001"
        }
      ]

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x200000001, duration=723.041s, table=0, n_packets=6, n_bytes=592, priority=1,icmp,dl_vlan=2,nw_src=172.16.10.0/24 actions=NORMAL
     cookie=0x6e00000001, duration=75.669s, table=0, n_packets=0, n_bytes=0, priority=1,tcp,dl_vlan=110,nw_dst=172.16.10.11,tp_src=80 actions=NORMAL
     cookie=0x0, duration=744.927s, table=0, n_packets=6, n_bytes=276, priority=65534,arp actions=NORMAL
     cookie=0x0, duration=744.927s, table=0, n_packets=17, n_bytes=1494, priority=0 actions=CONTROLLER:0
     cookie=0x6e00000002, duration=41.536s, table=0, n_packets=0, n_bytes=0, priority=1,tcp,dl_vlan=110,nw_src=172.16.10.11,tp_dst=80 actions=NORMAL
     cookie=0x200000002, duration=704.397s, table=0, n_packets=6, n_bytes=592, priority=1,icmp,dl_vlan=2,nw_dst=172.16.10.0/24 actions=NORMAL

実際にwgetで確認します。webサーバが起動していないので接続が拒否されますが、
要求自体は正常に疎通できていることがわかります。

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# wget 192.168.30.11
    --2013-12-10 13:31:01--  http://192.168.30.11/
    192.168.30.11:80 に接続しています... 失敗しました: 接続を拒否されました.

ICMPに関するルール追加をしていないので、先ほどと同様vlan_id=110のホストでは
pingが遮断されます。

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# ping 192.168.30.11
    PING 192.168.30.11 (192.168.30.11) 56(84) bytes of data.
    ^C
    --- 192.168.30.11 ping statistics ---
    7 packets transmitted, 0 received, 100% packet loss, time 6046ms

