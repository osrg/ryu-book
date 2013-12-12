.. _ch_spanning_tree:

スパニングツリーの実装
======================

本章では、Ryuを用いたスパニングツリーの実装方法を解説していきます。


スパニングツリー
----------------

スパニングツリーはループ構造を持つネットワークにおけるブロードキャストストーム
の発生を抑制する機能です。また、ループを防止するという本来の機能を応用して、
ネットワーク故障が発生した際に自動的に経路を切り替えるネットワークの
冗長性確保の手段としても用いられます。

スパニングツリーにはSTP、RSTP、PVST+、MSTPなど様々な種別がありますが、
本章では最も基本的なSTPの実装を見ていきます。



STP(spanning tree protocol：IEEE 802.1D)はネットワークを論理的なツリーとして扱い、
各ブリッジのポートをフレーム転送可能または不可能な状態に設定することで、
ループ構造を持つネットワークにおけるブロードキャストストームの発生を抑制します。

.. only:: latex

   +------------------------------------------+------------------------------------------+
   | #TODO: image1.eps                        |  #TODO: image2.eps                       |
   |                                          |                                          |
   |  ループを持つネットワーク                |   ループを回避したネットワーク           |
   +------------------------------------------+------------------------------------------+

.. only:: not latex

   +------------------------------------------+------------------------------------------+
   | #TODO: image1.png                        |  #TODO: image2.png                       |
   |                                          |                                          |
   |  ループを持つネットワーク                |   ループを回避したネットワーク           |
   +------------------------------------------+------------------------------------------+


STPではブリッジ間でBPDU(Bridge Protocol Data Unit)パケットを相互に交換
しブリッジや各ポートの情報を比較することで、論理ツリーの頂点である
ルートブリッジを決定し、さらに各ブリッジのポートのフレーム転送可否を決定します。

具体的には、次のような手順により実現されます。

1. ルートブリッジの選出

    ブリッジ間のBPDUパケットの交換により、最小のブリッジIDを持つブリッジが
    ルートブリッジとして選出され、以降はルートブリッジのみがオリジナルの
    BPDUパケットを送信し、他のブリッジはルートブリッジから受信したBPDUパケット
    を転送します。

    .. NOTE::

        ブリッジIDは、各ブリッジに設定されたブリッジ優先度
        (デフォルト0x8000：RyuのSTPライブラリではコンフィグ設定が可能)と
        特定ポートのMACアドレスの組み合わせで算出されます。

            ブリッジID

            ============== ===========
            上位2byte      下位6byte
            ============== ===========
            ブリッジ優先度 MACアドレス
            ============== ===========



2. ポートの役割の決定

    各ポートのルートブリッジに至るまでのコストを元に、ポートの役割を決定します。

    * ルートポート(Root port)：
        ブリッジ内で最もルートブリッジまでのコストが小さいポート。
        ルートブリッジからのBPDUパケットを受信するポートになります。

    * 指定ポート(Designated port)：
        各リンクのルートブリッジまでのコストが小さい側のポート。
        ルートブリッジから受信したBPDUパケットを送信するポートになります。
        ルートブリッジのポートは全て指定ポートです。

    * 非指定ポート(Non designated port)：
        ルートポート・指定ポート以外のポート。
        フレーム転送を抑制するポートです。


    .. only:: latex

        +------------------------------------------+
        | #TODO: image3.eps                        |
        |                                          |
        |  各ポートの役割                          |
        +------------------------------------------+

    .. only:: not latex

        +------------------------------------------+
        | #TODO: image3.png                        |
        |                                          |
        |  各ポートの役割                          |
        +------------------------------------------+


    .. NOTE::

        ルートブリッジに至るまでのコストは次のように算出されます。
        #TODO:


3. ポートの状態遷移

    ポート役割の決定後、各ポートはLISTEN状態になります。その後、以下に示す
    状態遷移を行い、最終的に各ポートの役割に従ってFORWARD状態または
    BLOCK状態に遷移します。

    .. only:: latex

        +------------------------------------------+
        | #TODO: image4.eps                        |
        |                                          |
        |  ポート状態遷移                          |
        +------------------------------------------+

    .. only:: not latex

        +------------------------------------------+
        | #TODO: image4.png                        |
        |                                          |
        |  ポート状態遷移                          |
        +------------------------------------------+

    
    コンフィグで無効ポートと設定されたポートはDISABLE状態となり、
    以降、状態遷移は行われません。

    ======= ===========================================
    状態    動作
    ======= ===========================================
    DISABLE 無効ポート。全ての受信パケットを無視します。
    BLOCK   BPDU受信のみ を行います。
    LISTEN  BPDU送受信 を行います。
    LEARN   BPDU送受信/MAC学習 を行います。
    FORWARD BPDU送受信/MAC学習/フレーム転送 を行います。
    ======= ===========================================


これらの動作が各ブリッジで実行されることにより、フレーム転送を行うポートと
フレーム転送を抑制するポートが決定され、ネットワーク内のループが解消されます。

また、リンクダウンやBPDUパケットのmax age(デフォルト20秒)間の未受信
による故障検出、あるいはポートの追加等によりネットワークトポロジの変更を
検出した場合は、各ブリッジで上記の 1. 2. 3. を実行しツリーの再構築が
行われます(STPの再計算)。



Ryuアプリケーションの実行
-------------------------

Ryuのスパニングツリーアプリケーションを実行してみます。

Ryuのソースツリーに用意されているsimple_switch_stp.pyはOpenFlow 1.0専用
のアプリケーションであるため、ここでは新たにOpenFlow 1.3に対応した
simple_switch_stp_13.pyを作成することとします。このプログラムは、
「 :ref:`ch_switching_hub` 」のスイッチングハブにスパニングツリー機能を
追加したアプリケーションです。


ソース名： ``simple_switch_stp_13.py``

.. rst-class:: sourcecode

.. literalinclude:: sources/simple_switch_stp_13.py





実験環境の構築
^^^^^^^^^^^^^^

スパニングツリーアプリケーションの動作確認を行う実験環境を構築します。

VMイメージ利用のための環境設定やログイン方法等は「 :ref:`ch_switching_hub` 」
を参照してください。

