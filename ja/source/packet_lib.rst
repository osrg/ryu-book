Ryu パケットライブラリ
======================

OpenFlowのPacket-InやPacket-Outメッセージには、生のパケット内容
をあらわすバイト列が入るフィールドがあります。
Ryuには、このような生のパケットをアプリケーションから扱いやすく
するためのライブラリが用意されています。
本章はこのライブラリについて紹介します。

.. NOTE::
    OpenFlow 1.2以降では、Packet-Inメッセージのmatchフィールドから、
    パース済みのパケットヘッダーの内容を取得できる場合があります。
    ただし、このフィールドにどれだけの情報を入れてくれるかは、スイッチの
    実装によります。
    例えばOpen vSwitchは最低限の情報しか入れてくれませんので、
    多くの場合コントローラー側でパケット内容を解析する必要があります。
    一方LINCは可能な限り多くの情報を入れてくれます。

基本的な使い方
--------------

プロトコルヘッダクラス
^^^^^^^^^^^^^^^^^^^^^^

Ryuパケットライブラリには、色々なプロトコルヘッダに対応するクラス
が用意されています。

以下のものを含むプロトコルがサポートされています。
各プロトコルに対応するクラスなどの詳細はAPIリファレンスをご参照ください。

- arp
- bgp
- bpdu
- dhcp
- ethernet
- icmp
- icmpv6
- igmp
- ipv4
- ipv6
- llc
- lldp
- mpls
- pbb
- sctp
- slow
- tcp
- udp
- vlan
- vrrp

各プロトコルヘッダクラスの__init__引数名は、基本的にはRFCなどで
使用されている名前と同じになっています。
プロトコルヘッダクラスのインスタンス属性の命名規則も同様です。
ただし、typeなど、Python built-inと衝突する名前のフィールドに対応する
__init__引数名には、type_のように最後に_が付きます。

いくつかの__init__引数にはデフォルト値が設定されており省略できます。
以下の例ではversion=4等が省略されています。

.. raw:: latex

    \begin{sourcecode}
        from ryu.lib.ofproto import inet
        from ryu.lib.packet import ipv4

        pkt_ipv4 = ipv4.ipv4(dst='192.0.2.1',
                             src='192.0.2.2',
                             proto=inet.IPPROTO_UDP)
    \end{sourcecode}

.. raw:: latex

    \begin{sourcecode}
        print pkt_ipv4.dst
        print pkt_ipv4.src
        print pkt_ipvr.proto
    \end{sourcecode}

ネットワークアドレス
^^^^^^^^^^^^^^^^^^^^

RyuパケットライブラリのAPIでは、基本的に文字列表現のネットワークアドレスが
使用されます。例えば以下のようなものです。

============= ===================
アドレス種別  python文字列の例
============= ===================
MACアドレス   '00:03:47:8c:a1:b3'
IPv4アドレス  '192.0.2.1'
IPv6アドレス  '2001:db8::2'
============= ===================

パケットの解析 (パース)
^^^^^^^^^^^^^^^^^^^^^^^^

パケットのバイト列から、対応するpythonオブジェクトを生成します。

具体的には以下のようになります。

1. ryu.lib.packet.packet.Packetクラスのオブジェクトを生成
   (data引数に解析するバイト列を指定)
2. 1.のオブジェクトのget_protocolメソッド等を使用して、
   各プロトコルヘッダに対応するオブジェクトを取得

.. raw:: latex

    \begin{sourcecode}
        pkt = packet.Packet(data=bin_packet)
        pkt_ethernet = pkt.get_protocol(ethernet.ethernet)
        if not pkt_ethernet:
            # non ethernet
            return
        print pkt_ethernet.dst
        print pkt_ethernet.src
        print pkt_ethernet.ethertype
    \end{sourcecode}

パケットの生成 (シリアライズ)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

pythonオブジェクトから、対応するパケットのバイト列を生成します。

具体的には以下のようになります。

1. ryu.lib.packet.packet.Packetクラスのオブジェクトを生成
2. 各プロトコルヘッダに対応するオブジェクトを生成  (ethernet, ipv4, ...)
3. 1.のオブジェクトのadd_protocolメソッドを使用して2.のヘッダを順番に追加
4. 1.のオブジェクトのserializeメソッドを呼び出してバイト列を生成

チェックサムやペイロード長などのいくつかのフィールドは、
明示的に値を指定しなくてもserialize時に自動的に計算されます。
詳細は各クラスのリファレンスをご参照ください。

.. raw:: latex

    \begin{sourcecode}
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=...,
                                           dst=...,
                                           src=...))
        pkt.add_protocol(ipv4.ipv4(dst=...,
                                   src=...,
                                   proto=...))
        pkt.add_protocol(icmp.icmp(type_=...,
                                   code=...,
                                   csum=...,
                                   data=...))
        pkt.serialize()
        bin_packet = pkt.data
    \end{sourcecode}

Scapyライクな代替APIも用意されていますので、お好みに応じてご使用ください。

.. raw:: latex

    \begin{sourcecode}
        e = ethernet.ethernet(...)
        i = ipv4.ipv4(...)
        u = udp.udp(...)
        pkt = e/i/u
    \end{sourcecode}

アプリケーション例
------------------

上記の例を使用して作成した、pingに返事をするアプリケーションを示します。

ARP REQUESTとICMP ECHO REQUESTをPacket-Inで受けとり、
返事をPacket-Outで送信します。
IPアドレス等は__init__メソッド内にハードコードされています。

.. raw:: latex

    \lstinputlisting{ping_responder.py}

