.. _ch_openflow_protocol:

OpenFlow 通訊協定
=================

本章將描述 Match、Instructions 和 Action 在 OpenFlow 協定中的細節。

Match
----------

有許多種類的指定條件可以用在 Match ，隨著 OpenFlow 版本的不斷更新，數量也在持續增加中。
在 OpenFlow 1.0 時僅有 12 種，OpenFlow 1.3 時數量就來到約 40 種。

若想要了解每個指令的細節，請參考 OpenFlow 規格書。本章僅簡要列出 OpenFlow 1.3 的 Match 指令。


================= ==========================================================
Match Field 名稱  說明
================= ==========================================================
in_port           接受埠編號(含邏輯埠)
in_phy_port       接收埠實體編號
metadata          在 table 間傳遞使用的 Metadata
eth_src           Ethernet MAC 來源位址
eth_dst           Ethernet MAC 目的位址
eth_type          Ethernet 訊框種類
vlan_vid          VLAN ID
vlan_pcp          VLAN PCP
ip_dscp           IP DSCP
ip_ecn            IP ECN
ip_proto          IP 協定種類
ipv4_src          IPv4 IP 來源位址
ipv4_dst          IPv4 IP 目的位址
tcp_src           TCP port 來源編號
tcp_dst           TCP port 目的編號
udp_src           UDP port 來源編號
udp_dst           UDP port 目的編號
sctp_src          SCTP port 來源編號
sctp_dst          SCTP port 目的編號
icmpv4_type       ICMP 種類
icmpv4_code       ICMP Code 編碼
arp_op            ARP Opcode
arp_spa           ARP IP 來源位址
arp_tpa           ARP IP 目的位址
arp_sha           ARP MAC 來源位址
arp_tha           ARP MAC 目的位址
ipv6_src          IPv6 IP 來源位址
ipv6_dst          IPv6 IP 目的位址
ipv6_flabel       IPv6 Flow label
icmpv6_type       ICMPv6 Type
icmpv6_code       ICMPv6 Code
ipv6_nd_target    IPv6 neighbour discovery 目的位址
ipv6_nd_sll       IPv6 neighbour discovery link-layer 來源位址
ipv6_nd_tll       IPv6 neighbour discovery link-layer 目的位址
mpls_label        MPLS 標簽
mpls_tc           MPLS Traffic class(TC)
mpls_bos          MPLS Bos bit
pbb_isid          802.1ah PBB I-SID
tunnel_id         邏輯埠的 metadata
ipv6_exthdr       IPv6 extension header 的 Pseudo-field
================= ==========================================================


可以針對 MAC address 或 IP address，透過 Mask 來指定 field。

Instruction
-----------

Instruction 是用來定義當封包滿足所規範的 Match 條件時，需要執行的動作。
下面列出相關的定義。 


.. tabularcolumns:: |l|L|

==================== =====================================================================
Instruction                 説明
==================== =====================================================================
Goto Table(必要)     在 OpenFlow 1.1 或更新的版本中， multiple flow tables
                     將是必需支援的項目。透過 Goto Table 的指令可以在多個 table
                     間進行移轉，並繼續相關的比對及對應的動作。
                     例如：「收到來自 port 1 的封包時，增加 VLAN-ID 200 的 tag
                     ，並移動至 table 2」。
                     而所指定的 table ID 則必須是大於目前的 table ID。
Write Metadata(選項)  寫入 Metadata 以做為下一個 table 所需的參考資料。
Write Actions(必要)  在目前的 action set 中寫入新的 action ，如果有相同的 action 存在時
                     ，會進行覆蓋。
Apply Actions(選項)   立刻執行所指定的 action 不對現有的 action set 進行修改。
Clear Actions(選項)   清空目前存在 action set 中的資料。
Meter(選項)           指定該封包到所定義的 meter table。
==================== =====================================================================


以下的類別是對應各個 Instruction 的 Ryu 實作。

* ``OFPInstructionGotoTable``
* ``OFPInstructionWriteMetadata``
* ``OFPInstructionActions``
* ``OFPInstructionMeter``

Write/Apply/Clear Actions 已經包含在 OPFInstructionActions 中，可以在安裝的時候進行選取。


.. NOTE::

   Write Actions 雖然在規格中被列為必要，但是目前的 Open vSwitch 並不支援該功能。
   Apply Actions 是目前 Open vSwitch 所提供的功能，所以可以用來替代 Write Actions。
   Write Actions 預計在 Open vSwitch 2.1.0 中支援。


Action
----------

OFPActionOutput Class 是用來轉送指定封包，其中包含 Packet-Out 和 Flow Mod。
設定好要傳送的最大封包容量（max_len）和要傳送的 Controller 目的地做為 Constructor 的參數。
對於設定目的地，除了實體連接埠號之外還有一些其他的值可以進行定義。


.. tabularcolumns:: |l|L|

================= ========================================================================
値                説明
================= ========================================================================
OFPP_IN_PORT      轉送到接收埠
OFPP_TABLE        轉送到最前端的 table
OFPP_NORMAL       使用交換器本身的 L2 / L3 功能轉送
OFPP_FLOOD        轉送 （Flood） 到所有 VLAN 的物理連接埠，除了來源埠跟已閉鎖的埠之外
OFPP_ALL          轉送到除了來源埠之外的所有埠
OFPP_CONTROLLER   轉送到 Controller 的 Packet-In 訊息
OFPP_LOCAL        轉送到交換器本身（local port）
OFPP_ANY          使用 Wild card 來指定 Flow Mod （delete） 或 Flow Stats Requests 訊息的埠號，
                  主要功能並不是用來轉送封包訊息。
================= ========================================================================


當指定 max_len 為 0 時，Binary data 將不會被加在 Packet-In 的訊息中。
當 ``OFPCML_NO_BUFFER`` 被指定時，所有的封包將會加入 Packet-In 訊息中而不會暫存在 OpenFlow 交換器。