ループ構造を持つ特殊なトポロジで動作させるため、「 :ref:`ch_link_aggregation` 」
と同様にトポロジ構築スクリプトによりmininet環境を構築します。


ソース名： ``spanning_tree.py``

.. rst-class:: sourcecode

.. literalinclude:: sources/spanning_tree.py


VM環境でこのプログラムを実行することにより、スイッチs1、s2、s3の間でループが
存在するトポロジが作成されます。netコマンドの実行結果は以下の通りです。


.. rst-class:: console

::

    ryu@ryu-vm:~$ sudo ./spanning_tree.py 
    Unable to contact the remote controller at 127.0.0.1:6633
    mininet> net
    c0
    s1 lo:  s1-eth1:h1-eth0 s1-eth2:s2-eth2 s1-eth3:s3-eth3
    s2 lo:  s2-eth1:h2-eth0 s2-eth2:s1-eth2 s2-eth3:s3-eth2
    s3 lo:  s3-eth1:h3-eth0 s3-eth2:s2-eth3 s3-eth3:s1-eth3
    h1 h1-eth0:s1-eth1
    h2 h2-eth0:s2-eth1
    h3 h3-eth0:s3-eth1


OpenFlowバージョンの設定
^^^^^^^^^^^^^^^^^^^^^^^^

使用するOpenFlowのバージョンを1.3に設定します。
このコマンド入力は、スイッチs1、s2、s3のxterm上で行ってください。


Node: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13


Node: s2:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s2 protocols=OpenFlow13


Node: s3:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s3 protocols=OpenFlow13




スイッチングハブの実行
^^^^^^^^^^^^^^^^^^^^^^

準備が整ったので、Ryuアプリケーションを実行します。ウインドウタイトルが
「Node: c0 (root)」となっている xterm から次のコマンドを実行します。


Node: c0:

.. rst-class:: console

::

    root@ryu-vm:~$ ryu-manager ./simple_switch_stp_13.py 
    loading app simple_switch_stp_13.py
    loading app ryu.controller.ofp_handler
    loading app ryu.controller.ofp_handler
    instantiating app None of Stp
    creating context stplib
    instantiating app simple_switch_stp_13.py of SimpleSwitch13
    instantiating app ryu.controller.ofp_handler of OFPHandler


OpenFlowスイッチ起動時のSTP計算
"""""""""""""""""""""""""""""""

各OpenFlowスイッチとコントローラの接続が完了すると、BPDUパケットの交換が
始まり、ルートブリッジの選出・ポート役割の設定・ポート状態遷移が行われます。
この結果、最終的に各ポートはFORWARD状態またはBLOCK状態となります。


.. rst-class:: console

::

    [STP][INFO] dpid=0000000000000001: Join as stp bridge.
    [STP][INFO] dpid=0000000000000001: [port=1] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000001: [port=2] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000001: [port=3] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000002: Join as stp bridge.
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000002: [port=2] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000002: [port=3] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000001: [port=2] Receive superior BPDU.
    [STP][INFO] dpid=0000000000000001: [port=1] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000001: [port=2] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000001: [port=3] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000001: Root bridge.
    [STP][INFO] dpid=0000000000000001: [port=1] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000001: [port=2] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000001: [port=3] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000002: [port=2] Receive superior BPDU.
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000002: [port=2] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000002: [port=3] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000002: Non root bridge.
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000002: [port=2] ROOT_PORT           / LISTEN
    [STP][INFO] dpid=0000000000000002: [port=3] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000003: Join as stp bridge.
    [STP][INFO] dpid=0000000000000003: [port=1] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000003: [port=2] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000003: [port=3] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000002: [port=3] Receive superior BPDU.
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000002: [port=2] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000002: [port=3] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000002: Non root bridge.
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000002: [port=2] ROOT_PORT           / LISTEN
    [STP][INFO] dpid=0000000000000002: [port=3] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000001: [port=3] Receive superior BPDU.
    [STP][INFO] dpid=0000000000000001: [port=1] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000001: [port=2] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000001: [port=3] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000001: Root bridge.
    [STP][INFO] dpid=0000000000000001: [port=1] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000001: [port=2] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000001: [port=3] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000003: [port=2] Receive superior BPDU.
    [STP][INFO] dpid=0000000000000003: [port=1] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000003: [port=2] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000003: [port=3] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000003: Non root bridge.
    [STP][INFO] dpid=0000000000000003: [port=1] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000003: [port=2] ROOT_PORT           / LISTEN
    [STP][INFO] dpid=0000000000000003: [port=3] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000003: [port=3] Receive superior BPDU.
    [STP][INFO] dpid=0000000000000003: [port=1] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000003: [port=2] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000003: [port=3] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000003: Non root bridge.
    [STP][INFO] dpid=0000000000000003: [port=1] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000003: [port=2] NON_DESIGNATED_PORT / LISTEN
    [STP][INFO] dpid=0000000000000003: [port=3] ROOT_PORT           / LISTEN
    [STP][INFO] dpid=0000000000000001: [port=3] Receive superior BPDU.
    [STP][INFO] dpid=0000000000000001: [port=1] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000001: [port=2] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000001: [port=3] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000001: Root bridge.
    [STP][INFO] dpid=0000000000000001: [port=1] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000001: [port=2] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000001: [port=3] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / LEARN
    [STP][INFO] dpid=0000000000000002: [port=2] ROOT_PORT           / LEARN
    [STP][INFO] dpid=0000000000000002: [port=3] DESIGNATED_PORT     / LEARN
    [STP][INFO] dpid=0000000000000003: [port=1] DESIGNATED_PORT     / LEARN
    [STP][INFO] dpid=0000000000000003: [port=2] NON_DESIGNATED_PORT / LEARN
    [STP][INFO] dpid=0000000000000003: [port=3] ROOT_PORT           / LEARN
    [STP][INFO] dpid=0000000000000001: [port=1] DESIGNATED_PORT     / LEARN
    [STP][INFO] dpid=0000000000000001: [port=2] DESIGNATED_PORT     / LEARN
    [STP][INFO] dpid=0000000000000001: [port=3] DESIGNATED_PORT     / LEARN
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / FORWARD
    [STP][INFO] dpid=0000000000000002: [port=2] ROOT_PORT           / FORWARD
    [STP][INFO] dpid=0000000000000002: [port=3] DESIGNATED_PORT     / FORWARD
    [STP][INFO] dpid=0000000000000003: [port=1] DESIGNATED_PORT     / FORWARD
    [STP][INFO] dpid=0000000000000003: [port=2] NON_DESIGNATED_PORT / BLOCK
    [STP][INFO] dpid=0000000000000003: [port=3] ROOT_PORT           / FORWARD
    [STP][INFO] dpid=0000000000000001: [port=1] DESIGNATED_PORT     / FORWARD
    [STP][INFO] dpid=0000000000000001: [port=2] DESIGNATED_PORT     / FORWARD
    [STP][INFO] dpid=0000000000000001: [port=3] DESIGNATED_PORT     / FORWARD