以下はping -c 3を実行した場合のログの例です。

.. raw:: latex

    \begin{console}
    EVENT ofp_event->IcmpResponder EventOFPSwitchFeatures
    switch features ev version: 0x4 msg_type 0x6 xid 0xb63c802c OFPSwitchFeatures(auxiliary_id=0,capabilities=71,datapath_id=11974852296259,n_buffers=256,n_tables=254)
    move onto main mode
    EVENT ofp_event->IcmpResponder EventOFPPacketIn
    packet-in ethernet(dst='ff:ff:ff:ff:ff:ff',ethertype=2054,src='0a:e4:1c:d1:3e:43'), arp(dst_ip='192.0.2.9',dst_mac='00:00:00:00:00:00',hlen=6,hwtype=1,opcode=1,plen=4,proto=2048,src_ip='192.0.2.99',src_mac='0a:e4:1c:d1:3e:43'), '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    packet-out ethernet(dst='0a:e4:1c:d1:3e:43',ethertype=2054,src='0a:e4:1c:d1:3e:44'), arp(dst_ip='192.0.2.99',dst_mac='0a:e4:1c:d1:3e:43',hlen=6,hwtype=1,opcode=2,plen=4,proto=2048,src_ip='192.0.2.9',src_mac='0a:e4:1c:d1:3e:44')
    EVENT ofp_event->IcmpResponder EventOFPPacketIn
    packet-in ethernet(dst='0a:e4:1c:d1:3e:44',ethertype=2048,src='0a:e4:1c:d1:3e:43'), ipv4(csum=47390,dst='192.0.2.9',flags=0,header_length=5,identification=32285,offset=0,option=None,proto=1,src='192.0.2.99',tos=0,total_length=84,ttl=255,version=4), icmp(code=0,csum=38471,data=echo(data='S,B\x00\x00\x00\x00\x00\x03L)(\x00\x00\x00\x00\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./\x00\x00\x00\x00\x00\x00\x00\x00',id=44565,seq=0),type=8)
    packet-out ethernet(dst='0a:e4:1c:d1:3e:43',ethertype=2048,src='0a:e4:1c:d1:3e:44'), ipv4(csum=14140,dst='192.0.2.99',flags=0,header_length=5,identification=0,offset=0,option=None,proto=1,src='192.0.2.9',tos=0,total_length=84,ttl=255,version=4), icmp(code=0,csum=40519,data=echo(data='S,B\x00\x00\x00\x00\x00\x03L)(\x00\x00\x00\x00\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./\x00\x00\x00\x00\x00\x00\x00\x00',id=44565,seq=0),type=0)
    EVENT ofp_event->IcmpResponder EventOFPPacketIn
    packet-in ethernet(dst='0a:e4:1c:d1:3e:44',ethertype=2048,src='0a:e4:1c:d1:3e:43'), ipv4(csum=47383,dst='192.0.2.9',flags=0,header_length=5,identification=32292,offset=0,option=None,proto=1,src='192.0.2.99',tos=0,total_length=84,ttl=255,version=4), icmp(code=0,csum=12667,data=echo(data='T,B\x00\x00\x00\x00\x00Q\x17?(\x00\x00\x00\x00\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./\x00\x00\x00\x00\x00\x00\x00\x00',id=44565,seq=1),type=8)
    packet-out ethernet(dst='0a:e4:1c:d1:3e:43',ethertype=2048,src='0a:e4:1c:d1:3e:44'), ipv4(csum=14140,dst='192.0.2.99',flags=0,header_length=5,identification=0,offset=0,option=None,proto=1,src='192.0.2.9',tos=0,total_length=84,ttl=255,version=4), icmp(code=0,csum=14715,data=echo(data='T,B\x00\x00\x00\x00\x00Q\x17?(\x00\x00\x00\x00\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./\x00\x00\x00\x00\x00\x00\x00\x00',id=44565,seq=1),type=0)
    EVENT ofp_event->IcmpResponder EventOFPPacketIn
    packet-in ethernet(dst='0a:e4:1c:d1:3e:44',ethertype=2048,src='0a:e4:1c:d1:3e:43'), ipv4(csum=47379,dst='192.0.2.9',flags=0,header_length=5,identification=32296,offset=0,option=None,proto=1,src='192.0.2.99',tos=0,total_length=84,ttl=255,version=4), icmp(code=0,csum=26863,data=echo(data='U,B\x00\x00\x00\x00\x00!\xa26(\x00\x00\x00\x00\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./\x00\x00\x00\x00\x00\x00\x00\x00',id=44565,seq=2),type=8)
    packet-out ethernet(dst='0a:e4:1c:d1:3e:43',ethertype=2048,src='0a:e4:1c:d1:3e:44'), ipv4(csum=14140,dst='192.0.2.99',flags=0,header_length=5,identification=0,offset=0,option=None,proto=1,src='192.0.2.9',tos=0,total_length=84,ttl=255,version=4), icmp(code=0,csum=28911,data=echo(data='U,B\x00\x00\x00\x00\x00!\xa26(\x00\x00\x00\x00\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./\x00\x00\x00\x00\x00\x00\x00\x00',id=44565,seq=2),type=0)
    \end{console}

IPフラグメント対応は読者への宿題とします。
OpenFlowプロトコル自体にはMTUを取得する方法がありませんので、
ハードコードするか、何らかの工夫が必要です。
また、Ryuパケットライブラリは常にパケット全体をパース/シリアライズ
しますので、フラグメント化されたパケットを処理するためのAPI変更が必要です。
