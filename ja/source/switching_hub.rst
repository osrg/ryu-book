スイッチングハブの実装
======================

本章では、簡単なスイッチングハブの実装を題材として、RyuによるOpenFlow
コントローラの実装方法を解説していきます。


スイッチングハブ
----------------

世の中には様々な機能を持つスイッチングハブがありますが、ここでは一番単純な、
必要最低限の機能を持ったスイッチングハブの実装をみてみます。

スイッチングハブの機能は次のようなものとします。

* ポートに接続されているホストのMACアドレスを学習し、MACアドレステーブル
  に保持する
* 受信パケットの宛先ホストが接続されているポートへ、パケットを転送する
* 未知の宛先ホストへのパケットは、フラッディングする

これらの機能をOpenFlowで実現します。


OpenFlowによるスイッチングハブ
------------------------------

コントローラは、OpenFlowスイッチがパケット受信時に発行するPacket-In
メッセージから、ポートに接続されているホストのMACアドレスを学習します。

OpenFlow 1.3では、OpenFlowスイッチにPacket-Inを発行させるために、Table-
missフローエントリという特別なエントリをフローテーブルに追加する必要
があります。

Table-missフローエントリは、優先度が最低(0)で、すべてのパケットにマッチ
するエントリです。このエントリのインストラクションにコントローラポート
への出力アクションを指定することで、受信パケットが、すべての通常のフロー
エントリにマッチしなかった場合、Packet-Inを発行するようになります。

.. NOTE::

    現時点のOpen vSwitchでは、まだOpenFlow 1.3への対応が不完全であり、
    OpenFlow 1.3以前と同様にデフォルトでPacket-Inが発行されます。また、
    Table-missフローエントリにも現時点では未対応で、通常のフローエントリ
    として扱われます。

コントローラは、受信したPacket-Inメッセージから、パケットの受信ポートと
送信元MACアドレスを得て、MACアドレステーブルを更新します。

また、宛先MACアドレスをMACアドレステーブルから検索し、見つかった場合は
対応するポートへ転送するようPacket-OutメッセージをOpenFlowスイッチに
発行します。

さらに、対応するModify Flow Entry(Flow Mod)メッセージを発行し、OpenFlow
スイッチにフローエントリを設定することで、同一条件のパケットについては、
Packet-Inメッセージを発行せずにパケット転送するようにします。

宛先MACアドレスがMACアドレステーブルに存在しないアドレスだった場合は、
フラッディングを指定したPacket-Outメッセージを発行します。

.. HINT::

    OpenFlowでは、NORMALポートという論理的な出力ポートがオプションで規定
    されており、出力ポートにNORMALを指定すると、スイッチのL2/L3機能を使っ
    てパケットを処理するようになります。つまり、すべてのパケットをNORMAL
    ポートに出力するように指示するだけで、スイッチングハブとして動作する
    ようにできます(スイッチがNORMALポートをサポートしている場合)が、ここ
    では各々の処理をOpenFlowを使って実現するものとします。


これらの動作を順を追って図とともに説明します。
なお、ここではTable-missフローエントリについては省略しています。


1. 初期状態

    フローテーブルが空の初期状態です。

    ポート1にホストA、ポート4にホストB、ポート3にホストCが接続されているもの
    とします。


    .. image:: images/switching_hub/fig1.png
       :scale: 80 %


2. ホストA→ホストB

    ホストAからホストBへのパケットが送信されると、Packet-Inメッセージが送られ、
    ホストAのMACアドレスがポート1に学習されます。ホストBのポートはまだ分かって
    いないため、パケットはフラッディングされ、パケットはホストBとホストCで受信
    されます。

    .. image:: images/switching_hub/fig2.png
       :scale: 80 %


    Packet-In::

        in-port: 1
        eth-dst: ホストB
        eth-src: ホストA

    Packet-Out::

        action: OUTPUT:フラッディング


3. ホストB→ホストA

    ホストBからホストAにパケットが返されると、フローテーブルにエントリを追加し、
    またパケットはポート1に転送されます。そのため、このパケットはホストCでは
    受信されません。

        .. image:: images/switching_hub/fig3.png
           :scale: 80 %


    Packet-In::

        in-port: 4
        eth-dst: ホストA
        eth-src: ホストB

    Packet-Out::

        action: OUTPUT:ポート1


4. ホストA→ホストB

    再度、ホストAからホストBへのパケットが送信されると、フローテーブルに
    エントリを追加し、またパケットはポート4に転送されます。

        .. image:: images/switching_hub/fig4.png
           :scale: 80 %


    Packet-In::

        in-port: 1
        eth-dst: ホストB
        eth-src: ホストA

    Packet-Out::

        action: OUTPUT:ポート4


次に、実際にRyuを使って実装されたスイッチングハブのソースコードを見ていきます。


Ryuによるスイッチングハブの実装
-------------------------------

スイッチングハブのソースコードは、Ryuのソースツリーにあります。

    ryu/app/simple_switch_13.py

OpenFlowのバージョンに応じて、他にもsimple_switch.py(OpenFlow 1.0)、
simple_switch_12.py(OpenFlow 1.2)がありますが、ここではOpenFlow 1.3に対応した
実装を見ていきます。