パケットがループしないことを確認するため、ホスト1からホスト2へpingを実行します。

pingコマンドを実行する前に、各スイッチでパケットがループしていないことを
確認できるようにtcpdumpコマンドを実行しておきます。



Node: s1:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -i s1-eth2 arp


Node: s2:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -i s2-eth2 arp


Node: s3:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -i s3-eth2 arp


トポロジ構築スクリプトを実行したコンソールで、次のコマンドを実行して
ホスト1からホスト2へpingを発行します。


.. rst-class:: console

::

    mininet> h1 ping h2
    PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
    64 bytes from 10.0.0.2: icmp_req=1 ttl=64 time=84.4 ms
    64 bytes from 10.0.0.2: icmp_req=2 ttl=64 time=0.657 ms
    64 bytes from 10.0.0.2: icmp_req=3 ttl=64 time=0.074 ms
    64 bytes from 10.0.0.2: icmp_req=4 ttl=64 time=0.076 ms
    64 bytes from 10.0.0.2: icmp_req=5 ttl=64 time=0.054 ms
    64 bytes from 10.0.0.2: icmp_req=6 ttl=64 time=0.053 ms
    64 bytes from 10.0.0.2: icmp_req=7 ttl=64 time=0.041 ms
    64 bytes from 10.0.0.2: icmp_req=8 ttl=64 time=0.049 ms
    64 bytes from 10.0.0.2: icmp_req=9 ttl=64 time=0.074 ms
    64 bytes from 10.0.0.2: icmp_req=10 ttl=64 time=0.073 ms
    64 bytes from 10.0.0.2: icmp_req=11 ttl=64 time=0.068 ms
    ^C
    --- 10.0.0.2 ping statistics ---
    11 packets transmitted, 11 received, 0% packet loss, time 9998ms
    rtt min/avg/max/mdev = 0.041/7.784/84.407/24.230 ms


各スイッチで実行したtcpdumpの出力結果から、ARPがループしていないことが
確認できます。


Node: s1:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -i s1-eth2 arp
    tcpdump: WARNING: s1-eth2: no IPv4 address assigned
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on s1-eth2, link-type EN10MB (Ethernet), capture size 65535 bytes
    11:30:24.692797 ARP, Request who-has 10.0.0.2 tell 10.0.0.1, length 28
    11:30:24.749153 ARP, Reply 10.0.0.2 is-at 82:c9:d7:e9:b7:52 (oui Unknown), length 28
    11:30:29.797665 ARP, Request who-has 10.0.0.1 tell 10.0.0.2, length 28
    11:30:29.798250 ARP, Reply 10.0.0.1 is-at c2:a4:54:83:43:fa (oui Unknown), length 28




Node: s2:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -i s2-eth2 arp
    tcpdump: WARNING: s2-eth2: no IPv4 address assigned
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on s2-eth2, link-type EN10MB (Ethernet), capture size 65535 bytes
    11:30:24.692824 ARP, Request who-has 10.0.0.2 tell 10.0.0.1, length 28
    11:30:24.749116 ARP, Reply 10.0.0.2 is-at 82:c9:d7:e9:b7:52 (oui Unknown), length 28
    11:30:29.797659 ARP, Request who-has 10.0.0.1 tell 10.0.0.2, length 28
    11:30:29.798254 ARP, Reply 10.0.0.1 is-at c2:a4:54:83:43:fa (oui Unknown), length 28


Node: s3:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -i s3-eth2 arp
    tcpdump: WARNING: s3-eth2: no IPv4 address assigned
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on s3-eth2, link-type EN10MB (Ethernet), capture size 65535 bytes
    11:30:24.698477 ARP, Request who-has 10.0.0.2 tell 10.0.0.1, length 28



故障検出時のSTP再計算
"""""""""""""""""""""

次に、リンクダウンが起こった際のSTP再計算の動作を確認します。
各OpenFlowスイッチ起動後のSTP計算が完了した状態で次のコマンドを実行し、
ポートをダウンさせます。


Node: s2:

.. rst-class:: console

::

    root@ryu-vm:~# ifconfig s2-eth2 down



リンクダウンを検出しSTP再計算が行われ、これまでBLOCK状態だった
dpid=0000000000000003のport2がFORWARD状態となり、再びフレーム転送可能な状態
となったことが確認できます。


.. rst-class:: console

::

    [STP][INFO] dpid=0000000000000002: [port=2] Link down.
    [STP][INFO] dpid=0000000000000002: [port=2] DESIGNATED_PORT     / DISABLE
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000002: [port=3] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000002: Root bridge.
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000002: [port=3] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000001: [port=2] Link down.
    [STP][INFO] dpid=0000000000000001: [port=2] DESIGNATED_PORT     / DISABLE
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / LEARN
    [STP][INFO] dpid=0000000000000002: [port=3] DESIGNATED_PORT     / LEARN
    [STP][INFO] dpid=0000000000000003: [port=2] Wait BPDU timer is exceeded.
    [STP][INFO] dpid=0000000000000003: [port=1] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000003: [port=2] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000003: [port=3] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000003: Root bridge.
    [STP][INFO] dpid=0000000000000003: [port=1] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000003: [port=2] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000003: [port=3] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000003: [port=3] Receive superior BPDU.
    [STP][INFO] dpid=0000000000000003: [port=1] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000003: [port=2] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000003: [port=3] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000003: Non root bridge.
    [STP][INFO] dpid=0000000000000003: [port=1] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000003: [port=2] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000003: [port=3] ROOT_PORT           / LISTEN
    [STP][INFO] dpid=0000000000000002: [port=3] Receive superior BPDU.
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000002: [port=3] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000002: Non root bridge.
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000002: [port=3] ROOT_PORT           / LISTEN
    [STP][INFO] dpid=0000000000000003: [port=1] DESIGNATED_PORT     / LEARN
    [STP][INFO] dpid=0000000000000003: [port=2] DESIGNATED_PORT     / LEARN
    [STP][INFO] dpid=0000000000000003: [port=3] ROOT_PORT           / LEARN
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / LEARN
    [STP][INFO] dpid=0000000000000002: [port=3] ROOT_PORT           / LEARN
    [STP][INFO] dpid=0000000000000003: [port=1] DESIGNATED_PORT     / FORWARD
    [STP][INFO] dpid=0000000000000003: [port=2] DESIGNATED_PORT     / FORWARD
    [STP][INFO] dpid=0000000000000003: [port=3] ROOT_PORT           / FORWARD
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / FORWARD
    [STP][INFO] dpid=0000000000000002: [port=3] ROOT_PORT           / FORWARD



故障回復時のSTP再計算
"""""""""""""""""""""

