.. _ch_openflow_protocol:

OpenFlow Protocol
=================

This section describes match, instructions and actions defined in the OpenFlow protocol.

Match
-----

There are a variety of conditions that can be specified to match, and it grows each time OpenFlow is updated. OpenFlow 1.0 had 12 types but in OpenFlow 1.3 as many as 40 types of conditions are defined.

For details of individual matches, please refer to the OpenFlow specification. This section gives a brief description of the Match field in OpenFlow 1.3.

================= ======================================================
Match field name  Explanation
================= ======================================================
in_port           Port number of receiving port
in_phy_port       Physical port number of receiving port
metadata          Metadata used to pass information between tables
eth_dst           Destination MAC address of Ethernet
eth_src           Source MAC address of Ethernet
eth_type          Frame type of Ethernet
vlan_vid          VLAN ID
vlan_pcp          VLAN PCP
ip_dscp           IP DSCP
ip_ecn            IP ECN
ip_proto          Protocol type of IP
ipv4_src          Source IP address of IPv4
ipv4_dst          Destination IP address of IPv4
tcp_src           Source port number of TCP
tcp_dst           Destination port number of TCP
udp_src           Source port number of UDP
udp_dst           Destination port number of UDP
sctp_src          Source port number of SCTP
sctp_dst          Destination port number of SCTP
icmpv4_type       Type of ICMP
icmpv4_code       Code of ICMP
arp_op            Opcode of ARP
arp_spa           Source IP address of ARP
arp_tpa           Target IP address of ARP
arp_sha           Source MAC address of ARP
arp_tha           Target MAC address of ARP
ipv6_src          Source IP address of IPv6
ipv6_dst          Destination IP address of IPv6
ipv6_flabel       Flow label of IPv6
icmpv6_type       Type of ICMPv6
icmpv6_code       Code of ICMPv6
ipv6_nd_target    Target address of IPv6 neighbor discovery
ipv6_nd_sll       Source link-layer address of IPv6 neighbor discovery
ipv6_nd_tll       Target link-layer address of IPv6 neighbor discovery
mpls_label        MPLS label
mpls_tc           MPLS traffic class (TC)
mpls_bos          MPLS BoS bit
pbb_isid          I-SID of 802.1ah PBB
tunnel_id         Metadata about logical port
ipv6_exthdr       Pseudo-field of extension header of IPv6
================= ======================================================

Depending on fields such as the MAC address and IP address, you can further specify the mask.


Instruction
-----------

The instruction is intended to define what happens when a packet corresponding to the match is received. The following types are defined.

.. tabularcolumns:: |l|L|

=========================== =================================================
Instruction                 Explanation
=========================== =================================================
Goto Table (Required)       In OpenFlow 1.1 and later, multiple flow tables 
                            are supported. Using GotoTable, you can take over
                            the process of matching packets to a flow table 
                            you specify. For example, you can set flow entry
                            such as "Add a VLAN-ID200 to packets received on 
                            port 1 and send it to table 2".

                            The table ID you specify must be a value greater
                            than the current table ID.
Write Metadata (Optional)   Set the metadata that can be referenced in the
                            following table.
Write Actions (Required)    Add an action that is specified in the current
                            set of actions. If same type of action has been
                            set already, it is replaced with the new action.
Apply Actions (Optional)    Immediately apply the specified action without 
                            changing the action set.
Clear Actions (Optional)    Delete all actions in the current action set.
Meter (Optional)            Apply the packet to the meter you specify.
=========================== =================================================

The following classes corresponding to each instruction are implemented in Ryu.

* ``OFPInstructionGotoTable``
* ``OFPInstructionWriteMetadata``
* ``OFPInstructionActions``
* ``OFPInstructionMeter``

Write/Apply/Clear Actions is grouped into OPFInstructionActions and is selected at the time of instantiation.

.. NOTE::

   Support for Write Actions is said to be essential, but at the current time it is not supported in Open vSwitch. Apply Actions is supported, so you need to use it instead.


Action
------

The OFPActionOutput class is used to specify packet forwarding to be used in Packet-Out and Flow Mod messages. Specify the maximum data size (max_len) to be transmitted to the controller and the destination in the constructor arguments. For the destination, other than the physical port number of the switch, some defined value can be used.

.. tabularcolumns:: |l|L|

================= ============================================================
Value             Explanation
================= ============================================================
OFPP_IN_PORT      Forwarded to the receive port
OFPP_TABLE        Applied to the first flow table.
OFPP_NORMAL       Forwarded by the L2/L3 switch function
OFPP_FLOOD        Flooded to all physical ports of the VLAN except blocked ports and receiving ports
OFPP_ALL          Forwarded to all physical ports except receiving ports
OFPP_CONTROLLER   Sent to the controller as a Packet-In message.
OFPP_LOCAL        Indicates a local port of the switch
OFPP_ANY          Meant to be used as a wild card when you select a port using Flow Mod (delete) or Stats Requests messages, and it's not used in packet forwarding.
================= ============================================================

When you specify 0 for max_len, binary data of packet is not attached to the Packet-In message. If ``OFPCML_NO_BUFFER`` is specified, the entire packet is attached to the Packet-In message without buffering the packet on the OpenFlow switch.