短いソースコードなので、全体をここに掲載します。

.. literalinclude:: sources/simple_switch_13.py

それでは、それぞれの実装内容について見ていきます。


クラスの定義と初期化
^^^^^^^^^^^^^^^^^^^^

Ryuアプリケーションとして実装するため、ryu.base.app_manager.RyuAppを
継承します。また、OpenFlow 1.3を使用するため、 ``OFP_VERSIONS`` に
OpenFlow 1.3のバージョンを指定しています。

また、MACアドレステーブル mac_to_port を定義しています。

OpenFlowプロトコルでは、OpenFlowスイッチとコントローラが通信を行うために
必要となるハンドシェイクなどのいくつかの手順が決められていますが、Ryuの
フレームワークが処理してくれるため、Ryuアプリケーションでは意識する必要は
ありません。

::

    class SimpleSwitch13(app_manager.RyuApp):
        OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

        def __init__(self, *args, **kwargs):
            super(SimpleSwitch13, self).__init__(*args, **kwargs)
            self.mac_to_port = {}

        # ...


イベントハンドラ
^^^^^^^^^^^^^^^^

Ryuでは、OpenFlowメッセージを受信するとメッセージに対応したイベントが発生
します。Ryuアプリケーションは、受け取りたいメッセージに対応したイベント
ハンドラを実装します。

イベントハンドラは、引数にイベントオブジェクトを持つ関数を定義し、
``ryu.controller.handler.set_ev_cls`` デコレータで修飾します。

set_ev_clsは、引数に受け取るメッセージに対応したイベントクラスとOpenFlow
スイッチのステートを指定します。

イベントクラス名は、 ``ryu.controller.ofp_event.EventOFP`` + <OpenFlow
メッセージ名>となっています。例えば、Packet-Inメッセージの場合は、
``EventOFPPacketIn`` になります。
詳しくは、Ryuのドキュメント *Ryu application API* を参照してください。
ステートには、以下のいずれか、またはリストを指定します。

.. tabularcolumns:: |l|L|

=========================================== ==================================
定義                                        説明
=========================================== ==================================
ryu.controller.handler.HANDSHAKE_DISPATCHER HELLOメッセージの交換
ryu.controller.handler.CONFIG_DISPATCHER    SwitchFeaturesメッセージの受信待ち
ryu.controller.handler.MAIN_DISPATCHER      通常状態
ryu.controller.handler.DEAD_DISPATCHER      コネクションの切断
=========================================== ==================================


Table-missフローエントリの追加
""""""""""""""""""""""""""""""

OpenFlowスイッチとのハンドシェイク完了後にTable-missフローエントリを
フローテーブルに追加し、Packet-Inメッセージを受信する準備を行います。

具体的には、Switch Features(Features Reply)メッセージを受け取り、そこで
Table-missフローエントリの追加を行います。

::

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # ...

``ev.msg`` には、イベントに対応するOpenFlowメッセージクラスのインスタンスが
格納されています。この場合は、
``ryu.ofproto.ofproto_v1_3_parser.OFPSwitchFeatures`` になります。

``msg.datapath`` には、このメッセージを発行したOpenFlowスイッチに対応する
``ryu.controller.controller.Datapath`` クラスのインスタンスが格納されています。

Datapathクラスは、OpenFlowスイッチとの実際の通信処理や受信メッセージに対応
したイベントの発行などの重要な処理を行っています。

Ryuアプリケーションで利用する主な属性は以下のものです。

.. tabularcolumns:: |l|L|

============== ==============================================================
属性名         説明
============== ==============================================================
id             接続しているOpenFlowスイッチのID(データパスID)です。
ofproto        使用しているOpenFlowバージョンに対応したofprotoモジュールを
               示します。現時点では、以下のいずれかになります。

               ``ryu.ofproto.ofproto_v1_0``

               ``ryu.ofproto.ofproto_v1_2``

               ``ryu.ofproto.ofproto_v1_3``
ofproto_parser ofprotoと同様に、ofproto_parserモジュールを示します。
               現時点では、以下のいずれかになります。

               ``ryu.ofproto.ofproto_v1_0_parser``

               ``ryu.ofproto.ofproto_v1_2_parser``

               ``ryu.ofproto.ofproto_v1_3_parser``
============== ==============================================================

Ryuアプリケーションで利用するDatapathクラスの主なメソッドは以下のものです。

send_msg(msg)

    OpenFlowメッセージを送信します。
    msgは、送信OpenFlowメッセージに対応した
    ``ryu.ofproto.ofproto_parser.MsgBase`` のサブクラスです。


スイッチングハブでは、受信したSwitch Featuresメッセージ自体は特に
使いません。Table-missフローエントリを追加するタイミングを得るための
イベントとして扱っています。

::

    def switch_features_handler(self, ev):
        # ...

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

Table-missフローエントリを作成します。

すべてのパケットにマッチさせるため、空のマッチを生成します。マッチは
``OFPMatch`` クラスで表されます。詳細については後述します。

次に、コントローラポートへ転送するためのOUTPUTアクションクラス(
``OFPActionOutput``)のインスタンスを生成します。

