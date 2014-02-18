.. _ch_packet_lib:

Packet Library
==============

The Packet-Out and Packet-In message of OpenFlow have a field that enters a byte string that represents the contents of the raw packet. Ryu offers a library for easier handling of such raw packets from applications. This section describes this library.


Basic Usage
-----------

Protocol Header Class
^^^^^^^^^^^^^^^^^^^^^

The Ryu packet library offers classes corresponding to various protocol headers.

Protocols including the following are supported.
For details of classes corresponding to each protocol, please refer to `API Reference <http://ryu.readthedocs.org/en/latest/>`_.

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

__init__ argument name of each protocol header class is basically the same as the name that is used for RFC, etc. It is the same for the naming convention of instance attributes of the protocol header class. However, for __init__ argument name that corresponds to a field with a name that conflicts one built in to Python such as type, _ is attached at the end, such as type.

Some __init__ arguments have a default value and can be omitted. In the following example, version=4 etc. it omitted.

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

Network Address
^^^^^^^^^^^^^^^

In the API of the library Ryu packet, basically the network address of the string representation is used. The following is an example.

============= =========================
Address type  Example of python string
============= =========================
MAC address   '00:03:47:8c:a1:b3'
IPv4 address  '192.0.2.1'
IPv6 address  '2001:db8::2'
============= =========================

Analysis of Packet (Parse)
^^^^^^^^^^^^^^^^^^^^^^^^^^

Generate a corresponding python object from a sequence of bytes of the packet.

A specific example is as follows.

1. Generate ryu.lib.packet.packet.Packet class object. (Specify the byte string to be parsed into the data argument)
2. Using the get_protocol method etc. of object of 1 above, obtain the object corresponding to the respective protocol header.

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

Generation of Packets (Serialization)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Generate a corresponding sequence of bytes of the packet from a python object.

A specific example is as follows.

1. Generate a ryu.lib.packet.packet.Packet class object.
2. Generate an object corresponding to each protocol header. (ethernet, ipv4, ...)
3. Using the add_protocol method of the object of 1. above, add a header of 2. above, in order.
4. Call the serialize method of the object object of 1. above, and generate the byte sequence.

Some fields such as payload length and checksum are calculated automatically at the time of serialization even if you do not explicitly specify a value. Please refer to the reference for each class for more information.

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

An alternate API similar to Scapy is also available. Please use it according to your preference.

.. rst-class:: sourcecode

::

        e = ethernet.ethernet(...)
        i = ipv4.ipv4(...)
        u = udp.udp(...)
        pkt = e/i/u

Application Examples
--------------------

The following is an example of an application that responds to a ping created using the above examples.

Receive ARP REQUEST and ICMP ECHO REQUEST with Packet-In and send a response with Packet-Out.
IP addresses, etc. are hard-coded in the __init__ method.

.. rst-class:: sourcecode

.. literalinclude:: sources/ping_responder.py


.. NOTE::
    In OpenFlow 1.2 or later, you may retrieve the content of a parsed packet header from the match field of a Packet-In message.
    However, how much information is put in this field depends on the implementation of the switch.
    For example, Open vSwitch only puts in the minimum amount of information, and in many cases the content of the packet must be analyzed on the controller side.
    On the other hand, LINC puts in as much information as possible.

The following is an example of the log when you run ping-c 3.

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

Handling of IP fragments will be an exercise for the reader.
The OpenFlow protocol itself does not have a method to obtain the MTU, thus it needs to be hard-coded or requires some other idea.
Also, since the Ryu packet library will always parse or serialize the entire packet, you'll need API change to process packets that are fragmented.
