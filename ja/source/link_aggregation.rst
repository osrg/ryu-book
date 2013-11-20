.. _ch_link_aggregation:

リンク・アグリゲーションの実装
==============================

本章では、「 :ref:`ch_switching_hub` 」のスイッチングハブに簡単なリンク・
アグリゲーション機能を追加します。


リンク・アグリゲーション
------------------------

リンク・アグリゲーションは、IEEE802.1AX-2008で規定されている、複数の物理的な
回線を束ねてひとつの論理的なリンクとして扱う技術です。リンク・アグリゲーション
機能により、特定のネットワーク機器間の通信速度を向上させることができ、また同時
に、冗長性を確保することで耐障害性を向上させることができます。

.. only:: latex

   +---------------------------------------------+---------------------------------------------+
   | .. image:: images/link_aggregation/fig1.eps | .. image:: images/link_aggregation/fig2.eps |
   +---------------------------------------------+---------------------------------------------+

.. only:: not latex

   +---------------------------------------------+---------------------------------------------+
   | .. image:: images/link_aggregation/fig1.png | .. image:: images/link_aggregation/fig2.png |
   |    :scale: 40%                              |    :scale: 40%                              |
   +---------------------------------------------+---------------------------------------------+

リンク・アグリゲーション機能を使用するには、それぞれのネットワーク機器において、
どのインターフェースをどのグループとして束ねるのかという設定を事前に行っておく
必要があります。

リンク・アグリゲーション機能を開始する方法には、それぞれのネットワーク機器に
対し直接指示を行うスタティックな方法と、LACP
(Link Aggregation Control Protocol)というプロトコルを使用することによって
動的に開始させるダイナミックな方法があります。

ダイナミックな方法を採用した場合、各ネットワーク機器は対向インターフェース同
士でLACPデータユニットを定期的に交換することにより、疎通不可能になっていない
ことをお互いに確認し続けます。この方法には、ネットワーク機器間にメディアコン
バータなどの中継装置が存在した場合にも、中継装置の向こう側のリンクダウンを検
知することができるというメリットがあります。本章では、LACPを用いたダイナミッ
クなリンク・アグリゲーション機能を実装していきます。


実装するリンク・アグリゲーション機能の整理
------------------------------------------

LACPを用いたリンク・アグリゲーションの仕組みは、簡単に言うと以下のようなもの
です。

* 物理インターフェースのMACアドレスとは別に、束ねられた論理インターフェース
  のMACアドレスを用意します(物理インターフェースのMACアドレスのうちのどれか
  ひとつである場合もあります)。
* LACPデータユニットには論理インターフェースを表すMACアドレスが記載されてお
  り、LACPデータユニット以外のフレーム転送には、この論理インターフェースの
  MACアドレスを使用します。
* LACPデータユニットの交換には個々の物理インターフェースのMACアドレスを使用
  します。
* LACPデータユニットを交換する物理インターフェースは、その役割によってACTIVE
  とPASSIVEに分類されます。ACTIVEは一定時間ごとにLACPデータユニットを送信し、
  疎通を能動的に確認します。PASSIVEはACTIVEから送信されたLACPデータユニット
  を受信した際に応答を返すことにより、疎通を受動的に確認します。
* LACPデータユニットの交換に成功した場合、リンク・アグリゲーションを開始しま
  す。リンク・アグリゲーション実行中、論理インターフェース間を通過するパケッ
  トは、特定の振り分けロジックに従い、いずれかの物理インターフェースから送
  信されます(振り分けロジックに関しては仕様で定められていません)。
* リンク・アグリゲーション開始後も、LACPデータユニットを定期的に交換します。
  一定時間交換が途絶えたら、そのリンクには問題が発生したものとみなし、パケッ
  ト転送での使用を中止します。交換が再開されたら、そのリンクは復旧したものと
  みなし、パケット転送での使用を再開します。

OpenFlowスイッチとOpenFlowコントローラで、リンク・アグリゲーション機能を以下
のように実現することにします。実装を簡素化するためにいくつか制限を設けてあり
ます。

* LACPデータユニットを交換するインターフェースはPASSIVEのみ実装するものとし
  ます。これにより、定期送信のためのタイマー処理が不要となります。
