.. _ch_spanning_tree:

スパニングツリー
================

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
各スイッチ(本章ではブリッジと呼ぶことがあります)のポートをフレーム転送可能または不可能な状態に設定することで、
ループ構造を持つネットワークでブロードキャストストームの発生を抑制します。


.. only:: latex

    .. image:: images/spanning_tree/fig1.eps
        :align: center

.. only:: epub

    .. image:: images/spanning_tree/fig1.png
        :align: center

.. only:: not latex and not epub

    .. image:: images/spanning_tree/fig1.png
        :scale: 50 %
        :align: center


STPではブリッジ間でBPDU(Bridge Protocol Data Unit)パケットを相互に交換
し、ブリッジやポートの情報を比較しあうことで、
各ポートのフレーム転送可否を決定します。

具体的には、次のような手順により実現されます。

1．ルートブリッジの選出

    ブリッジ間のBPDUパケットの交換により、最小のブリッジIDを持つブリッジが
    ルートブリッジとして選出されます。以降はルートブリッジのみがオリジナルの
    BPDUパケットを送信し、他のブリッジはルートブリッジから受信したBPDUパケット
    を転送します。

.. NOTE::

    ブリッジIDは、各ブリッジに設定されたブリッジpriority
    と特定ポートのMACアドレスの組み合わせで算出されます。

        ブリッジID

        ================ ===========
        上位2byte        下位6byte  
        ================ ===========
        ブリッジpriority MACアドレス
        ================ ===========

2．ポートの役割の決定

    各ポートのルートブリッジに至るまでのコストを元に、ポートの役割を決定します。

    * ルートポート(Root port)

        ブリッジ内で最もルートブリッジまでのコストが小さいポート。
        ルートブリッジからのBPDUパケットを受信するポートになります。

    * 指定ポート(Designated port)

        各リンクのルートブリッジまでのコストが小さい側のポート。
        ルートブリッジから受信したBPDUパケットを送信するポートになります。
        ルートブリッジのポートは全て指定ポートです。

    * 非指定ポート(Non designated port)

        ルートポート・指定ポート以外のポート。
        フレーム転送を抑制するポートです。



        .. only:: latex

            .. image:: images/spanning_tree/fig2.eps
                :scale: 80 %

.. only:: epub

    .. image:: images/spanning_tree/fig2.png
        :align: center

.. only:: not latex and not epub

    .. image:: images/spanning_tree/fig2.png
        :align: center
        :scale: 50 %



.. NOTE::

    ルートブリッジに至るまでのコストは、各ポートが受信したBPDUパケットの
    設定値から次のように比較されます。

        優先1：root path cost値による比較。

            各ブリッジはBPDUパケットを転送する際に、出力ポートに設定された
            path cost値をBPDUパケットのroot path cost値に加算します。
            これによりroot path cost値はルートブリッジに到達するまでに
            経由する各リンクのpath cost値の合計の値となります。

        優先2：root path cost値が同じ場合、対向ブリッジのブリッジIDにより比較。

        優先3：対向ブリッジのブリッジIDが同じ場合(各ポートが同一ブリッジに
        接続しているケース)、対向ポートのポートIDにより比較。

            ポートID

            ============== ==========
            上位2byte      下位2byte
            ============== ==========
            ポートpriority ポート番号
            ============== ==========


3．ポートの状態遷移

    ポート役割の決定後(STP計算の完了時)、各ポートはLISTEN状態になります。
    その後、以下に示す状態遷移を行い、最終的に各ポートの役割に従って
    FORWARD状態またはBLOCK状態に遷移します。コンフィグで無効ポートと設定
    されたポートはDISABLE状態となり、以降、状態遷移は行われません。


.. only:: latex

   .. image:: images/spanning_tree/fig3.eps
        :align: center

.. only:: epub

    .. image:: images/spanning_tree/fig3.png
        :align: center

.. only:: not latex and not epub

    .. image:: images/spanning_tree/fig3.png
        :align: center
        :scale: 50 %


    各ポートは状態に応じてフレーム転送有無などの動作を決定します。

    ======= =============================================
    状態    動作
    ======= =============================================
    DISABLE 無効ポート。全ての受信パケットを無視します。
    BLOCK   BPDU受信のみ を行います。
    LISTEN  BPDU送受信 を行います。
    LEARN   BPDU送受信／MAC学習 を行います。
    FORWARD BPDU送受信／MAC学習／フレーム転送 を行います。
    ======= =============================================



