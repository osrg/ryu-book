.. _ch_openflow_protocol:

OpenFlowプロトコル
==================

本章では、OpenFlowプロトコルで定義されている、マッチとインストラクションおよび
アクションについて説明します。

マッチ
------

マッチに指定できる条件には様々なものがあり、OpenFlowのバージョンが上がる
度にその種類は増えています。OpenFlow 1.0では12種類でしたが、OpenFlow 1.3
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


インストラクション
------------------

インストラクションは、マッチに該当するパケットを受信した時の動作を定義する
もので、 次のタイプが規定されています。

.. tabularcolumns:: |l|L|

=========================== =================================================
インストラクション          説明
=========================== =================================================
Goto Table (必須)           OpenFlow 1.1以降では、複数のフローテーブルがサポー
                            トされています。Goto Tableによって、マッチしたパ
                            ケットの処理を、指定したフローテーブルに引き継ぐ
                            ことができます。例えば、「ポート1で受信したパケッ
                            トにVLAN-ID 200を付加して、テーブル2へ飛ぶ」といっ
                            たフローエントリが設定できます。

                            指定するテーブルIDは、現在のテーブルIDより大きい
                            値でなければなりません。
Write Metadata (オプション) 以降のテーブルで参照できるメタデータをセットしま
                            す。
Write Actions (必須)        現在のアクションセットに指定されたアクションを追
                            加します。同じタイプのアクションが既にセットされ
                            ていた場合には、新しいアクションで置き換えられま
                            す。
Apply Actions (オプション)  アクションセットは変更せず、指定されたアクション
                            を直ちに適用します。
Clear Actions (オプション)  現在のアクションセットのすべてのアクションを削除
                            します。
Meter (オプション)          指定したメーターにパケットを適用します。
=========================== =================================================

Ryuでは、各インストラクションに対応する次のクラスが実装されています。

* ``OFPInstructionGotoTable``
* ``OFPInstructionWriteMetadata``
* ``OFPInstructionActions``
* ``OFPInstructionMeter``

Write/Apply/Clear Actionsは、OPFInstructionActionsにまとめられていて、
インスタンス生成時に選択します。

.. NOTE::

   Write Actionsのサポートは仕様上必須とされていますが、古いバージョンの
   Open vSwitchでは未実装であり、代替としてApply Actionsを使用する必要が
   ありました。
   Open vSwitch 2.1.0からはWrite Actionsのサポートが追加されました。


アクション
----------

OFPActionOutputクラスは、Packet-OutメッセージやFlow Modメッセージで使用
するパケット転送を指定するものです。コンストラクタの引数で転送先と、
コントローラへ送信する場合は最大データサイズ(max_len)を指定します。
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