OFPActionOutputクラスは、Packet-OutメッセージやFlow Modメッセージで使用
するパケット転送を指定するものです。コンストラクタの引数で転送先と
コントローラへ送信する最大データサイズ(max_len)を指定します。
転送先には、スイッチの物理的なポート番号の他にいくつかの定義された値が
指定できます。

.. tabularcolumns:: |l|L|

================= ============================================================
値                説明
================= ============================================================
OFPP_IN_PORT      受信ポートに転送されます
OFPP_TABLE        先頭のフローテーブルに摘要されます
OFPP_NORMAL       スイッチのL2/L3機能で転送されます
OFPP_FLOOD        受信ポートやブロックされているポートを除く当該VLAN内の
                  すべての物理ポートにフラッディングされます
OFPP_ALL          受信ポートを除くすべての物理ポートに転送されます
OFPP_CONTROLLER   コントローラにPacket-Inメッセージとして送られます
OFPP_LOCAL        スイッチのローカルポートを示します
OFPP_ANY          Flow Mod(delete)メッセージやFlow Stats Requestsメッセージ
                  でポートを選択する際にワイルドカードとして使用するもので、
                  パケット転送では使用されません
================= ============================================================

max_lenに0を指定すると、Packet-Inメッセージにパケットのバイナリデータは
添付されなくなります。 ``OFPCML_NO_BUFFER`` を指定すると、OpenFlowスイッチ上
でそのパケットをバッファせず、Packet-Inメッセージにパケット全体が添付されます。

.. NOTE::

   max_lenには通常、Packet-Inハンドラ内の処理で必要となるバイト数を指定
   します。OFPCML_NO_BUFFERを指定するとパケット全体が送られるため、パフォー
   マンスが悪くなります。ところが、現時点のOpen vSwitchの実装では、例えば
   max_lenに128を指定した場合、バッファリングせずにパケットの先頭128バイト
   のみを添付したPacket-Inが発行されます。これでは128バイトを越えるサイズの
   パケットが正しく転送できなくなってしまいますので、ここではOFPCML_NO_BUFFER
   を指定してパケット全体を添付するようにしています。


最後に、優先度に0(最低)を指定して ``add_flow()`` メソッドを実行してFlow Mod
メッセージを送信します。add_flow()メソッドの内容については後述します。


Packet-inメッセージ
"""""""""""""""""""

未知の受信パケットを受け付けるため、Packet-Inメッセージを受け取ります。

::

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # ...


OFPPacketInクラスのよく使われる属性には以下のようなものがあります。

.. tabularcolumns:: |l|L|

========= ===================================================================
属性名    説明
========= ===================================================================
match     ``ryu.ofproto.ofproto_v1_3_parser.OFPMatch`` クラスのインスタンス
          で、受信パケットのメタ情報が設定されています。
data      受信パケット自体を示すバイナリデータです。
total_len 受信パケットのデータ長です。
buffer_id 受信パケットがOpenFlowスイッチ上でバッファされている場合、
          そのIDが示されます。バッファされていない場合は、
          ``ryu.ofproto.ofproto_v1_3.OFP_NO_BUFFER`` がセットされます。
========= ===================================================================


MACアドレステーブルの更新
"""""""""""""""""""""""""

::

    def _packet_in_handler(self, ev):
        # ...

        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        # ...

OFPPacketInクラスのmatchから、受信ポート(``in_port``)を取得します。
宛先MACアドレスと送信元MACアドレスは、Ryuのパケットライブラリを使って、
受信パケットのEthernetヘッダから取得しています。

取得した送信元MACアドレスと受信ポート番号で、MACアドレステーブルを更新します。

複数のOpenFlowスイッチとの接続に対応するため、MACアドレステーブルはOpenFlow
スイッチ毎に管理するようになっています。OpenFlowスイッチの識別にはデータパスID
を用いています。


転送先ポートの判定
""""""""""""""""""

宛先MACアドレスが、MACアドレステーブルに存在する場合は対応するポート番号を、
見つからなかった場合はフラッディング(``OFPP_FLOOD``)を出力ポートに指定した
OUTPUTアクションクラスのインスタンスを生成します。

::

    def _packet_in_handler(self, ev):
        # ...

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        # ...


宛先MACアドレスがみつかった場合は、OpenFlowスイッチのフローテーブルに
エントリを追加します。

Table-missフローエントリの追加と同様に、マッチとアクションを指定して
add_flow()を実行し、フローエントリを追加します。

Table-missフローエントリとは違って、今回はマッチに条件を設定します。

指定できる条件には様々なものがあり、OpenFlowのバージョンが上がる度に
その種類は増えています。OpenFlow 1.0では12種類でしたが、OpenFlow 1.3
では40種類もの条件が定義されています。

個々の詳細については、OpenFlowの仕様書などを参照して頂くとして、ここでは
OpenFlow 1.3のMatchフィールドを簡単に紹介します。