これらの処理が各ブリッジで実行されることにより、フレーム転送を行うポートと
フレーム転送を抑制するポートが決定され、ネットワーク内のループが解消されます。

また、リンクダウンやBPDUパケットのmax age(デフォルト20秒)間の未受信
による故障検出、あるいはポートの追加等によりネットワークトポロジの変更を
検出した場合は、各ブリッジで上記の 1. 2. 3. を実行しツリーの再構築が
行われます(STPの再計算)。



Ryuアプリケーションの実行
-------------------------

スパニングツリーの機能をOpenFlowを用いて実現した、Ryuのスパニングツリー
アプリケーションを実行してみます。

このプログラムは、「 :ref:`ch_switching_hub` 」にスパニングツリー機能を
追加したアプリケーションです。


ソース名： ``simple_switch_stp_13.py``

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_stp_13.py
    :lines: 16-

.. NOTE::

    使用するスイッチがOpen vSwitchの場合、バージョンや設定によっては
    BPDUが転送されず、本アプリが正常に動作しないことがあります。
    Open vSwitchではスイッチ自身の機能としてSTPを実装していますが、
    この機能を無効(デフォルト設定)にしている場合、
    IEEE 802.1Dで規定されるスパニングツリーのマルチキャストMACアドレス
    "01:80:c2:00:00:00"を宛先とするパケットを転送しないためです。
    本アプリを動作させる際は、下記のようなソース修正を行うことで、
    この制約を回避できます。

    ryu/ryu/lib/packet/bpdu.py:

    .. rst-class:: sourcecode

    ::

        # BPDU destination
        #BRIDGE_GROUP_ADDRESS = '01:80:c2:00:00:00'
        BRIDGE_GROUP_ADDRESS = '01:80:c2:00:00:0e'

    なお、ソース修正後は変更を反映させるため、下記のコマンドを実行してください。

    .. rst-class:: console

    ::

        $ cd ryu
        $ sudo python setup.py install
        running install
        ...
        ...
        running install_scripts
        Installing ryu-manager script to /usr/local/bin
        Installing ryu script to /usr/local/bin


実験環境の構築
^^^^^^^^^^^^^^

スパニングツリーアプリケーションの動作確認を行う実験環境を構築します。

VMイメージ利用のための環境設定やログイン方法等は「 :ref:`ch_switching_hub` 」
を参照してください。

ループ構造を持つ特殊なトポロジで動作させるため、「 :ref:`ch_link_aggregation` 」
と同様にトポロジ構築スクリプトによりmininet環境を構築します。


ソース名： ``spanning_tree.py``

.. rst-class:: sourcecode

.. literalinclude:: ../../sources/spanning_tree.py


VM環境でこのプログラムを実行することにより、スイッチs1、s2、s3の間でループが
存在するトポロジが作成されます。



.. only:: latex

    .. image:: images/spanning_tree/fig4.eps
        :scale: 70 %
        :align: center

.. only:: epub

    .. image:: images/spanning_tree/fig4.png
        :align: center

.. only:: not latex and not epub

    .. image:: images/spanning_tree/fig4.png
        :align: center
        :scale: 50 %



netコマンドの実行結果は以下の通りです。


.. rst-class:: console

::

    $ curl -O https://raw.githubusercontent.com/osrg/ryu-book/master/sources/spanning_tree.py
    $ sudo ./spanning_tree.py
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

    # ovs-vsctl set Bridge s1 protocols=OpenFlow13


Node: s2:

.. rst-class:: console

::

    # ovs-vsctl set Bridge s2 protocols=OpenFlow13


Node: s3:

.. rst-class:: console

::

    # ovs-vsctl set Bridge s3 protocols=OpenFlow13




スイッチングハブの実行
^^^^^^^^^^^^^^^^^^^^^^

準備が整ったので、Ryuアプリケーションを実行します。ウインドウタイトルが
「Node: c0 (root)」となっている xterm から次のコマンドを実行します。


Node: c0:

.. rst-class:: console

::

    $ ryu-manager ryu.app.simple_switch_stp_13
    loading app ryu.app.simple_switch_stp_13
    loading app ryu.controller.ofp_handler
    instantiating app None of Stp
    creating context stplib
    instantiating app ryu.app.simple_switch_stp_13 of SimpleSwitch13
    instantiating app ryu.controller.ofp_handler of OFPHandler


