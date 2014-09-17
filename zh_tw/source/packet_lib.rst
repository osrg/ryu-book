.. _ch_packet_lib:

封包函式庫
====================

OpenFlow 中 Packet-In 和 Packet-Out 訊息是用來產生封包，可以在當中的欄位放入 Byte 資料並轉換為原始封包的方法。Ryu 提供了相當容易使用的封包產生函式庫給應用程式使用。

本章將介紹該函式庫。

基本使用方法
----------------------------

協定標頭類別（Protocol Header Class）
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ryu 封包函式庫提供許多協定對應的類別，用來解析或包裝封包。

下面列出 Ryu 目前所支援的協定。
若需要了解每個協定的細節請參照 `API 參考資料 <http://ryu.readthedocs.org/en/latest/>`_ 

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
- ospf
- pbb
- sctp
- slow
- tcp
- udp
- vlan
- vrrp

每一個協定類別的 __init__ 參數基本上跟 RFC 所提到的名稱是一致的。
同樣的每一個協定實體命名也相同。
但是當 __init__ 名稱與 Python 內定的關鍵字發生衝突時，會在名稱的尾端加上底線「_」。

有些 __init__ 的參數由於有內定的預設值，因此可以忽略。
下面的例子中，原本需要被加入的參數 version = 4 或其他值就可以被忽略。


.. rst-class:: sourcecode

::

        from ryu.lib.ofproto import inet
        from ryu.lib.packet import ipv4

        pkt_ipv4 = ipv4.ipv4(dst='192.0.2.1',
                             src='192.0.2.2',
                             proto=inet.IPPROTO_UDP)

.. rst-class:: sourcecode

::

        print pkt_ipv4.dst
        print pkt_ipv4.src
        print pkt_ipv4.proto


網路位址（Network Address）
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ryu 封包函式庫的 API 使用最基本的文字作為表現。舉例如下：


============= ===================
位址種類      python 文字表示
============= ===================
MAC 位址      '00:03:47:8c:a1:b3'
IPv4 位址     '192.0.2.1'
IPv6 位址     '2001:db8::2'
============= ===================


封包的解析（Parse）
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

封包的 Byte String 可以產生相對應的 Python 物件。

具體的事例如下：

1. ryu.lib.packet.packet.Packet 類別的物件產生
   （指定要解析的 byte string 給 data 作為參數）
2. 使用先前產生的物件中 get_protocol 方法，取得協定中相關屬性的物件。


.. rst-class:: sourcecode

::

        pkt = packet.Packet(data=bin_packet)
        pkt_ethernet = pkt.get_protocol(ethernet.ethernet)
        if not pkt_ethernet:
            # non ethernet
            return
        print pkt_ethernet.dst
        print pkt_ethernet.src
        print pkt_ethernet.ethertype


封包的產生（序列化，Serialize）
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

把 Python 物件轉換成為相對封包的 byte string。

具體說明如下：

1. 產生 ryu.lib.packet.packet.Packet 類別的物件
2. 產生相對應的協定物件（ethernet, ipv4, …）
3. 在 1. 所產生的物件中，使用 add_protocol 方法將 2. 所產生的物件依序加入
4. 呼叫 1. 所產生物件中的 serialize 方法將物件轉換成 byte string

Checksum 和 payload 的長度不需要特別設定，在序列化的同時會被自動計算出來。
詳細的各類別細節請參考相關資訊。


.. rst-class:: sourcecode

::

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


另外也提供 API 類似 Scapy，請根據個人喜好選擇使用。


.. rst-class:: sourcecode

::

        e = ethernet.ethernet(...)
        i = ipv4.ipv4(...)
        u = udp.udp(...)
        pkt = e/i/u


應用程式範例
------------------------------------

接下來的例子是使用上述的方法，達成一個可以針對 ping 做出回應的應用程式。

接受 Packet-In 所收到的 ARP REQUEST 和 ICMP ECHO REQUEST 後藉由 Packet-Out 發送回應。
IP 位址等 __init__ 的參數都是使用固定程式碼（hard-code）的方式。


.. rst-class:: sourcecode

.. literalinclude:: sources/ping_responder.py


.. NOTE::

    OpenFlow 1.2版本之後，因為 match 而帶來的 Packet-In 訊息中，將會帶有已經被解析過的資訊。
    但是這些資訊的多寡以及詳細程度要看每一台交換器的實際處理決定。
    例如 Open vSwitch 僅放入最低需求的資訊，在大多數的情況下 Controller 需要針對資料再進行處理。
    反之 LINC 則盡可能放入資訊。


以下是使用 “ping -c 3” 時所產生的記錄擋（log）。


.. rst-class:: console

::

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

IP fragments 將會是使用者需要解決的課題。
由於 OpenFlow 協定本身並沒有提供得到 MTU 資訊的方法，目前僅能使用其他方法解決。例如固定程式碼（hard-code）。
另外，因為 Ryu 封包函式庫會對所有的封包進行解析或序列化，你將會需要使用 API 來處理封包斷裂（fragmented）的問題。