================= ==========================================================
Matchフィールド名 説明
================= ==========================================================
in_port           受信ポートのポート番号
in_phy_port       受信ポートの物理ポート番号
metadata          テーブル間で情報を受け渡すために用いられるメタデータ
eth_dst           Ethernetの宛先MACアドレス
eth_src           Ethernetの送信元MACアドレス
eth_type          Ethernetのフレームタイプ
vlan_vid          VLAN ID
vlan_pcp          VLAN PCP
ip_dscp           IP DSCP
ip_ecn            IP ECN
ip_proto          IPのプロトコル種別
ipv4_src          IPv4の送信元IPアドレス
ipv4_dst          IPv4の宛先IPアドレス
tcp_src           TCPの送信元ポート番号
tcp_dst           TCPの宛先ポート番号
udp_src           UDPの送信元ポート番号
udp_dst           UDPの宛先ポート番号
sctp_src          SCTPの送信元ポート番号
sctp_dst          SCTPの宛先ポート番号
icmpv4_type       ICMPのType
icmpv4_code       ICMPのCode
arp_op            ARPのオペコード
arp_spa           ARPの送信元IPアドレス
arp_tpa           ARPのターゲットIPアドレス
arp_sha           ARPの送信元MACアドレス
arp_tha           ARPのターゲットMACアドレス
ipv6_src          IPv6の送信元IPアドレス
ipv6_dst          IPv6の宛先IPアドレス
ipv6_flabel       IPv6のフローラベル
icmpv6_type       ICMPv6のType
icmpv6_code       ICMPv6のCode
ipv6_nd_target    IPv6ネイバーディスカバリのターゲットアドレス
ipv6_nd_sll       IPv6ネイバーディスカバリの送信元リンクレイヤーアドレス
ipv6_nd_tll       IPv6ネイバーディスカバリのターゲットリンクレイヤーアドレス
mpls_label        MPLSのラベル
mpls_tc           MPLSのトラフィッククラス(TC)
mpls_bos          MPLSのBoSビット
pbb_isid          802.1ah PBBのI-SID
tunnel_id         論理ポートに関するメタデータ
ipv6_exthdr       IPv6の拡張ヘッダの擬似フィールド
================= ==========================================================

MACアドレスやIPアドレスなどのフィールドによっては、さらにマスクを指定する
ことができます。

今回のスイッチングハブの実装では、受信ポート(in_port)と宛先MACアドレス
(eth_dst)を指定しています。例えば、「ポート1で受信したホストB宛」のパケット
が対象となります。

今回のフローエントリでは、優先度に1を指定しています。優先度は値が大きい
ほど優先度が高くなるので、ここで追加するフローエントリは、Table-missフロー
エントリより先に評価されるようになります。

前述のアクションを含めてまとめると、以下のようなエントリをフローテーブル
に追加します。

    ポート1で受信した、ホストB宛(宛先MACアドレスがB)のパケットを、
    ポート4に転送する


フローエントリの追加処理
""""""""""""""""""""""""

Packet-Inハンドラの処理がまだ終わっていませんが、ここで一旦フローエントリ
を追加するメソッドの方を見ていきます。

::

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        # ...

フローエントリには、対象となるパケットの条件を示すマッチと、そのパケット
に対する操作を示すインストラクション、エントリの優先度、有効時間などを
設定します。

マッチについては既に説明しました。

インストラクションは、マッチに該当するパケットを受信した時の動作を定義する
もので、 次のタイプが規定されています。

Goto Table (必須)

    OpenFlow 1.1以降では、複数のフローテーブルがサポートされています。Goto 
    Tableによって、マッチしたパケットの処理を、指定したフローテーブルに引き
    継ぐことができます。例えば、「ポート1で受信したパケットにVLAN-ID 200を
    付加して、テーブル2へ飛ぶ」といったフローエントリが設定できます。

    指定するテーブルIDは、現在のテーブルIDより大きい値でなければなりません。

Write Metadata (オプション)

    以降のテーブルで参照できるメタデータをセットします。

Write Actions (必須)

    現在のアクションセットに指定されたアクションを追加します。同じタイプの
    アクションが既にセットされていた場合には、新しいアクションで置き換えら
    れます。

Apply Actions (オプション)

    アクションセットは変更せず、指定されたアクションを直ちに適用します。

Clear Actions (オプション)

    現在のアクションセットのすべてのアクションを削除します。

Meter (オプション)

    指定したメーターにパケットを適用します。


Ryuでは、各インストラクションに対応する次のクラスが実装されています。

* ``OFPInstructionGotoTable``
* ``OFPInstructionWriteMetadata`` 
* ``OFPInstructionActions``
* ``OFPInstructionMeter``

Write/Apply/Clear Actionsは、OPFInstructionActionsにまとめられていて、
インスタンス生成時に選択します。

スイッチングハブの実装では、Apply Actionsを使用して、指定したアクションを
直ちに適用するように設定しています。

.. NOTE::

   Write Actionsのサポートは必須とされていますが、現時点のOpen vSwitch
   ではサポートされていません。Apply Actionsがサポートされているので、
   代わりにこちらを使う必要があります。


最後に、Flow Modメッセージを発行してフローテーブルにエントリを追加します。

::

    def add_flow(self, datapath, port, dst, actions):
        # ...

        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

Flow Modメッセージに対応するクラスは ``OFPFlowMod`` クラスです。OFPFlowMod
クラスのインスタンスを生成して、Datapath.send_msg() メソッドでOpenFlow
スイッチにメッセージを送信します。