続けて、リンクダウンが回復した際のSTP再計算の動作を確認します。
リンクダウン中の状態で次のコマンドを実行し、ポートを起動させます。


Node: s2:

.. rst-class:: console

::

    root@ryu-vm:~# ifconfig s2-eth2 up



リンク復旧を検出しSTP再計算が行われOpenFlowスイッチの初回起動時と同様の
ツリー構成となり、再びフレーム転送可能な状態となったことが確認できます。


.. rst-class:: console

::

    [STP][INFO] dpid=0000000000000002: [port=2] Link down.
    [STP][INFO] dpid=0000000000000002: [port=2] DESIGNATED_PORT     / DISABLE
    [STP][INFO] dpid=0000000000000002: [port=2] Link up.
    [STP][INFO] dpid=0000000000000002: [port=2] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000001: [port=2] Link up.
    [STP][INFO] dpid=0000000000000001: [port=2] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000001: [port=2] Receive superior BPDU.
    [STP][INFO] dpid=0000000000000001: [port=1] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000001: [port=2] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000001: [port=3] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000001: Root bridge.
    [STP][INFO] dpid=0000000000000001: [port=1] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000001: [port=2] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000001: [port=3] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000002: [port=2] Receive superior BPDU.
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000002: [port=2] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000002: [port=3] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000002: Non root bridge.
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000002: [port=2] ROOT_PORT           / LISTEN
    [STP][INFO] dpid=0000000000000002: [port=3] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000003: [port=2] Receive superior BPDU.
    [STP][INFO] dpid=0000000000000003: [port=1] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000003: [port=2] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000003: [port=3] DESIGNATED_PORT     / BLOCK
    [STP][INFO] dpid=0000000000000003: Non root bridge.
    [STP][INFO] dpid=0000000000000003: [port=1] DESIGNATED_PORT     / LISTEN
    [STP][INFO] dpid=0000000000000003: [port=2] NON_DESIGNATED_PORT / LISTEN
    [STP][INFO] dpid=0000000000000003: [port=3] ROOT_PORT           / LISTEN
    [STP][INFO] dpid=0000000000000001: [port=1] DESIGNATED_PORT     / LEARN
    [STP][INFO] dpid=0000000000000001: [port=2] DESIGNATED_PORT     / LEARN
    [STP][INFO] dpid=0000000000000001: [port=3] DESIGNATED_PORT     / LEARN
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / LEARN
    [STP][INFO] dpid=0000000000000002: [port=2] ROOT_PORT           / LEARN
    [STP][INFO] dpid=0000000000000002: [port=3] DESIGNATED_PORT     / LEARN
    [STP][INFO] dpid=0000000000000003: [port=1] DESIGNATED_PORT     / LEARN
    [STP][INFO] dpid=0000000000000003: [port=2] NON_DESIGNATED_PORT / LEARN
    [STP][INFO] dpid=0000000000000003: [port=3] ROOT_PORT           / LEARN
    [STP][INFO] dpid=0000000000000001: [port=1] DESIGNATED_PORT     / FORWARD
    [STP][INFO] dpid=0000000000000001: [port=2] DESIGNATED_PORT     / FORWARD
    [STP][INFO] dpid=0000000000000001: [port=3] DESIGNATED_PORT     / FORWARD
    [STP][INFO] dpid=0000000000000002: [port=1] DESIGNATED_PORT     / FORWARD
    [STP][INFO] dpid=0000000000000002: [port=2] ROOT_PORT           / FORWARD
    [STP][INFO] dpid=0000000000000002: [port=3] DESIGNATED_PORT     / FORWARD
    [STP][INFO] dpid=0000000000000003: [port=1] DESIGNATED_PORT     / FORWARD
    [STP][INFO] dpid=0000000000000003: [port=2] NON_DESIGNATED_PORT / BLOCK
    [STP][INFO] dpid=0000000000000003: [port=3] ROOT_PORT           / FORWARD




OpenFlowによるスパニングツリー
------------------------------

Ryuのスパニングツリーアプリケーションにおいて、OpenFlowを用いてどのように
スパニングツリーの機能を実現しているかを見ていきます。

OpenFlow 1.3には次のようなポートの動作を設定するコンフィグが用意されているため、
各ポートの状態に応じてPort ModificationメッセージをOpenFlowスイッチに発行
することで、ポートのフレーム転送有無などの動作を制御することができます。

================== =========================================================
値                 説明
================== =========================================================
OFPPC_PORT_DOWN    保守者により無効設定された状態です
OFPPC_NO_RECV      当該ポートで受信した全てのパケットを廃棄します
OFPPC_NO_FWD       当該ポートからパケット転送を行いません
OFPPC_NO_PACKET_IN table-missとなった場合にPacket-Inメッセージを送信しません
================== =========================================================


また、ポート状態ごとのBPDUパケット受信とBPDU以外のパケット受信を制御するため、
BPDUパケットをPacket-InするフローエントリとBPDU以外のパケットをdropする
フローエントリをそれぞれFlow ModメッセージによりOpenFlowスイッチに登録します。