OpenFlowスイッチ起動時のSTP計算
"""""""""""""""""""""""""""""""

各OpenFlowスイッチとコントローラの接続が完了すると、BPDUパケットの交換が
始まり、ルートブリッジの選出・ポート役割の設定・ポート状態遷移が行われます。


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


この結果、最終的に各ポートはFORWARD状態またはBLOCK状態となります。



.. only:: latex

    .. image:: images/spanning_tree/fig5.eps
        :scale: 70 %
        :align: center

.. only:: epub

    .. image:: images/spanning_tree/fig5.png
        :align: center

.. only:: not latex and not epub

    .. image:: images/spanning_tree/fig5.png
        :align: center
        :scale: 50 %



パケットがループしないことを確認するため、ホスト1からホスト2へpingを実行します。

pingコマンドを実行する前に、
tcpdumpコマンドを実行しておきます。



Node: s1:

.. rst-class:: console

::

    # tcpdump -i s1-eth2 arp


Node: s2:

.. rst-class:: console

::

    # tcpdump -i s2-eth2 arp


Node: s3:

.. rst-class:: console

::

    # tcpdump -i s3-eth2 arp


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


tcpdumpの出力結果から、ARPがループしていないことが
確認できます。


Node: s1:

.. rst-class:: console

::

    # tcpdump -i s1-eth2 arp
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

    # tcpdump -i s2-eth2 arp
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

    # tcpdump -i s3-eth2 arp
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

    # ifconfig s2-eth2 down



リンクダウンが検出され、STP再計算が実行されます。


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


これまでBLOCK状態だったs3-eth2のポートがFORWARD状態となり、
再びフレーム転送可能な状態となったことが確認できます。


.. only:: latex

    .. image:: images/spanning_tree/fig6.eps
        :scale: 70 %
        :align: center

.. only:: epub

    .. image:: images/spanning_tree/fig6.png
        :align: center

.. only:: not latex and not epub

    .. image:: images/spanning_tree/fig6.png
        :align: center
        :scale: 50 %



