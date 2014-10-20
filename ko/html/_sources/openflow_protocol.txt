.. _ch_openflow_protocol:

OpenFlow 프로토콜
=================

이 장에서는 OpenFlow 프로토콜에 정의된 매치(match), 명령(instruction) 및 
액션(action)에 대해 설명합니다. 

매치
----

매치에 사용할 수 있는 조건에는 여러 가지가 있으며, OpenFlow의 버전이 올라갈 때
마다 그 종류는 증가하고 있습니다. OpenFlow 1.0에서는 12 종류 였지만, OpenFlow 1.3
는 40 가지의 조건이 정의되어 있습니다. 

개별적인 자세한 내용은 OpenFlow 스펙 등을 참조하시면 됩니다. 여기에서는
OpenFlow 1.3 Match 필드를 간단하게 소개합니다. 

================= ==========================================================
Match 필드 이름   설명
================= ==========================================================
in_port           수신 포트의 포트 번호
in_phy_port       수신 포트의 물리적 포트 번호
metadata          테이블간에 정보를 전달하는 데 사용되는 메타 데이터 
eth_dst           Ethernet 대상 MAC 주소
eth_src           Ethernet 원본 MAC 주소
eth_type          Ethernet 프레임 타입
vlan_vid          VLAN ID
vlan_pcp          VLAN PCP
ip_dscp           IP DSCP
ip_ecn            IP ECN
ip_proto          IP 프로토콜 종류
ipv4_src          IPv4의 소스 IP 주소
ipv4_dst          IPv4의 대상 IP 주소
tcp_src           TCPd 원본 포트 번호
tcp_dst           TCP 목적지 포트 번호
udp_src           UDP 소스 포트 번호
udp_dst           UDP 대상 포트 번호
sctp_src          SCTP의 원본 포트 번호
sctp_dst          SCTP 목적지 포트 번호
icmpv4_type       ICMP의 Type
icmpv4_code       ICMP의 Code
arp_op            ARP의 작동 코드
arp_spa           ARP의 소스 IP 주소
arp_tpa           ARP의 대상 IP 주소
arp_sha           ARP의 소스 MAC 주소
arp_tha           ARP의 대상 MAC 주소
ipv6_src          IPv6의 소스 IP 주소
ipv6_dst          IPv6의 대상 IP 주소
ipv6_flabel       IPv6의 플로우 레이블
icmpv6_type       ICMPv6의 Type
icmpv6_code       ICMPv6의 Code
ipv6_nd_target    IPv6 네이버 디스커버리의 대상 주소 
ipv6_nd_sll       IPv6 네이버 디스커버리 원본 링크 계층 주소 
ipv6_nd_tll       IPv6 네이버 디스커버리 타겟 링크 계층 주소 
mpls_label        MPLS 레이블
mpls_tc           MPLS 트래픽 클래스 (TC)
mpls_bos          MPLS의 BoS 비트
pbb_isid          802.1ah PBB의 I-SID
tunnel_id         논리 포트에 대한 메타 데이터
ipv6_exthdr       IPv6 확장 헤더의 의사 필드
================= ==========================================================

MAC 주소와 IP 주소 등의 일부 필드는 또한 마스크를 지정할 수 있습니다. 


명령
----

명령(instruction)은 매치에 해당하는 패킷을 수신했을 때의 동작을 정의하는
것으로, 다음과 같은 유형이 규정되어 있습니다. 

.. tabularcolumns:: |l|L|

=========================== =================================================
명령                        설명
=========================== =================================================
Goto Table (필수)           OpenFlow 1.1 이상에서는 여러 개의 플로우 테이블을                               합니다. Goto Table에 의해 일치된 패킷의 
                            처리를 지정된 플로우 테이블에서 처리하도록 할 
                            수 있습니다. 예를 들어, "포트 1에서 받은 패킷
                            에 VLAN-ID 200을 추가하여 테이블 2에 보냄」이라고
                            플로우 항목을 설정할 수 있습니다.

                            지정된 테이블 ID는 현재 테이블 ID보다 큰
                            값이 아니면 안됩니다. 
Write Metadata (옵션)       이후의 테이블에서 볼 수 있는 메타 데이터를 설정합니
                            다.
Write Actions (필수)        현재 액션 세트에 지정된 액션을 추가
                            합니다. 동일한 유형의 액션이 이미 설정된
                            경우에는 새로운 액션으로 대체됩니다.
Apply Actions (옵션)        액션 세트는 변경하지 않고, 지정된 액션을 
                            즉시 적용합니다.
Clear Actions (옵션)        현재 액션 세트에서 모든 액션을 제거합니다.
Meter (옵션)                지정된 미터에 패킷을 적용합니다.
=========================== =================================================

Ryu는 각 명령어에 해당하는 다음 클래스가 구현되어 있습니다. 

* ``OFPInstructionGotoTable``
* ``OFPInstructionWriteMetadata``
* ``OFPInstructionActions``
* ``OFPInstructionMeter``

Write/Apply/Clear Actions는 OPFInstructionActions에 정리하고 있고,
인스턴스 생성시에 선택합니다. 

.. NOTE::

   Write Actions의 지원은 스펙에서 필수로 되어 있지만, 이전 버전의 
   Open vSwitch에서는 구현되지 않았으며, 대신 Apply Actions를 
   사용해야 했었습니다. 
   Open vSwitch 2.1.0에서 Write Actions 지원이 추가되었습니다.


액션
----

OFPActionOutput 클래스는 Packet-Out 메시지와 Flow Mod 메시지를 사용하여 
패킷 전송을 지정하는 것입니다. 생성자의 인수 대상과
컨트롤러에 보내려면 최대 데이터 크기 (max_len)을 지정합니다.
대상에는 스위치의 물리적 포트 번호 외에 몇 가지 정의된 값을 
지정할 수 있습니다. 

.. tabularcolumns:: |l|L|

================= ============================================================
값                설명
================= ============================================================
OFPP_IN_PORT      수신 포트로 전송됩니다 
OFPP_TABLE        첫번째 플로우 테이블에 적용됩니다 
OFPP_NORMAL       스위치의 L2/L3 기능으로 전송됩니다 
OFPP_FLOOD        수신 포트 또는 블록된 포트를 제외한 해당 VLAN의
                  모든 물리적 포트에 Flooding
                  
OFPP_ALL          수신 포트를 제외한 모든 물리적 포트에 전송합니다 
OFPP_CONTROLLER   컨트롤러에 Packet-In 메시지로 보냅니다 
OFPP_LOCAL        스위치의 로컬 포트를 지정합니다 
OFPP_ANY          Flow Mod (delete) 메시지 및 Flow Stats Requests 메시지
                  에서 포트를 선택할 때 와일드 카드로 사용하는 것으로,
                  패킷 전송에서 사용되지 않습니다 
                  
                  
================= ============================================================

max_len 0을 지정하면 Packet-In 메시지 패킷의 이진 데이터를 
첨부하지 않습니다. ``OFPCML_NO_BUFFER`` 을 지정하면 OpenFlow 스위치
에서 패킷을 버퍼없이 Packet-In 메시지 패킷 전체가 첨부됩니다.