コントローラは各OpenFlowスイッチに対して、下記のようにポートコンフィグ設定と
フローエントリ設定を行うことで、ポート状態に応じたBPDUパケットの送受信や
MACアドレス学習(BPDU以外のパケット受信)、フレーム転送(BPDU以外のパケット送信)
の制御を行います。

======= ==========================================================================
状態    設定
======= ==========================================================================
DISABLE ポートコンフィグ(NO_RECV/ NO_FWD)、フローエントリ(設定無し)
BLOCK   ポートコンフィグ(NO_FWD)、フローエントリ(BPDU Packet-In/ BPDU以外drop)
LISTEN  ポートコンフィグ(設定無し)、フローエントリ(BPDU Packet-In/ BPDU以外drop)
LEARN   ポートコンフィグ(設定無し)、フローエントリ(BPDU Packet-In/ BPDU以外drop)
FORWARD ポートコンフィグ(設定無し)、フローエントリ(BPDU Packet-In)
======= ==========================================================================

.. NOTE::

    Ryuに実装されているスパニングツリーのライブラリは、簡略化のため
    LEARN状態でのMACアドレス学習(BPDU以外のパケット受信)を行っていません。


これらの設定に加え、コントローラはOpenFlowスイッチとの接続時に収集した
ポート情報や各OpenFlowスイッチが受信したBPDUパケットに設定されたルートブリッジ
の情報を元に送信用のBPDUパケットを構築しPacket-Outメッセージを発行することで、
OpenFlowスイッチ間のBPDUパケットの交換を実現します。



Ryuによるスパニングツリーの実装
-------------------------------

続いて、Ryuを用いて実装されたスパニングツリーのソースコードを見ていきます。
スパニングツリーのソースコードは、Ryuのソースツリーにあります。

    ryu/lib/stplib.py

    ryu/app/simple_switch_stp.py


stplib.pyはBPDUパケットの交換や各ポートの役割・状態の管理などの
スパニングツリー機能を提供するライブラリです。
simple_switch_stp.pyはスパニングツリーライブラリを適用することで
スイッチングハブのアプリケーションにスパニングツリー機能を追加した
アプリケーションプログラムです。

.. ATTENTION::

    前述の通り、simple_switch_stp.pyはOpenFlow 1.0専用のアプリケーション
    であるため、本章では「 `Ryuアプリケーションの実行`_ 」に示した
    OpenFlow 1.3に対応したsimple_switch_stp_13.pyを元にアプリケーションの
    詳細を説明します。



ライブラリの実装
^^^^^^^^^^^^^^^^

ライブラリ概要
""""""""""""""

.. only:: latex

    +------------------------------------------+
    | #TODO: image5.eps                        |
    |                                          |
    |  ライブラリ概要                          |
    +------------------------------------------+

.. only:: not latex

    +------------------------------------------+
    | #TODO: image5.png                        |
    |                                          |
    |  ライブラリ概要                          |
    +------------------------------------------+


STPライブラリ(Stpクラスオブジェクト)がOpenFlowスイッチのコントローラへの接続を
検出すると、Bridgeクラスオブジェクト・Portクラスオブジェクトが生成されます。
各クラスオブジェクトが生成・起動された後は、Stpクラスオブジェクトからの
OpenFlowメッセージ受信通知、BridgeクラスオブジェクトのSTP計算
(ルートブリッジ選択・各ポートの役割選択)、Portクラスオブジェクトの
ポート状態遷移・BPDUパケット送受信が連動し、スパニングツリー機能を実現します。



コンフィグ設定項目
""""""""""""""""""

STPライブラリはStp.set_config()メソッドによりブリッジ・ポートの
コンフィグ設定IFを提供します。設定可能な項目は以下の通りです。


* bridge

    ========== =================================================== ============
    項目       説明                                                デフォルト値
    ========== =================================================== ============
    priority   ブリッジ優先度                                      0x8000
    sys_ext_id VLAN-IDを設定 (*現状のSTPライブラリはVLAN未対応)    0
    max_age    BPDUパケットの受信待ちタイマー値                    20[sec]
    hello_time BPDUパケットの送信間隔                              2 [sec]
    fwd_delay  各ポートがLISTEN状態およびLEARN状態に留まる時間     15[sec]
    ========== =================================================== ============


* port

    ========= ==================== ============================
    項目      説明                 デフォルト値
    ========= ==================== ============================
    priority  ポート優先度         0x80
    path_cost リンクのコスト値     リンクスピードを元に自動設定
    enable    ポートの有効無効設定 True
    ========= ==================== ============================



BPDUパケット送信
""""""""""""""""

BPDUパケット送信はPortクラスのBPDUパケット送信スレッド(Port.send_bpdu_thread)
で行っています。ポート状態がLISTENとなった際にスレッド処理が開始され、
ポート役割がDESIGNATED_PORTの場合にのみ、ルートブリッジから通知された
hello time(Port.port_times.hello_time：デフォルト2秒)間隔で
BPDUパケットの生成(Port._generate_config_bpdu())およびBPDUパケット送信
(Port.ofctl.send_packet_out())を行います。


.. rst-class:: sourcecode

::

    class Port(object):

        def __init__(self, dp, logger, config, send_ev_func, timeout_func,
                     topology_change_func, bridge_id, bridge_times, ofport):
            super(Port, self).__init__()

            # ...

            # BPDU handling threads
            self.send_bpdu_thread = PortThread(self._transmit_bpdu)

        # ...

        def _transmit_bpdu(self):
            while True:
                # Send config BPDU packet if port role is DESIGNATED_PORT.
                if self.role == DESIGNATED_PORT:
                
                    # ...
                
                    bpdu_data = self._generate_config_bpdu(flags)
                    self.ofctl.send_packet_out(self.ofport.port_no, bpdu_data)
                    
                    # ...

                hub.sleep(self.port_times.hello_time)


送信するBPDUパケットは、OpenFlowスイッチのコントローラ接続時に収集した
ポート情報(Port.ofport)や受信したBPDUパケットに設定された
ルートブリッジ情報(Port.port_priority、Port.port_times)などを元に構築されます。


.. rst-class:: sourcecode

::

    class Port(object):

        def _generate_config_bpdu(self, flags):
            src_mac = self.ofport.hw_addr
            dst_mac = bpdu.BRIDGE_GROUP_ADDRESS
            length = (bpdu.bpdu._PACK_LEN + bpdu.ConfigurationBPDUs.PACK_LEN
                      + llc.llc._PACK_LEN + llc.ControlFormatU._PACK_LEN)

            e = ethernet.ethernet(dst_mac, src_mac, length)
            l = llc.llc(llc.SAP_BPDU, llc.SAP_BPDU, llc.ControlFormatU())
            b = bpdu.ConfigurationBPDUs(
                flags=flags,
                root_priority=self.port_priority.root_id.priority,
                root_mac_address=self.port_priority.root_id.mac_addr,
                root_path_cost=self.port_priority.root_path_cost+self.path_cost,
                bridge_priority=self.bridge_id.priority,
                bridge_mac_address=self.bridge_id.mac_addr,
                port_priority=self.port_id.priority,
                port_number=self.ofport.port_no,
                message_age=self.port_times.message_age+1,
                max_age=self.port_times.max_age,
                hello_time=self.port_times.hello_time,
                forward_delay=self.port_times.forward_delay)

            pkt = packet.Packet()
            pkt.add_protocol(e)
            pkt.add_protocol(l)
            pkt.add_protocol(b)
            pkt.serialize()

            return pkt.data


BPDUパケット受信
""""""""""""""""

