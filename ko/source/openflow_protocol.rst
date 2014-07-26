.. _ch_openflow_protocol:

OpenFlow 프로토콜
=================

이 장에서는 OpenFlow 프로토콜에 정의 된 일치와 지침 및
작업에 대해 설명합니다. 

매치
----

매치에 사용할 수있는 조건에는 여러 가지가 있으며, OpenFlow의 버전이 올라갈 때
마다 그 종류는 증가하고 있습니다. OpenFlow 1.0에서는 12 종류 였지만, OpenFlow 1.3
는 40 가지의 조건이 정의되어 있습니다. 

개별 자세한 내용은 OpenFlow 스펙 등을 참조하시면됩니다 만, 여기에서는
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
ip_proto          IP 프로토콜 종별
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
ipv6_flabel       IPv6의 흐름 레이블
icmpv6_type       ICMPv6의 Type
icmpv6_code       ICMPv6의 Code
ipv6_nd_target    IPv6 네이버 디스커버리의 대상 주소 
ipv6_nd_sll       IPv6 네이버 디스커버리 원본 링크 계층 주소 
ipv6_nd_tll       IPv6 네이버 디스커버리 타겟 링크 계층 주소 
mpls_label        MPLS 레이블
mpls_tc           MPLS 트래픽 클래스 (TC)
mpls_bos          MPLS의 BoS 비트
pbb_isid          802.1ah PBBのI-SID
tunnel_id         논리 포트에 대한 메타 데이터
ipv6_exthdr       IPv6 확장 헤더의 의사 필드
================= ==========================================================

MAC 주소와 IP 주소 등의 일부 필드는 또한 마스크를 지정하는
수 있습니다. 


지침
----

지침은 일치에 해당하는 패킷을 수신했을 때의 동작을 정의하는
것으로, 다음과 같은 유형이 규정되어 있습니다. 

.. tabularcolumns:: |l|L|

=========================== =================================================
지팀                        설명
=========================== =================================================
Goto Table (필수)           OpenFlow 1.1 이상에서는 여러 흐름 테이블 지원
                            트되고 있습니다. Goto Table 의해 일치 된 파
                            켓의 처리를 지정된 흐름 테이블에 인수
                            수 있습니다. 예를 들어, "포트 1에서받은 패킷
                            트에 VLAN-ID 200을 추가하여 테이블 2에 난다」라고
                            흐름 항목을 설정할 수 있습니다.

                            지정된 테이블 ID는 현재 테이블 ID보다 큰
                            값이 아니면 안됩니다. 
Write Metadata (옵션)       이후의 테이블에서 볼 수있는 메타 데이터를 설정합니
                            다.
Write Actions (필수)        현재 액션 세트에 지정된 액션을 추가
                            가압합니다. 동일한 유형의 작업이 이미 설정된
                            한 경우에는 새로운 조치로 대체됩니다
                            입니다. 
Apply Actions (옵션)        액션 세트는 변경하지 않고, 지정된 액션
                            를 즉시 적용합니다.
Clear Actions (옵션)        현재 액션 세트의 모든 액션을 제거
                            합니다.
Meter (옵션)                지정된 미터에 패킷을 적용합니다.
=========================== =================================================

Ryu는 각 명령어에 해당하는 다음의 클래스가 구현되어 있습니다. 

* ``OFPInstructionGotoTable``
* ``OFPInstructionWriteMetadata``
* ``OFPInstructionActions``
* ``OFPInstructionMeter``

Write/Apply/Clear Actions는 OPFInstructionActions에 정리하고 있고,
인스턴스 생성시에 선택합니다. 

.. NOTE::

   Write Actions의 지원은 필수로되어 있습니다 만, 현재의 Open vSwitch
   에서 지원되지 않습니다. Apply Actions를 지원하고 있으므로,
   대신이 옵션을 사용할 필요가 있습니다.
   Write Actions는 Open vSwitch 2.1.0에서 지원 될 예정입니다. 


액션
----

OFPActionOutput 클래스는 Packet-Out 메시지와 Flow Mod 메시지 사용
패킷 전송을 지정하는 것입니다. 생성자의 인수 대상과
컨트롤러에 보내려면 최대 데이터 크기 (max_len)을 지정합니다.
대상에는 스위치의 물리적 포트 번호 외에 몇 가지 정의 된 값이
지정할 수 있습니다. 

.. tabularcolumns:: |l|L|

================= ============================================================
값                설명
================= ============================================================
OFPP_IN_PORT      수신 포트로 전송됩니다 
OFPP_TABLE        위로의 흐름 테이블에 적용됩니다 
OFPP_NORMAL       스위치의 L2/L3 기능으로 전송됩니다 
OFPP_FLOOD        수신 포트 또는 블록 된 포트를 제외한 해당 VLAN의
                  모든 물리적 포트에 Flooding
                  
OFPP_ALL          수신 포트를 제외한 모든 물리적 포트에 전송됩니다 
OFPP_CONTROLLER   컨트롤러에 Packet-In 메시지로 보내집니다 
OFPP_LOCAL        스위치의 로컬 포트를 지정합니다 
OFPP_ANY          Flow Mod (delete) 메시지 및 Flow Stats Requests 메시지
                  에서 포트를 선택할 때 와일드 카드로 사용하는 것으로,
                  패킷 전송에서 사용되지 않습니다 
                  
                  
================= ============================================================

max_len 0을 지정하면 Packet-In 메시지 패킷의 이진 데이터
첨부 된 없습니다. ``OFPCML_NO_BUFFER`` 을 지정하면 OpenFlow 스위치
에서 패킷을 버퍼없이 Packet-In 메시지 패킷 전체가 첨부됩니다.