故障回復時のSTP再計算
"""""""""""""""""""""

続けて、リンクダウンが回復した際のSTP再計算の動作を確認します。
リンクダウン中の状態で次のコマンドを実行し、ポートを起動させます。


Node: s2:

.. rst-class:: console

::

    # ifconfig s2-eth2 up



リンク復旧が検出され、STP再計算が実行されます。


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


アプリケーション起動時と同様のツリー構成となり、再びフレーム転送可能
な状態となったことが確認できます。


.. only:: latex

    .. image:: images/spanning_tree/fig7.eps
        :scale: 70 %
        :align: center

.. only:: epub

    .. image:: images/spanning_tree/fig7.png
        :align: center

.. only:: not latex and not epub

    .. image:: images/spanning_tree/fig7.png
        :align: center
        :scale: 50 %



OpenFlowによるスパニングツリー
------------------------------

Ryuのスパニングツリーアプリケーションにおいて、OpenFlowを用いてどのように
スパニングツリーの機能を実現しているかを見ていきます。

OpenFlow 1.3には次のようなポートの動作を設定するコンフィグが用意されています。
Port ModificationメッセージをOpenFlowスイッチに発行
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


======= ================ ============================
状態    ポートコンフィグ フローエントリ
======= ================ ============================
DISABLE NO_RECV／NO_FWD  設定無し
BLOCK   NO_FWD           BPDU Packet-In／BPDU以外drop
LISTEN  設定無し         BPDU Packet-In／BPDU以外drop
LEARN   設定無し         BPDU Packet-In／BPDU以外drop
FORWARD 設定無し         BPDU Packet-In
======= ================ ============================


.. NOTE::

    Ryuに実装されているスパニングツリーのライブラリは、簡略化のため
    LEARN状態でのMACアドレス学習(BPDU以外のパケット受信)を行っていません。


これらの設定に加え、コントローラはOpenFlowスイッチとの接続時に収集した
ポート情報や各OpenFlowスイッチが受信したBPDUパケットに設定されたルートブリッジ
の情報を元に、送信用のBPDUパケットを構築しPacket-Outメッセージを発行することで、
OpenFlowスイッチ間のBPDUパケットの交換を実現します。



Ryuによるスパニングツリーの実装
-------------------------------

続いて、Ryuを用いて実装されたスパニングツリーのソースコードを見ていきます。
スパニングツリーのソースコードは、Ryuのソースツリーにあります。

    ryu/lib/stplib.py

    ryu/app/simple_switch_stp_13.py


stplib.pyはBPDUパケットの交換や各ポートの役割・状態の管理などの
スパニングツリー機能を提供するライブラリです。
simple_switch_stp_13.pyはスパニングツリーライブラリを適用することで
スイッチングハブのアプリケーションにスパニングツリー機能を追加した
アプリケーションプログラムです。

ライブラリの実装
^^^^^^^^^^^^^^^^

ライブラリ概要
""""""""""""""

.. only:: latex

    .. image:: images/spanning_tree/fig8.eps
        :scale: 80 %
        :align: center

.. only:: epub

    .. image:: images/spanning_tree/fig8.png
        :align: center

.. only:: not latex and not epub

    .. image:: images/spanning_tree/fig8.png
        :scale: 40 %
        :align: center



STPライブラリ(Stpクラスインスタンス)がOpenFlowスイッチのコントローラ
への接続を検出すると、Bridgeクラスインスタンス・Portクラスインスタンスが
生成されます。各クラスインスタンスが生成・起動された後は、

* StpクラスインスタンスからのOpenFlowメッセージ受信通知
* BridgeクラスインスタンスのSTP計算(ルートブリッジ選択・各ポートの役割選択)
* Portクラスインスタンスのポート状態遷移・BPDUパケット送受信

が連動し、スパニングツリー機能を実現します。



コンフィグ設定項目
""""""""""""""""""

STPライブラリは ``Stp.set_config()`` メソッドによりブリッジ・ポートの
コンフィグ設定IFを提供します。設定可能な項目は以下の通りです。


* bridge

    ================ =================================================== ============
    項目             説明                                                デフォルト値
    ================ =================================================== ============
     ``priority``    ブリッジ優先度                                      0x8000
     ``sys_ext_id``  VLAN-IDを設定 (\*現状のSTPライブラリはVLAN未対応)   0
     ``max_age``     BPDUパケットの受信待ちタイマー値                    20[sec]
     ``hello_time``  BPDUパケットの送信間隔                              2 [sec]
     ``fwd_delay``   各ポートがLISTEN状態およびLEARN状態に留まる時間     15[sec]
    ================ =================================================== ============


* port

    =============== ==================== ============================
    項目            説明                 デフォルト値
    =============== ==================== ============================
     ``priority``   ポート優先度         0x80
     ``path_cost``  リンクのコスト値     リンクスピードを元に自動設定
     ``enable``     ポートの有効無効設定 True
    =============== ==================== ============================



BPDUパケット送信
""""""""""""""""

BPDUパケット送信はPortクラスのBPDUパケット送信スレッド
( ``Port.send_bpdu_thread`` )で行っています。ポートの役割が指定ポート
( ``DESIGNATED_PORT`` )の場合、ルートブリッジから通知されたhello time
( ``Port.port_times.hello_time`` ：デフォルト2秒)間隔でBPDUパケット生成
( ``Port._generate_config_bpdu()`` )およびBPDUパケット送信
( ``Port.ofctl.send_packet_out()`` )を行います。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/stplib.py
    :prepend: class Port(object):
              # ...
    :pyobject: Port.__init__

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/stplib.py
    :prepend: class Port(object):
              # ...
    :pyobject: Port._transmit_bpdu

送信するBPDUパケットは、OpenFlowスイッチのコントローラ接続時に収集した
ポート情報( ``Port.ofport`` )や受信したBPDUパケットに設定された
ルートブリッジ情報( ``Port.port_priority、Port.port_times`` )などを元に
構築されます。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/stplib.py
    :prepend: class Port(object):
              # ...
    :pyobject: Port._generate_config_bpdu

