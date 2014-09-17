ofproto 函式庫
=================

本章介紹 Ryu ofproto 函式庫。

簡單說明
----------------

ofproto 函式庫是用來產生及解析 OpenFlow 訊息的函式庫。

相關模組
--------------

每個 OpenFlow（ 版本 X.Y ）都有相對應的常數模組（ ofproto_vX_Y ）和解析模組（ ofproto_vX_Y_parser ）每個 OpenFlow 版本的實作基本上是獨立的。


================== ======================== ===============================
OpenFlow 版本      常數模組                 解析模組
================== ======================== ===============================
1.0.x              ryu.ofproto.ofproto_v1_0 ryu.ofproto.ofproto_v1_0_parser
1.2.x              ryu.ofproto.ofproto_v1_2 ryu.ofproto.ofproto_v1_2_parser
1.3.x              ryu.ofproto.ofproto_v1_3 ryu.ofproto.ofproto_v1_3_parser
1.4.x              ryu.ofproto.ofproto_v1_4 ryu.ofproto.ofproto_v1_4_parser
================== ======================== ===============================


常數模組
^^^^^^^^^^^^^^

常數模組是用來做為通訊協定中的常數設定使用，下面列出幾個例子。


================== ==================================
常數               說明
================== ==================================
OFP_VERSION        通訊協定版本編號
OFPP_xxxx          連接埠號
OFPCML_NO_BUFFER   無緩衝區間，直接對全體發送訊息
OFP_NO_BUFFER      無效的緩衝編號
================== ==================================


解析器模組
^^^^^^^^^^^^^^^^^^

解析模組提供各個 OpenFlow 訊息的對應類別，下面列出幾個例子。
為了更好的說明類別的實體，接下來的描述將用”訊息物件”取代”訊息類別”。


================ ==================================
類別（ Class ）    說明
================ ==================================
OFPHello         OFPT_HELLO 訊息
OFPPacketOut     OFPT_PACKET_OUT 訊息
OFPFlowMod       OFPT_FLOW_MOD 訊息
================ ==================================


解析模組對應了 OpenFlow 訊息的 Payload 結構中所需的定義，例如下面的例子。
為了更好的說明類別的實體，今後將用結構物件（ structure object ）取代結構類別（ structure class ）。


======================= ==================================
類別（ Class ）           結構
======================= ==================================
OFPMatch                ofp_match
OFPInstructionGotoTable ofp_instruction_goto_table
OFPActionOutput         ofp_action_output
======================= ==================================


基本使用方法
----------------------------

ProtocolDesc 類別
^^^^^^^^^^^^^^^^^^

這是為了 OpenFlow 協定所必需存在的類別。
使用訊息類別的 __init__ 作為 datapath 的參數，指定該類別的物件。


.. rst-class:: sourcecode

::

    from ryu.ofproto import ofproto_protocol
    from ryu.ofproto import ofproto_v1_3

    dp = ofproto_protocol.ProtocolDesc(version=ofproto_v1_3.OFP_VERSION)


網路位址（ Network Address ）
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Ryu ofproto 函式庫的 API 使用最基本的文字表現網路位址，請看下面的例子。


.. NOTE::

    但是 OpenFlow 1.0 和這樣的標示方法不同。
    （ 2014年2月更新 ）


====================== =====================
位址（ Address ）種類  python文字表示
====================== =====================
MAC 位址               '00:03:47:8c:a1:b3'
IPv4 位址              '192.0.2.1'
IPv6 位址              '2001:db8::2'
====================== =====================


訊息物件（ Message Object ）的產生
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

每個訊息類別（ message class ），結構類別（ structure class ）都需要適當的參數以用來產生。
參數的名稱跟 OpenFlow 協定所定義的欄位名稱基本上是一致的。
在有衝突的情況下會在最後加入「_」，例如：「``type_`` 」就是。


.. rst-class:: sourcecode

::

    from ryu.ofproto import ofproto_protocol
    from ryu.ofproto import ofproto_v1_3

    dp = ofproto_protocol.ProtocolDesc(version=ofproto_v1_3.OFP_VERSION)
    ofp = dp.ofproto
    ofpp = dp.ofproto_parser
    actions = [parser.OFPActionOutput(port=ofp.OFPP_CONTROLLER,
                                      max_len=ofp.OFPCML_NO_BUFFER)]
    inst = [parser.OFPInstructionActions(type_=ofp.OFPIT_APPLY_ACTIONS,
                                         actions=actions)]
    fm = ofpp.OFPFlowMod(datapath=dp,
                         priority=0,
                         match=ofpp.OFPMatch(in_port=1,
                                             eth_src='00:50:56:c0:00:08'),
                         instructions=inst)


.. NOTE::

    常數模組、解析模組最好是在 import 的時候就直接標明。
    如此一來在 OpenFlow 版本變更的時候，可以將修正的程度將到最低。
    另外儘量使用 ProtocolDesc 物件的 ofproto 和 ofproto_parser 屬性。


訊息物件（ Message Object ）的解析
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

訊息物件（ message object ）的內容是可以查詢的。

例如 OFPPacketIn 物件中 pid 的 match field 用查詢 pin.match 即可得到相關的訊息。

OFPMatch 物件中 TLV 的各部分可以使用下列的名稱取得相關的資料。


.. rst-class:: sourcecode

::

    print pin.match['in_port']


JSON
^^^^^^^^

訊息物件（ message object ）轉換成為 json.dump 的功能是存在的，反之亦然。


.. NOTE::

    但是目前 OpenFlow 1.0 相關的實作並不完全。
    （ 2014年2月更新 ）


.. rst-class:: sourcecode

::

    import json

    print json.dumps(msg.to_jsondict())


訊息（ message ）的解析（ parse ）
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

該功能是為了把訊息的原始資料轉換成訊息物件。
對於從交換器收到的訊息，框架（ Framwork ）會自動地進行處理，Ryu 應用程式（ Application ）是不需要特別處理的。

具體來說如下：

1. ryu.ofproto.ofproto_parser.header 用來處理版本相依的解析
2. 上面處理過的結果可以用 ryu.ofproto.ofproto_parser.msg 功能來解析剩餘的部分

訊息的產生（ 序列化，Serialize ）
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

將訊息物件轉換並產生對應的訊息 Byte 。
同樣的，來自交換器的訊息將由框架自動處理，Ryu 應用程式無需額外的動作。

具體來說如下：

1. 呼叫訊息物件的序列化方法
2. 從訊息物件中將 buf 的屬性讀取出來

有些欄位，例如“len”即使不指定，在序列化的同時也會自動被計算出來。