BPDUパケットの受信は、StpクラスのPacket-Inイベントハンドラによって
検出され、Bridgeクラスオブジェクトを経由してPortクラスオブジェクトに
通知されます。イベントハンドラの実装は「 :ref:`ch_switching_hub` 」を
参照してください。

BPDUパケットを受信したポートは、以前に受信したBPDUパケットと今回受信した
BPDUパケットのブリッジIDなどの比較(Stp.compare_bpdu_info())を行い、
STP再計算の要否判定を行います。以前に受信したBPDUより優れたBPDU(SUPERIOR)を
受信した場合、「新たなルートブリッジが追加された」などのネットワークトポロジ変更が
発生したことを意味するため、Bridgeクラスオブジェクトに通知されSTP再計算の契機となります。


.. rst-class:: sourcecode

::

    class Port(object):

        def rcv_config_bpdu(self, bpdu_pkt):
            # Check received BPDU is superior to currently held BPDU.
            root_id = BridgeId(bpdu_pkt.root_priority,
                               bpdu_pkt.root_system_id_extension,
                               bpdu_pkt.root_mac_address)
            root_path_cost = bpdu_pkt.root_path_cost
            designated_bridge_id = BridgeId(bpdu_pkt.bridge_priority,
                                            bpdu_pkt.bridge_system_id_extension,
                                            bpdu_pkt.bridge_mac_address)
            designated_port_id = PortId(bpdu_pkt.port_priority,
                                        bpdu_pkt.port_number)

            msg_priority = Priority(root_id, root_path_cost,
                                    designated_bridge_id,
                                    designated_port_id)
            msg_times = Times(bpdu_pkt.message_age,
                              bpdu_pkt.max_age,
                              bpdu_pkt.hello_time,
                              bpdu_pkt.forward_delay)

            rcv_info = Stp.compare_bpdu_info(self.designated_priority,
                                             self.designated_times,
                                             msg_priority, msg_times)

            # ...

            return rcv_info, rcv_tc



故障検出
""""""""

リンク断などの直接故障や、一定時間ルートブリッジからのBPDUパケットを
受信できない間接故障を検出した場合も、STP再計算の契機となります。

リンク断はStpクラスのPortStatusイベントハンドラによって検出し、
Bridgeクラスオブジェクトへ通知されます。

BPDUパケットの受信待ちタイムアウトはPortクラスのBPDUパケット受信待ちスレッド
(Port.wait_bpdu_thread)で検出します。max age(デフォルト20秒)間、ルートブリッジ
からのBPDUパケットを受信できない場合に間接故障と判断し、
Bridgeクラスオブジェクトへ通知されます。

タイマーの更新とタイムアウトの検出にはhubモジュール(ryu.lib.hub)の
hub.Eventとhub.Timeoutを用います。hub.Eventはhub.Event.wait()でwait状態に
入りhub.Event.set()が実行されるまでスレッドが中断されます。hub.Timeoutは
指定されたタイムアウト時間内にtry節の処理が終了しない場合、hub.Timeout例外
を発行します。hub.Eventがwait状態に入りhub.Timeoutで指定されたタイムアウト
時間内にhub.Event.set()が実行されない場合に、BPDUパケットの受信待ち
タイムアウトと判断しBridgeクラスのSTP再計算処理を呼び出します。


.. rst-class:: sourcecode

::

    class Port(object):

        def __init__(self, dp, logger, config, send_ev_func, timeout_func,
                     topology_change_func, bridge_id, bridge_times, ofport):
            super(Port, self).__init__()
            # ...
            self.wait_bpdu_timeout = timeout_func
            # ...
            self.wait_bpdu_thread = PortThread(self._wait_bpdu_timer)

        # ...

        def _wait_bpdu_timer(self):
            time_exceed = False

            while True:
                self.wait_timer_event = hub.Event()
                message_age = (self.designated_times.message_age
                               if self.designated_times else 0)
                timer = self.port_times.max_age - message_age
                timeout = hub.Timeout(timer)
                try:
                    self.wait_timer_event.wait()
                except hub.Timeout as t:
                    if t is not timeout:
                        err_msg = 'Internal error. Not my timeout.'
                        raise RyuException(msg=err_msg)
                    self.logger.info('[port=%d] Wait BPDU timer is exceeded.',
                                     self.ofport.port_no, extra=self.dpid_str)
                    time_exceed = True
                finally:
                    timeout.cancel()
                    self.wait_timer_event = None

                if time_exceed:
                    break

            if time_exceed:  # Bridge.recalculate_spanning_tree
                hub.spawn(self.wait_bpdu_timeout)


受信したBPDUパケットの比較処理(Stp.compare_bpdu_info())により
SUPERIORまたはREPEATEDと判定された場合は、ルートブリッジからのBPDUパケット
が受信出来ていることを意味するため、BPDU受信待ちタイマーの更新
(Port._update_wait_bpdu_timer())を行います。hub.Eventである
Port.wait_timer_eventのset()処理によりPort.wait_timer_eventはwait状態から
解放され、BPDUパケット受信待ちスレッド(Port.wait_bpdu_thread)は
except hub.Timeout節のタイムアウト処理に入ることなくタイマーをキャンセルし、
改めてタイマーをセットし直すことで次のBPDUパケットの受信待ちを開始します。