BPDUパケット受信
""""""""""""""""

BPDUパケットの受信は、StpクラスのPacket-Inイベントハンドラによって検出され、
Bridgeクラスインスタンスを経由してPortクラスインスタンスに通知されます。
イベントハンドラの実装は「 :ref:`ch_switching_hub` 」を参照してください。

BPDUパケットを受信したポートは、以前に受信したBPDUパケットと今回受信した
BPDUパケットのブリッジIDなどの比較( ``Stp.compare_bpdu_info()`` )を行い、
STP再計算の要否判定を行います。以前に受信したBPDUより優れたBPDU( ``SUPERIOR`` )
を受信した場合、「新たなルートブリッジが追加された」などのネットワーク
トポロジ変更が発生したことを意味するため、STP再計算の契機となります。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/stplib.py
    :prepend: class Port(object):
              # ...
    :pyobject: Port.rcv_config_bpdu

故障検出
""""""""

リンク断などの直接故障や、一定時間ルートブリッジからのBPDUパケットを
受信できない間接故障を検出した場合も、STP再計算の契機となります。

リンク断はStpクラスのPortStatusイベントハンドラによって検出し、Bridgeクラス
インスタンスへ通知されます。

BPDUパケットの受信待ちタイムアウトはPortクラスのBPDUパケット受信待ちスレッド
( ``Port.wait_bpdu_thread`` )で検出します。max age(デフォルト20秒)間、
ルートブリッジからのBPDUパケットを受信できない場合に間接故障と判断し、
Bridgeクラスインスタンスへ通知されます。

BPDU受信待ちタイマーの更新とタイムアウトの検出にはhubモジュール(ryu.lib.hub)
の ``hub.Event`` と ``hub.Timeout`` を用います。 ``hub.Event`` は
``hub.Event.wait()`` でwait状態に入り ``hub.Event.set()`` が実行されるまで
スレッドが中断されます。 ``hub.Timeout`` は指定されたタイムアウト時間内に
``try`` 節の処理が終了しない場合、 ``hub.Timeout`` 例外を発行します。
``hub.Event`` がwait状態に入り ``hub.Timeout`` で指定されたタイムアウト時間内に
``hub.Event.set()`` が実行されない場合に、BPDUパケットの受信待ちタイムアウト
と判断しBridgeクラスのSTP再計算処理を呼び出します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/stplib.py
    :prepend: class Port(object):
              # ...
    :pyobject: Port._wait_bpdu_timer

受信したBPDUパケットの比較処理( ``Stp.compare_bpdu_info()`` )により
``SUPERIOR`` または ``REPEATED`` と判定された場合は、ルートブリッジからの
BPDUパケットが受信出来ていることを意味するため、BPDU受信待ちタイマーの更新
( ``Port._update_wait_bpdu_timer()`` )を行います。 ``hub.Event`` である
``Port.wait_timer_event`` の ``set()`` 処理により ``Port.wait_timer_event``
はwait状態から解放され、BPDUパケット受信待ちスレッド( ``Port.wait_bpdu_thread`` )
は ``except hub.Timeout`` 節のタイムアウト処理に入ることなくタイマーを
キャンセルし、改めてタイマーをセットし直すことで次のBPDUパケットの受信待ち
を開始します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/stplib.py
    :prepend: class Port(object):
              # ...
    :pyobject: Port.rcv_config_bpdu

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/stplib.py
    :prepend: class Port(object):
              # ...
    :pyobject: Port._update_wait_bpdu_timer

STP計算
"""""""

STP計算(ルートブリッジ選択・各ポートの役割選択)はBridgeクラスで実行します。

STP計算が実行されるケースではネットワークトポロジの変更が発生しており
パケットがループする可能性があるため、一旦全てのポートをBLOCK状態に設定
( ``port.down`` )し、かつトポロジ変更イベント( ``EventTopologyChange`` )
を上位APLに対して通知することで学習済みのMACアドレス情報の初期化を促します。

その後、 ``Bridge._spanning_tree_algorithm()`` でルートブリッジとポートの
役割を選択した上で、各ポートをLISTEN状態で起動( ``port.up`` )しポートの
状態遷移を開始します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/stplib.py
    :prepend: class Bridge(object):
              # ...
    :pyobject: Bridge.recalculate_spanning_tree

ルートブリッジの選出のため、ブリッジIDなどの自身のブリッジ情報と
各ポートが受信したBPDUパケットに設定された他ブリッジ情報を比較します
( ``Bridge._select_root_port`` )。

この結果、ルートポートが見つかった場合(自身のブリッジ情報よりもポートが
受信した他ブリッジ情報が優れていた場合)、他ブリッジがルートブリッジであると
判断し指定ポートの選出( ``Bridge._select_designated_port`` )と非指定ポート
の選出(ルートポート／指定ポート以外のポートを非指定ポートとして選出)を行います。

一方、ルートポートが見つからなかった場合(自身のブリッジ情報が最も優れていた場合)は
自身をルートブリッジと判断し各ポートは全て指定ポートとなります。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/stplib.py
    :prepend: class Bridge(object):
              # ...
    :pyobject: Bridge._spanning_tree_algorithm

ポート状態遷移
""""""""""""""

ポートの状態遷移処理は、Portクラスの状態遷移制御スレッド( ``Port.state_machine`` )
で実行しています。次の状態に遷移するまでのタイマーを ``Port._get_timer()`` で
取得し、タイマー満了後に ``Port._get_next_state()`` で次状態を取得し、
状態遷移を行います。また、STP再計算が発生しこれまでのポート状態に関係無く
BLOCK状態に遷移させるケースなど、 ``Port._change_status()`` が実行された場合
にも状態遷移が行われます。これらの処理は「 `故障検出`_ 」と同様に
hubモジュールの ``hub.Event`` と ``hub.Timeout`` を用いて実現しています。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/stplib.py
    :prepend: class Port(object):
              # ...
    :pyobject: Port._state_machine

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/stplib.py
    :prepend: class Port(object):
              # ...
    :pyobject: Port._get_timer

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/lib/stplib.py
    :prepend: class Port(object):
              # ...
    :pyobject: Port._get_next_state

アプリケーションの実装
^^^^^^^^^^^^^^^^^^^^^^

「 `Ryuアプリケーションの実行`_ 」に示したOpenFlow 1.3対応のスパニングツリー
アプリケーション(simple_switch_stp_13.py)と、「 :ref:`ch_switching_hub` 」
のスイッチングハブとの差異を順に説明していきます。


「_CONTEXTS」の設定
"""""""""""""""""""

「 :ref:`ch_link_aggregation` 」と同様にSTPライブラリを利用するため
CONTEXTを登録します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_stp_13.py
    :prepend: from ryu.lib import stplib
              # ...
    :pyobject: SimpleSwitch13
    :end-before: __init__

コンフィグ設定
""""""""""""""

STPライブラリの ``set_config()`` メソッドを用いてコンフィグ設定を行います。
ここではサンプルとして、以下の値を設定します。

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

.. literalinclude:: ../../ryu/app/simple_switch_stp_13.py
    :dedent: 4
    :pyobject: SimpleSwitch13.__init__

STPイベント処理
"""""""""""""""