* OpenFlowスイッチは、LACPデータユニットを受信した際、応答用のLACPデータユ
  ニットを送信します。この動作はOpenFlowスイッチ単体では実現できないので、
  OpenFlowスイッチにはLACPデータユニット受信時にPacket-Inを送信するフローエ
  ントリを登録し、応答用のLACPデータユニットの作成はOpenFlowコントローラで行
  い、Packet-Outで送信します。
* LACPデータユニットをPacket-Inさせるフローエントリにはidle_timeoutを設定
  し、一定時間LACPデータユニットを受信しなかった場合にFlowRemovedメッセージ
  がOpenFlowコントローラに飛ぶようにします。
* OpenFlowコントローラは、FlowRemovedメッセージを受信した際、どの物理イン
  ターフェースでLACPデータユニットの交換が停止したかを識別し、その物理イン
  ターフェースが所属している論理インターフェースに関連するすべてのフローエン
  トリを削除します。また、LACPデータユニットの交換が再開された際にも、当該論
  理インターフェースに関連するすべてのフローエントリを削除します。これは、選
  択可能な物理インターフェースの個数が増減したことに伴う再振り分けを想定した
  処理です。
* 振り分けロジックは実装しません。対向インターフェースが振り分けた経路をその
  まま使用するものとします。
* LACP以外のパケットは通常のスイッチングハブ機能で処理します。


LACPライブラリの実装
--------------------

前章で整理した機能の大部分を実装したLACPライブラリが、Ryuのソースツリーにあ
ります。

    ryu/lib/lacplib.py

.. ATTENTION::

    Ryu3.2に含まれているlacplib.pyには不具合があります。Ryu3.3以降をご利用
    ください。

以降の節で、各機能が具体的にどのように実装されているかを見ていきます。なお、
引用されているソースは抜粋です。全体像については実際のソースをご参照ください。


論理インターフェースの作成
^^^^^^^^^^^^^^^^^^^^^^^^^^

前述のとおり、リンク・アグリゲーション機能を使用するには、どのネットワーク
機器においてどのインターフェースをどのグループとして束ねるのかという設定を事
前に行っておく必要があります。RyuのLACPライブラリでは、以下のメソッドでこの
設定を行います。

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
^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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


リンク・アグリゲーション機能搭載スイッチングハブの実装
------------------------------------------------------

前章で説明したLACPライブラリを使用してリンク・アグリゲーション機能を実装した
スイッチングハブのソースコードが、Ryuのソースツリーにあります。

    ryu/app/simple_switch_lacp.py

ただし、上記のソースはOpenFlow 1.0用であるため、新たにOpenFlow 1.3に対応した
実装を作成することにします。

ソース名： ``simple_switch_lacp_13.py``

.. rst-class:: sourcecode

.. literalinclude:: sources/simple_switch_lacp_13.py

これより、「 :ref:`ch_switching_hub` 」のスイッチングハブとの差異を順に説明
していきます。


「_CONTEXTS」の設定
^^^^^^^^^^^^^^^^^^^

ryu.base.app_manager.RyuAppを継承したRyuアプリケーションは、「_CONTEXTS」
ディクショナリに他のRyuアプリケーションを設定することにより、他のアプリケー
ションを別スレッドで起動させることができます。ここではryu.lib.lacplib
モジュールのLacpLibクラスを「lacplib」という名前で「_CONTEXTS」に設定してい
ます。

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
^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

前章で説明したとおり、LACPライブラリはLACPデータユニットの含まれないPacket-In
メッセージを ``EventPacketIn`` というユーザ定義イベントとして送信します。
ユーザ定義イベントのイベントハンドラも、Ryuが提供するイベントハンドラと同じ
ように ``ryu.controller.handler.set_ev_cls`` デコレータで装飾します。

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

「 `実装するリンク・アグリゲーション機能の整理`_ 」で整理したとおり、ポート
の有効/無効状態が変更され、パケットの転送に使用可能な物理インターフェースの
個数が増減すると、論理インターフェースを通過するパケットが実際に使用する物理
インターフェースが変更になる可能性があります。パケットの経路が変更される場合、
すでに登録されているフローエントリを削除し、新たにフローエントリを登録する必
要があります。この例では処理を簡略化するため、「ポートの有効/無効状態が変更
された場合、当該OpenFlowスイッチの全学習結果を削除する」という実装となって
います。

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


リンク・アグリゲーション機能搭載スイッチングハブの実行
------------------------------------------------------