OFPFlowModクラスのコンストラクタには多くの引数がありますが、多くのものは
大抵の場合、デフォルト値のままで済みます。かっこ内はデフォルト値です。

datapath

    フローテーブルを操作する対象となるOpenFlowスイッチに対応するDatapath
    クラスのインスタンスです。通常は、Packet-Inメッセージなどのハンドラ
    に渡されるイベントから取得したものを指定します。

cookie (0)

    コントローラが指定する任意の値で、エントリの更新または削除を行う際の
    フィルタ条件として使用できます。パケットの処理では使用されません。

cookie_mask (0)

    エントリの更新または削除の場合に、0以外の値を指定すると、エントリの
    cookie値による操作対象エントリのフィルタとして使用されます。

table_id (0)

    操作対象のフローテーブルのテーブルIDを指定します。

command (ofproto_v1_3.OFPFC_ADD)

    どのような操作を行うかを指定します。

    ==================== ========================================
    値                   説明
    ==================== ========================================
    OFPFC_ADD            新しいフローエントリを追加します
    OFPFC_MODIFY         フローエントリを更新します
    OFPFC_MODIFY_STRICT  厳格に一致するフローエントリを更新します
    OFPFC_DELETE         フローエントリを削除します
    OFPFC_DELETE_STRICT  厳格に一致するフローエントリを更新します
    ==================== ========================================

idle_timeout (0)

    このエントリの有効期限を秒単位で指定します。エントリが参照されずに
    idle_timeoutで指定した時間を過ぎた場合、そのエントリは削除されます。
    エントリが参照されると経過時間はリセットされます。

    エントリが削除されるとFlow Removedメッセージがコントローラに通知され
    ます。

hard_timeout (0)

    このエントリの有効期限を秒単位で指定します。idle_timeoutと違って、
    hard_timeoutでは、エントリが参照されても経過時間はリセットされません。
    つまり、エントリの参照の有無に関わらず、指定された時間が経過すると
    エントリが削除されます。

    idle_timeoutと同様に、エントリが削除されるとFlow Removedメッセージが
    通知されます。

priority (0)

    このエントリの優先度を指定します。
    値が大きいほど、優先度も高くなります。

buffer_id (ofproto_v1_3.OFP_NO_BUFFER)

    OpenFlowスイッチ上でバッファされたパケットのバッファIDを指定します。
    バッファIDはPacket-Inメッセージで通知されたものであり、指定すると
    OFPP_TABLEを出力ポートに指定したPacket-OutメッセージとFlow Modメッセージ
    の2つのメッセージを送ったのと同じように処理されます。
    commandがOFPFC_DELETEまたはOFPFC_DELETE_STRICTの場合は無視されます。

    バッファIDを指定しない場合は、 ``OFP_NO_BUFFER`` をセットします。

out_port (0)

    OFPFC_DELETEまたはOFPFC_DELETE_STRICTの場合に、対象となるエントリを
    出力ポートでフィルタします。OFPFC_ADD、OFPFC_MODIFY、OFPFC_MODIFY_STRICT
    の場合は無視されます。

    出力ポートでのフィルタを無効にするには、 ``OFPP_ANY`` を指定します。

out_group (0)

    out_portと同様に、出力グループでフィルタします。

    無効にするには、 ``OFPG_ANY`` を指定します。

flags (0)

    以下のフラグの組み合わせを指定することができます。

    .. tabularcolumns:: |l|L|

    ===================== ===================================================
    値                    説明
    ===================== ===================================================
    OFPFF_SEND_FLOW_REM   このエントリが削除された時に、コントローラにFlow
                          Removedメッセージを発行します。
    OFPFF_CHECK_OVERLAP   OFPFC_ADDの場合に、重複するエントリのチェックを行い
                          ます。重複するエントリがあった場合にはFlow Modは失
                          敗し、エラーが返されます。
    OFPFF_RESET_COUNTS    該当エントリのパケットカウンタとバイトカウンタを
                          リセットします。
    OFPFF_NO_PKT_COUNTS   このエントリのパケットカウンタを無効にします。
    OFPFF_NO_BYT_COUNTS   このエントリのバイトカウンタを無効にします。
    ===================== ===================================================

match (None)

    マッチを指定します。

instructions ([])

    インストラクションのリストを指定します。


パケットの転送
""""""""""""""

Packet-Inハンドラに戻り、最後の処理の説明です。

宛先MACアドレスがMACアドレステーブルから見つかったかどうかに関わらず、最終的
にはPacket-Outメッセージを発行して、受信パケットを転送します。

::

    def _packet_in_handler(self, ev):
        # ...

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

Packet-Outメッセージに対応するクラスは ``OFPPacketOut`` クラスです。

OFPPacketOutのコンストラクタの引数は以下のようになっています。

datapath

    OpenFlowスイッチに対応するDatapathクラスのインスタンスを指定します。

buffer_id   

    OpenFlowスイッチ上でバッファされたパケットのバッファIDを指定します。
    バッファを使用しない場合は、 ``OFP_NO_BUFFER`` を指定します。

in_port

    パケットを受信したポートを指定します。受信パケットでない場合は、
    ``OFPP_CONTROLLER`` を指定します。

actions

    アクションのリストを指定します。