.. rst-class:: sourcecode

::

    class Port(object):

        def rcv_config_bpdu(self, bpdu_pkt):
            # ...

            rcv_info = Stp.compare_bpdu_info(self.designated_priority,
                                             self.designated_times,
                                             msg_priority, msg_times)
            # ...

            if ((rcv_info is SUPERIOR or rcv_info is REPEATED)
                    and (self.role is ROOT_PORT
                         or self.role is NON_DESIGNATED_PORT)):
                self._update_wait_bpdu_timer()

            # ...

        def _update_wait_bpdu_timer(self):
            if self.wait_timer_event is not None:
                self.wait_timer_event.set()
                self.wait_timer_event = None


STP計算
"""""""

STP計算(ルートブリッジ選択・各ポートの役割選択)はBridgeクラスで実行します。

STP計算が実行されるケースではネットワークトポロジの変更が発生しており
パケットがループする可能性があるため、一旦全てのポートをBLOCK状態に設定
(port.down)し、かつトポロジ変更イベント(EventTopologyChange)を上位APLに
対して通知することで学習済みのMACアドレス情報の初期化を促します。

その後、Bridge._spanning_tree_algorithm()でルートブリッジとポートの役割を
選択した上で、各ポートをLISTEN状態で起動(port.up)しポートの状態遷移を開始します。


.. rst-class:: sourcecode

::

    class Bridge(object):

        def recalculate_spanning_tree(self, init=True):
            """ Re-calculation of spanning tree. """
            # All port down.
            for port in self.ports.values():
                if port.state is not PORT_STATE_DISABLE:
                    port.down(PORT_STATE_BLOCK, msg_init=init)

            # Send topology change event.
            if init:
                self.send_event(EventTopologyChange(self.dp))

            # Update tree roles.
            port_roles = {}
            self.root_priority = Priority(self.bridge_id, 0, None, None)
            self.root_times = self.bridge_times

            if init:
                self.logger.info('Root bridge.', extra=self.dpid_str)
                for port_no in self.ports.keys():
                    port_roles[port_no] = DESIGNATED_PORT
            else:
                (port_roles,
                 self.root_priority,
                 self.root_times) = self._spanning_tree_algorithm()

            # All port up.
            for port_no, role in port_roles.items():
                if self.ports[port_no].state is not PORT_STATE_DISABLE:
                    self.ports[port_no].up(role, self.root_priority,
                                           self.root_times)


ルートブリッジの選出のため、ブリッジIDなどの自身のブリッジ情報と
各ポートが受信したBPDUパケットに設定された他ブリッジ情報を比較します
(Bridge._select_root_port)。

この結果、ルートポートが見つかった場合(自身のブリッジ情報よりもポートが
受信した他ブリッジ情報が優れていた場合)、他ブリッジがルートブリッジであると
判断し指定ポートの選出(Bridge._select_designated_port)と非指定ポートの選出
(ルートポート/指定ポート以外のポートを非指定ポートとして選出)を行います。

一方、ルートポートが見つからなかった場合(自身のブリッジ情報が最も優れていた場合)は
自身をルートブリッジと判断し各ポートは全て指定ポートとなります。



.. rst-class:: sourcecode

::

    class Bridge(object):

        def _spanning_tree_algorithm(self):
            """ Update tree roles.
                 - Root bridge:
                    all port is DESIGNATED_PORT.
                 - Non root bridge:
                    select one ROOT_PORT and some DESIGNATED_PORT,
                    and the other port is set to NON_DESIGNATED_PORT."""
            port_roles = {}

            root_port = self._select_root_port()

            if root_port is None:
                # My bridge is a root bridge.
                self.logger.info('Root bridge.', extra=self.dpid_str)
                root_priority = self.root_priority
                root_times = self.root_times

                for port_no in self.ports.keys():
                    if self.ports[port_no].state is not PORT_STATE_DISABLE:
                        port_roles[port_no] = DESIGNATED_PORT
            else:
                # Other bridge is a root bridge.
                self.logger.info('Non root bridge.', extra=self.dpid_str)
                root_priority = root_port.designated_priority
                root_times = root_port.designated_times

                port_roles[root_port.ofport.port_no] = ROOT_PORT

                d_ports = self._select_designated_port(root_port)
                for port_no in d_ports:
                    port_roles[port_no] = DESIGNATED_PORT

                for port in self.ports.values():
                    if port.state is not PORT_STATE_DISABLE:
                        port_roles.setdefault(port.ofport.port_no,
                                              NON_DESIGNATED_PORT)

            return port_roles, root_priority, root_times




ポート状態遷移
""""""""""""""

ポートの状態遷移処理は、Portクラスの状態遷移制御スレッド(Port.state_machine)
で実行しています。次の状態に遷移するまでのタイマーをPort._get_timer()で
取得し、タイマー満了後にPort._get_next_state()で次状態を取得し、状態遷移を
行います。また、STP再計算が発生しこれまでのポート状態に関係無くBLOCK状態に
遷移させるケースなど、Port._change_status()が実行された場合にも状態遷移が
行われます。これらの処理は「 `故障検出`_ 」と同様に
hubモジュールのhub.Eventとhub.Timeoutを用いて実現しています。


.. rst-class:: sourcecode