実際に、リンク・アグリゲーション機能搭載スイッチングハブを実行してみます。
最初に「 :ref:`ch_switching_hub` 」と同様にMininetを実行しますが、下図の
ようにトポロジが特殊なため、mnコマンドで作成することができません。

    .. only:: latex

       .. image:: images/link_aggregation/fig3.eps
          :scale: 80 %

    .. only:: not latex

       .. image:: images/link_aggregation/fig3.png
          :scale: 80 %

以降の節で、環境構築からリンク・アグリゲーション機能搭載スイッチングハブの実
行までの手順を説明します。


トポロジ構築スクリプトの実行
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

mnコマンドで構築できるトポロジでは、特定ノード間にはひとつのリンクしか作成で
きません。ここではMininetの低位クラスを直接使用するスクリプトを作成し、トポ
ロジを作成することにします。

ソース名： ``link_aggregation.py``

.. rst-class:: sourcecode

.. literalinclude:: sources/link_aggregation.py

このプログラムを実行することにより、ホストh1とスイッチs1の間に2本のリンクが
存在するトポロジが作成されます。netコマンドを実行することでトポロジを確認す
ることができます。

.. rst-class:: console

::

    ryu@ryu-vm:~$ sudo ./link_aggregation.py
    Unable to contact the remote controller at 127.0.0.1:6633
    mininet> net
    c1
    s1 lo:  s1-eth1:h1-eth0 s1-eth2:h1-eth1 s1-eth3:h2-eth0 s1-eth4:h3-eth0 s1-eth5:h4-eth0
    h1 h1-eth0:s1-eth1 h1-eth1:s1-eth2
    h2 h2-eth0:s1-eth3
    h3 h3-eth0:s1-eth4
    h4 h4-eth0:s1-eth5
    mininet>


ホストh1でのリンク・アグリゲーションの設定
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

前節のコマンドを実行すると、ホストh1～h4およびスイッチs1のxtermが起動します。
ホストh1のxtermで、ホスト側のリンク・アグリゲーションの設定を行います。本節
でのコマンド入力は、すべてホストh1のxterm上で行ってください。

まず、リンク・アグリゲーションを行うためのドライバモジュールをロードします。
Linuxではリンク・アグリゲーション機能はボンディングドライバが担当しています。
事前にドライバの設定ファイルを/etc/modprobe.d/bonding.confとして作成してお
きます。

ファイル名: ``/etc/modprobe.d/bonding.conf``

.. rst-class:: sourcecode

::

    alias bond0 bonding
    options bonding mode=4

.. rst-class:: console

::

    root@ryu-vm:~# modprobe bonding

続いて、bond0という名前の論理インターフェースを新たに作成します。

.. rst-class:: console

::

    root@ryu-vm:~# ip link add bond0 type bond

作成した論理インターフェースのグループに、h1-eth0とh1-eth1の物理インター
フェースを参加させます。このとき、物理インターフェースをダウンさせておく必要
があります。

.. rst-class:: console

::

    root@ryu-vm:~# ip link set h1-eth0 down
    root@ryu-vm:~# ip link set h1-eth0 master bond0
    root@ryu-vm:~# ip link set h1-eth1 down
    root@ryu-vm:~# ip link set h1-eth1 master bond0

論理インターフェースにIPアドレスを割り当てます。mnコマンドでホストを作成した
場合にならって、10.0.0.1を割り当てることにします。

.. rst-class:: console

::

    root@ryu-vm:~# ip addr add 10.0.0.1/24 dev bond0

最後に、論理インターフェースをアップさせます。

.. rst-class:: console

::

    root@ryu-vm:~# ip link set bond0 up


OpenFlowバージョンの設定
^^^^^^^^^^^^^^^^^^^^^^^^

「 :ref:`ch_switching_hub` 」で行ったのと同じように、使用するOpenFlowの
バージョンを1.3に設定します。このコマンド入力は、スイッチs1のxterm上で行っ
てください。

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13

スイッチングハブの実行
^^^^^^^^^^^^^^^^^^^^^^

準備が整ったので、Ryuアプリケーションを実行します。

.. CAUTION::

    TODO: 以下の内容を書いていく。

    * 起動方法
    * 動作確認方法の説明


まとめ
------

本章では、リンク・アグリゲーションライブラリの利用を題材として、以下の項目に
ついて説明しました。

* 「_CONTEXTS」を用いたライブラリの使用方法
* ユーザ定義イベントの定義方法とイベントトリガーの発生方法