data

    パケットのバイナリデータを指定します。buffer_idに ``OFP_NO_BUFFER``
    が指定された場合に使用されます。OpenFlowスイッチのバッファを利用す
    る場合は省略します。


スイッチングハブの実装では、buffer_idにPacket-Inメッセージのbuffer_idを
指定しています。Packet-Inメッセージのbuffer_idが無効だった場合は、
Packet-Inの受信パケットをdataに指定して、パケットを送信しています。


これで、スイッチングハブのソースコードの説明は終わりです。
次は、このスイッチングハブを実行して、実際の動作を確認します。


Ryuアプリケーションの実行
-------------------------

スイッチングハブの実行のため、OpenFlowスイッチにはOpen vSwitch、実行
環境としてmininetを使います。

Ryu用のOpenFlow Tutorial VMイメージが用意されているので、このVMイメージ
を利用すると実験環境を簡単に準備することができます。

VMイメージ

    http://sourceforge.net/projects/ryu/files/vmimages/OpenFlowTutorial/

    OpenFlow_Tutorial_Ryu3.2.ova (約1.4GB)

関連ドキュメント(Wikiページ)

    https://github.com/osrg/ryu/wiki/OpenFlow_Tutorial

ドキュメントにあるVMイメージは、Open vSwitchとRyuのバージョンが古いため
ご注意ください。


このVMイメージを使わず、自分で環境を構築することも当然できます。VMイメージ
で使用している各ソフトウェアのバージョンは以下の通りですので、自身で構築
する場合は参考にしてください。

Mininet VM バージョン2.0.0
  http://mininet.org/download/

Open vSwitch バージョン1.11.0
  http://openvswitch.org/download/

Ryu バージョン3.2
  https://github.com/osrg/ryu/

::

    $ sudo pip install ryu

ここでは、Ryu用OpenFlow TutorialのVMイメージを利用します。

Mininetの実行
^^^^^^^^^^^^^

mininetからxtermを起動するため、Xが使える環境が必要です。

ここでは、OpenFlow TutorialのVMを利用しているため、デスクトップPCから
sshでX11 Forwardingを有効にしてログインします。

::

    $ ssh -X ryu@<VMのアドレス>

ユーザー名は ``ryu`` 、パスワードも ``ryu`` です。


ログインできたら、 ``mn`` コマンドによりMininet環境を起動します。

構築する環境は、ホスト3台、スイッチ1台のシンプルな構成です。

mnコマンドのパラメータは、以下のようになります。

============ ========== ===========================================
パラメータ   値         説明
============ ========== ===========================================
topo         single,3   スイッチが1台、ホストが3台のトポロジ
mac          なし       自動的にホストのMACアドレスをセットする
switch       ovsk       Open vSwitchを使用する
controller   remote     OpenFlowコントローラは外部のものを利用する
x            なし       xtermを起動する
============ ========== ===========================================

実行例は以下のようになります。

.. line-block::

    $ sudo mn --topo single,3 --mac --switch ovsk --controller remote -x
    *** Creating network
    *** Adding controller
    Unable to contact the remote controller at 127.0.0.1:6633
    *** Adding hosts:
    h1 h2 h3 
    *** Adding switches:
    s1 
    *** Adding links:
    (h1, s1) (h2, s1) (h3, s1) 
    *** Configuring hosts
    h1 h2 h3 
    *** Running terms on localhost:10.0
    *** Starting controller
    *** Starting 1 switches
    s1 
    *** Starting CLI:
    mininet> 

実行するとデスクトップPC上でxtermが5つ起動します。
それぞれ、ホスト1～3、スイッチ、コントローラに対応します。

スイッチのxtermからコマンドを実行して、使用するOpenFlowのバージョンを
セットします。ウインドウタイトルが「switch: s1 (root)」となっている
ものがスイッチ用のxtermです。

まずはOpen vSwitchの状態を見てみます。

switch: s1:

    .. line-block::

        root@ryu-vm:~# ovs-vsctl show
        fdec0957-12b6-4417-9d02-847654e9cc1f
        Bridge "s1"
            Controller "ptcp:6634"
            Controller "tcp:127.0.0.1:6633"
            fail_mode: secure
            Port "s1-eth3"
                Interface "s1-eth3"
            Port "s1-eth2"
                Interface "s1-eth2"
            Port "s1-eth1"
                Interface "s1-eth1"
            Port "s1"
                Interface "s1"
                    type: internal
        ovs_version: "1.11.0"
        root@ryu-vm:~# ovs-dpctl show
        system@ovs-system:
                lookups: hit:14 missed:14 lost:0
                flows: 0
                port 0: ovs-system (internal)
                port 1: s1 (internal)
                port 2: s1-eth1
                port 3: s1-eth2
                port 4: s1-eth3
        root@ryu-vm:~#

スイッチ(ブリッジ) *s1* ができていて、ホストに対応するポートが
3つ追加されています。

次にOpenFlowのバージョンとして1.3を設定します。

switch: s1:

    .. line-block::

        root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13
        root@ryu-vm:~# 

空のフローテーブルを確認してみます。