「 :ref:`ch_link_aggregation` 」と同様にSTPライブラリから通知される
イベントを受信するイベントハンドラを用意します。



STPライブラリで定義された ``stplib.EventPacketIn`` イベントを利用することで、
BPDUパケットを除いたパケットを受信することが出来るため、
「 :ref:`ch_switching_hub` 」と同様のパケットハンドリンクを行います。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_stp_13.py
    :dedent: 4
    :prepend: @set_ev_cls(stplib.EventPacketIn, MAIN_DISPATCHER)
    :pyobject: SimpleSwitch13._packet_in_handler
    :end-before:  pkt = packet.Packet(msg.data)
    :append: # ...

ネットワークトポロジの変更通知イベント( ``stplib.EventTopologyChange`` )を
受け取り、学習したMACアドレスおよび登録済みのフローエントリを初期化しています。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_stp_13.py
    :dedent: 4
    :pyobject: SimpleSwitch13.delete_flow

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_stp_13.py
    :dedent: 4
    :prepend: @set_ev_cls(stplib.EventTopologyChange, MAIN_DISPATCHER)
    :pyobject: SimpleSwitch13._topology_change_handler

ポート状態の変更通知イベント( ``stplib.EventPortStateChange`` )を受け取り、
ポート状態のデバッグログ出力を行っています。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_stp_13.py
    :dedent: 4
    :prepend: @set_ev_cls(stplib.EventPortStateChange, MAIN_DISPATCHER)
    :pyobject: SimpleSwitch13._port_state_change_handler

以上のように、スパニングツリー機能を提供するライブラリと、ライブラリを
利用するアプリケーションによって、スパニングツリー機能を持つスイッチングハブの
アプリケーションを実現しています。



まとめ
------

本章では、スパニングツリーライブラリの利用を題材として、以下の項目に
ついて説明しました。

* hub.Eventを用いたイベント待ち合わせ処理の実現方法
* hub.Timeoutを用いたタイマー制御処理の実現方法
