.. _ch_packet_lib:

패킷 라이브러리
===============

OpenFlow의 Packet-In과 Packet-Out 메시지는 원시 패킷 내용
을 나타내는 바이트가 들어가는 필드가 있습니다.
Ryu에는 이러한 원시 패킷을 응용 프로그램에서 다루기 쉽고
하는 라이브러리가 포함되어 있습니다.
이 장에서는이 라이브러리를 소개합니다. 


기본적인 사용법 
---------------

프로토콜 헤더 클래스
^^^^^^^^^^^^^^^^^^^^

Ryu 패킷 라이브러리는 다양한 프로토콜 헤더에 대응하는 클래스
가 포함되어 있습니다.

다음을 포함 프로토콜을 지원합니다.
각 프로토콜에 대응하는 클래스 등의 자세한 것은 `API 레퍼런스 <http://ryu.readthedocs.org/en/latest/>`_ 를 참조하십시오. 

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

각 프로토콜 헤더 클래스의 __init__ 인수 이름은 기본적으로 RFC 등
사용 된 이름과 동일하게되어 있습니다.
프로토콜 헤더 클래스의 인스턴스 속성의 명명 규칙도 마찬가지입니다.
그러나 type 등 Python built-in과 충돌하는 이름의 필드에 해당하는
__init__ 인수 이름은 type_처럼 마지막에 _가 붙습니다.

일부 __init__ 인수는 기본값이 설정되어 생략 할 수 있습니다.
다음 예제에서는 version=4 등이 생략되어 있습니다. 

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

네트워크 주소 
^^^^^^^^^^^^^

Ryu 패킷 라이브러리의 API는 기본적으로 문자열 표현의 네트워크 주소가
사용됩니다. 예를 들면 다음과 같습니다.

============= ===================
주소 종류     python 문자열 예제
============= ===================
MAC 주소      '00:03:47:8c:a1:b3'
IPv4 주소     '192.0.2.1'
IPv6 주소     '2001:db8::2'
============= ===================

패킷 분석 (Parse)
^^^^^^^^^^^^^^^^^

패킷의 바이트 열에서 해당 python 객체를 생성합니다.

구체적으로는 다음과 같습니다.

1. ryu.lib.packet.packet.Packet 클래스의 객체를 생성
   (data 인수 분석하는 바이트를 지정)
2. 1. 개체의 get_protocol 메서드 등을 사용하여
   각 프로토콜 헤더에 해당하는 개체를 가져 

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

패킷의 생성 (연재)
^^^^^^^^^^^^^^^^^^

python 객체에서 해당 패킷의 바이트를 생성합니다.

구체적으로는 다음과 같습니다.

1. ryu.lib.packet.packet.Packet 클래스의 객체를 생성
2. 각 프로토콜 헤더에 해당하는 객체를 생성 (ethernet, ipv4, ...)
3. 1. 개체의 add_protocol 메서드를 사용하여 2. 헤더를 차례로 추가
4. 1. 개체 serialize 메서드를 호출하여 결과 바이트를

체크섬과 페이로드 길이 등의 일부 필드는
명시 적으로 값을 지정하지 않아도 serialize시 자동으로 계산됩니다.
자세한 내용은 각 클래스 참조를 참조하십시오. 

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

Scapy 좋아하는 대체 API도 포함되어 있기 때문에 취향에 따라 사용해주십시오. 

.. rst-class:: sourcecode

::

        e = ethernet.ethernet(...)
        i = ipv4.ipv4(...)
        u = udp.udp(...)
        pkt = e/i/u

어플리케이션 예
---------------

위의 예제를 사용하여 만든 ping에 응답하는 응용 프로그램을 보여줍니다.

ARP REQUEST와 ICMP ECHO REQUEST를 Packet-In에서 받아
답장을 Packet-Out으로 보냅니다.
IP 주소 등은 __init__ 메서드에 하드 코드되어 있습니다. 

.. rst-class:: sourcecode

.. literalinclude:: sources/ping_responder.py


.. NOTE::
    OpenFlow 1.2 이상에서는 Packet-In 메시지 match 필드에서
    퍼스 된 패킷 헤더의 내용을 검색 할 수 있습니다.
    그러나이 필드에 얼마나 많은 정보를 넣어 줄까 스위치의
    구현에 따라 다릅니다.
    예를 들어 Open vSwitch는 최소한의 정보 만 넣어주지 않으므로
    많은 경우 컨트롤러 측에서 패킷 내용을 분석해야합니다.
    한편 LINC는 가능한 한 많은 정보를 넣어줍니다.

다음은 ping -c 3를 실행 한 경우 로그의 예입니다

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

IP 조각 대응은 독자에게 숙제로합니다.
OpenFlow 프로토콜 자체에는 MTU를 검색하는 방법이 없기 때문에,
하드 코딩하거나 어떤 궁리가 필요합니다.
또한 Ryu 패킷 라이브러리는 항상 패킷 전체 퍼스 / 연재
때문에 단편화 된 패킷을 처리하기위한 API 변경이 필요합니다.