switch: s1:

    .. line-block::

        root@ryu-vm:~# ovs-ofctl -O OpenFlow13 dump-flows s1
        OFPST_FLOW reply (OF1.3) (xid=0x2):
        root@ryu-vm:~# 

ovs-ofctlコマンドには、オプションで使用するOpenFlowのバージョンを
指定する必要があります。デフォルトは *OpenFlow10* です。


スイッチングハブの実行
^^^^^^^^^^^^^^^^^^^^^^

準備が整ったので、Ryuアプリケーションを実行します。

ウインドウタイトルが「controller: c0 (root)」となっているxtermから
次のコマンドを実行します。

controller: c0:

    .. line-block::

        root@ryu-vm:~# ryu-manager --verbose ryu.app.simple_switch_13
        loading app ryu.app.simple_switch_13
        loading app ryu.controller.ofp_handler
        instantiating app ryu.app.simple_switch_13
        instantiating app ryu.controller.ofp_handler
        BRICK SimpleSwitch13
          CONSUMES EventOFPSwitchFeatures
          CONSUMES EventOFPPacketIn
        BRICK ofp_event
          PROVIDES EventOFPSwitchFeatures TO {'SimpleSwitch13': set(['config'])}
          PROVIDES EventOFPPacketIn TO {'SimpleSwitch13': set(['main'])}
          CONSUMES EventOFPErrorMsg
          CONSUMES EventOFPHello
          CONSUMES EventOFPEchoRequest
          CONSUMES EventOFPPortDescStatsReply
          CONSUMES EventOFPSwitchFeatures
        connected socket:<eventlet.greenio.GreenSocket object at 0x2e2c050> address:('127.0.0.1', 53937)
        hello ev <ryu.controller.ofp_event.EventOFPHello object at 0x2e2a550>
        move onto config mode
        EVENT ofp_event->SimpleSwitch13 EventOFPSwitchFeatures
        switch features ev version: 0x4 msg_type 0x6 xid 0xff9ad15b OFPSwitchFeatures(auxiliary_id=0,capabilities=71,datapath_id=1,n_buffers=256,n_tables=254)
        move onto main mode
    
OVSとの接続に時間がかかる場合がありますが、少し待つと上のように

::

    connected socket:<....
    hello ev ...
    ...
    move onto main mode

と表示されます。

これで、OVSと接続し、ハンドシェイクが行われ、Table-missフローエントリが
追加され、Packet-Inを待っている状態になっています。

Table-missフローエントリが追加されていることを確認します。

switch: s1:

    .. line-block::

        root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
        OFPST_FLOW reply (OF1.3) (xid=0x2):
         cookie=0x0, duration=105.975s, table=0, n_packets=0, n_bytes=0, priority=0 actions=CONTROLLER:65535
        root@ryu-vm:~# 

優先度が0で、マッチがなく、アクションにCONTROLLER、送信データサイズ65535
(0xffff = OFPCML_NO_BUFFER)が指定されています。


動作の確認
^^^^^^^^^^

ホスト1からホスト2へpingを実行します。

1. ARP request

    この時点では、ホスト1はホスト2のMACアドレスを知らないので、ICMP echo
    requestに先んじてARP requestをブロードキャストするはずです。
    このブロードキャストパケットはホスト2とホスト3で受信されます。

2. ARP reply

    ホスト2がARPに応答して、ホスト1にARP replyを返します。

3. ICMP echo request

    これでホスト1はホスト2のMACアドレスを知ることができたので、echo request
    をホスト2に送信します。

4. ICMP echo reply

    ホスト2はホスト1のMACアドレスを既に知っているので、echo replyをホスト1
    に返します。

このような通信が行われるはずです。

pingコマンドを実行する前に、各ホストでどのようなパケットを受信したかを確認
できるようにtcpdumpコマンドを実行しておきます。

host: h1:

    .. line-block::

        root@ryu-vm:~# tcpdump -en -i h1-eth0
        tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
        listening on h1-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes

host: h2:

    .. line-block::

        root@ryu-vm:~# tcpdump -en -i h2-eth0
        tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
        listening on h2-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes

host: h3:

    .. line-block::

        root@ryu-vm:~# tcpdump -en -i h3-eth0
        tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
        listening on h3-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes


それでは、最初にmnコマンドを実行したコンソールで、次のコマンドを実行して
ホスト1からホスト2へpingを発行します。

.. line-block::

    mininet> h1 ping -c1 h2
    PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
    64 bytes from 10.0.0.2: icmp_req=1 ttl=64 time=97.5 ms
    
    --- 10.0.0.2 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 97.594/97.594/97.594/0.000 ms
    mininet> 


ICMP echo replyは正常に返ってきました。

まずはフローテーブルを確認してみましょう。

switch: s1:

    .. line-block::

        root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
        OFPST_FLOW reply (OF1.3) (xid=0x2):
         cookie=0x0, duration=417.838s, table=0, n_packets=3, n_bytes=182, priority=0 actions=CONTROLLER:65535
         cookie=0x0, duration=48.444s, table=0, n_packets=2, n_bytes=140, priority=1,in_port=2,dl_dst=00:00:00:00:00:01 actions=output:1
         cookie=0x0, duration=48.402s, table=0, n_packets=1, n_bytes=42, priority=1,in_port=1,dl_dst=00:00:00:00:00:02 actions=output:2
        root@ryu-vm:~# 