::

    class Port(object):

        def _state_machine(self):
            """ Port state machine.
                 Change next status when timer is exceeded
                 or _change_status() method is called."""

            # ...

            while True:
                self.logger.info('[port=%d] %s / %s', self.ofport.port_no,
                                 role_str[self.role], state_str[self.state],
                                 extra=self.dpid_str)

                self.state_event = hub.Event()
                timer = self._get_timer()
                if timer:
                    timeout = hub.Timeout(timer)
                    try:
                        self.state_event.wait()
                    except hub.Timeout as t:
                        if t is not timeout:
                            err_msg = 'Internal error. Not my timeout.'
                            raise RyuException(msg=err_msg)
                        new_state = self._get_next_state()
                        self._change_status(new_state, thread_switch=False)
                    finally:
                        timeout.cancel()
                else:
                    self.state_event.wait()

                self.state_event = None

        def _get_timer(self):
            timer = {PORT_STATE_DISABLE: None,
                     PORT_STATE_BLOCK: None,
                     PORT_STATE_LISTEN: self.port_times.forward_delay,
                     PORT_STATE_LEARN: self.port_times.forward_delay,
                     PORT_STATE_FORWARD: None}
            return timer[self.state]

        def _get_next_state(self):
            next_state = {PORT_STATE_DISABLE: None,
                          PORT_STATE_BLOCK: None,
                          PORT_STATE_LISTEN: PORT_STATE_LEARN,
                          PORT_STATE_LEARN: (PORT_STATE_FORWARD
                                             if (self.role is ROOT_PORT or
                                                 self.role is DESIGNATED_PORT)
                                             else PORT_STATE_BLOCK),
                          PORT_STATE_FORWARD: None}
            return next_state[self.state]



アプリケーションの実装
^^^^^^^^^^^^^^^^^^^^^^

「 `Ryuアプリケーションの実行`_ 」に示したOpenFlow 1.3対応のスパニングツリー
アプリケーション(simple_switch_stp_13.py)と、「 :ref:`ch_switching_hub` 」
のスイッチングハブとの差異を順に説明していきます。


「_CONTEXTS」の設定
"""""""""""""""""""

「 :ref:`ch_link_aggregation` 」と同様にSTPライブラリを利用するため
CONTEXT登録します。


.. rst-class:: sourcecode

::

    from ryu.lib import stplib

    # ...

    class SimpleSwitch13(app_manager.RyuApp):
        OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
        _CONTEXTS = {'stplib': stplib.Stp}

        # ...


コンフィグ設定
""""""""""""""

STPライブラリのset_config()メソッドを用いてコンフィグ設定を行います。
ここでは以下の値を設定します。

===================== =============== ======
OpenFlowスイッチ      項目            設定値
===================== =============== ======
dpid=0000000000000001 bridge.priority 0x8000
dpid=0000000000000002 bridge.priority 0x9000
dpid=0000000000000003 bridge.priority 0xa000
===================== =============== ======

この設定によりdpid=0000000000000001のOpenFlowスイッチのブリッジIDが
常に最小の値となり、ルートブリッジに選択されることになります。


.. rst-class:: sourcecode

::

    class SimpleSwitch13(app_manager.RyuApp):

        # ...

        def __init__(self, *args, **kwargs):
            super(SimpleSwitch13, self).__init__(*args, **kwargs)
            self.mac_to_port = {}
            self.stp = kwargs['stplib']

            # Sample of stplib config.
            #  please refer to stplib.Stp.set_config() for details.
            config = {dpid_lib.str_to_dpid('0000000000000001'):
                         {'bridge': {'priority': 0x8000}},
                      dpid_lib.str_to_dpid('0000000000000002'):
                         {'bridge': {'priority': 0x9000}},
                      dpid_lib.str_to_dpid('0000000000000003'):
                         {'bridge': {'priority': 0xa000}}}
            self.stp.set_config(config)


STPイベント処理
"""""""""""""""

「 :ref:`ch_link_aggregation` 」と同様にSTPライブラリから通知される
イベントを受信するイベントハンドラを用意します。



* STPライブラリで定義されたEventPacketInイベントを利用することで、BPDUパケットを
  除いたパケットを受信することが出来るため、「 :ref:`ch_switching_hub` 」と同様の
  ハンドリンクを行います。

    .. rst-class:: sourcecode

    ::

        class SimpleSwitch13(app_manager.RyuApp):

            @set_ev_cls(stplib.EventPacketIn, MAIN_DISPATCHER)
            def _packet_in_handler(self, ev):

                # ...


* ネットワークトポロジの変更通知イベントを受け取り、学習したMACアドレスおよび
  登録済みのフローエントリを初期化しています。


    .. rst-class:: sourcecode

    ::

        class SimpleSwitch13(app_manager.RyuApp):

            def delete_flow(self, datapath):
                ofproto = datapath.ofproto
                parser = datapath.ofproto_parser

                for dst in self.mac_to_port[datapath.id].keys():
                    match = parser.OFPMatch(eth_dst=dst)
                    mod = parser.OFPFlowMod(
                        datapath, command=ofproto.OFPFC_DELETE,
                        out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                        priority=1, match=match)
                    datapath.send_msg(mod)

            # ...

            @set_ev_cls(stplib.EventTopologyChange, MAIN_DISPATCHER)
            def _topology_change_handler(self, ev):
                dp = ev.dp
                dpid_str = dpid_lib.dpid_to_str(dp.id)
                msg = 'Receive topology change event. Flush MAC table.'
                self.logger.debug("[dpid=%s] %s", dpid_str, msg)

                if dp.id in self.mac_to_port:
                    self.delete_flow(dp)
                    del self.mac_to_port[dp.id]


* ポート状態の変更通知イベントを受け取り、ポート状態のデバッグログ出力を
  行っています。

    .. rst-class:: sourcecode

    ::

        class SimpleSwitch13(app_manager.RyuApp):

            @set_ev_cls(stplib.EventPortStateChange, MAIN_DISPATCHER)
            def _port_state_change_handler(self, ev):
                dpid_str = dpid_lib.dpid_to_str(ev.dp.id)
                of_state = {stplib.PORT_STATE_DISABLE: 'DISABLE',
                            stplib.PORT_STATE_BLOCK: 'BLOCK',
                            stplib.PORT_STATE_LISTEN: 'LISTEN',
                            stplib.PORT_STATE_LEARN: 'LEARN',
                            stplib.PORT_STATE_FORWARD: 'FORWARD'}
                self.logger.debug("[dpid=%s][port=%d] state=%s",
                                  dpid_str, ev.port_no, of_state[ev.port_state])



以上のように、スパニングツリー機能を提供するライブラリと、ライブラリを
利用するアプリケーションによって、スパニングツリー機能を持つスイッチングハブの
アプリケーションを実現しています。



まとめ
------

本章では、スパニングツリーライブラリの利用を題材として、以下の項目に
ついて説明しました。

* hub.Eventを用いたイベント待ち合わせ処理の実現方法
* hub.Timeoutを用いたタイマー制御処理の実現方法