Table-missフローエントリ以外に、優先度が1のフローエントリが2つ登録されて
います。

(1) 受信ポート(in_port):2, 宛先MACアドレス(dl_dst):ホスト1 →  
    動作(actions):ポート1に転送
(2) 受信ポート(in_port):1, 宛先MACアドレス(dl_dst):ホスト2 →  
    動作(actions):ポート2に転送

(1)のエントリは2回参照され(n_packets)、(2)のエントリは1回参照されています。
(1)はホスト2からホスト1宛の通信なので、ARP replyとICMP echo replyの2つが
マッチしたものでしょう。
(2)はホスト1からホスト2宛の通信で、ARP requestはブロードキャストされるので、
これはICMP echo requestによるもののはずです。


それでは、simple_switch_13のログ出力を見てみます。

controller: c0:

    .. line-block::

        EVENT ofp_event->SimpleSwitch13 EventOFPPacketIn
        packet in 1 00:00:00:00:00:01 ff:ff:ff:ff:ff:ff 1
        EVENT ofp_event->SimpleSwitch13 EventOFPPacketIn
        packet in 1 00:00:00:00:00:02 00:00:00:00:00:01 2
        EVENT ofp_event->SimpleSwitch13 EventOFPPacketIn
        packet in 1 00:00:00:00:00:01 00:00:00:00:00:02 1


1つ目のPacket-Inは、ホスト1が発行したARP requestで、ブロードキャストなので
フローエントリは登録されず、Packet-Outのみが発行されます。

2つ目は、ホスト2から返されたARP replyで、宛先MACアドレスがホスト1となって
いるので前述のフローエントリ(1)が登録されます。

3つ目は、ホスト1からホスト2へ送信されたICMP echo requestで、フローエントリ
(2)が登録されます。

ホスト2からホスト1に返されたICMP echo replyは、登録済みのフローエントリ(1)
にマッチするため、Packet-Inは発行されずにホスト1へ転送されます。


最後に各ホストで実行したtcpdumpの出力を見てみます。

host: h1:

    .. line-block::

        root@ryu-vm:~# tcpdump -en -i h1-eth0
        tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
        listening on h1-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes
        20:38:04.625473 00:00:00:00:00:01 > ff:ff:ff:ff:ff:ff, ethertype ARP (0x0806), length 42: Request who-has 10.0.0.2 tell 10.0.0.1, length 28
        20:38:04.678698 00:00:00:00:00:02 > 00:00:00:00:00:01, ethertype ARP (0x0806), length 42: Reply 10.0.0.2 is-at 00:00:00:00:00:02, length 28
        20:38:04.678731 00:00:00:00:00:01 > 00:00:00:00:00:02, ethertype IPv4 (0x0800), length 98: 10.0.0.1 > 10.0.0.2: ICMP echo request, id 3940, seq 1, length 64
        20:38:04.722973 00:00:00:00:00:02 > 00:00:00:00:00:01, ethertype IPv4 (0x0800), length 98: 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 3940, seq 1, length 64


ホスト1では、最初にARP requestがブロードキャストされていて、続いてホスト2から
返されたARP replyを受信しています。
次にホスト1が発行したICMP echo request、ホスト2から返されたICMP echo replyが
受信されています。


host: h2:

    .. line-block::

        root@ryu-vm:~# tcpdump -en -i h2-eth0
        tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
        listening on h2-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes
        20:38:04.637987 00:00:00:00:00:01 > ff:ff:ff:ff:ff:ff, ethertype ARP (0x0806), length 42: Request who-has 10.0.0.2 tell 10.0.0.1, length 28
        20:38:04.638059 00:00:00:00:00:02 > 00:00:00:00:00:01, ethertype ARP (0x0806), length 42: Reply 10.0.0.2 is-at 00:00:00:00:00:02, length 28
        20:38:04.722601 00:00:00:00:00:01 > 00:00:00:00:00:02, ethertype IPv4 (0x0800), length 98: 10.0.0.1 > 10.0.0.2: ICMP echo request, id 3940, seq 1, length 64
        20:38:04.722747 00:00:00:00:00:02 > 00:00:00:00:00:01, ethertype IPv4 (0x0800), length 98: 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 3940, seq 1, length 64


ホスト2では、ホスト1が発行したARP requestを受信し、ホスト1にARP replyを
返しています。続いて、ホスト1からのICMP echo requestを受信し、ホスト1に
echo replyを返しています。

host: h3:

    .. line-block::

        root@ryu-vm:~# tcpdump -en -i h3-eth0
        tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
        listening on h3-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes
        20:38:04.637954 00:00:00:00:00:01 > ff:ff:ff:ff:ff:ff, ethertype ARP (0x0806), length 42: Request who-has 10.0.0.2 tell 10.0.0.1, length 28
    

ホスト3では、最初にホスト1がブロードキャストしたARP requestのみを受信
しています。



まとめ
------

本章では、簡単なスイッチングハブの実装を題材に、Ryuアプリケーションの実装
の基本的な手順と、OpenFlowによるOpenFlowスイッチの簡単な制御方法について
説明しました。

