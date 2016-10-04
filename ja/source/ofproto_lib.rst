.. _ch_ofproto_lib:

ofprotoライブラリ
=================

本章ではRyuのofprotoライブラリについて紹介します。

概要
----

ofprotoライブラリはOpenFlowプロトコルのメッセージの作成・解析を行なうための
ライブラリです。

モジュール構成
--------------

各OpenFlowバージョン(バージョンX.Y)について、
定数モジュール(ofproto_vX_Y)と
パーサーモジュール(ofproto_vX_Y_parser)が用意されています。
各OpenFlowバージョンの実装は基本的に独立しています。
OpenFlow 1.3 の場合は下記になります。

================== ======================== ===============================
OpenFlowバージョン 定数モジュール           パーサーモジュール
================== ======================== ===============================
1.3.x              ryu.ofproto.ofproto_v1_3 ryu.ofproto.ofproto_v1_3_parser
================== ======================== ===============================

定数モジュール
^^^^^^^^^^^^^^

定数モジュールにはプロトコル定数の定義があります。
例えば以下のようなものです。

================ ==================================
定数             説明
================ ==================================
OFP_VERSION      プロトコルバージョン番号
OFPP_xxxx        ポート番号
OFPCML_NO_BUFFER バッファせずに、パケット全体を送信
OFP_NO_BUFFER    無効なバッファ番号
================ ==================================

パーサーモジュール
^^^^^^^^^^^^^^^^^^

パーサーモジュールには各OpenFlowメッセージに対応したクラスが定義されています。
例えば以下のようなものです。
これらのクラスとそのインスタンスを、今後メッセージクラス、
メッセージオブジェクトと呼びます。

================ ==================================
クラス           説明
================ ==================================
OFPHello         OFPT_HELLOメッセージ
OFPPacketOut     OFPT_PACKET_OUTメッセージ
OFPFlowMod       OFPT_FLOW_MODメッセージ
================ ==================================

また、パーサーモジュールにはOpenFlowメッセージのペイロード中で使われる
構造体に対応するクラスも定義されています。
例えば以下のようなものです。
これらのクラスとそのインスタンスを、今後構造体クラス、
構造体オブジェクトと呼びます。

======================= ==================================
クラス                  構造体
======================= ==================================
OFPMatch                ofp_match
OFPInstructionGotoTable ofp_instruction_goto_table
OFPActionOutput         ofp_action_output
======================= ==================================

基本的な使い方
--------------

ProtocolDescクラス
^^^^^^^^^^^^^^^^^^

使用するOpenFlowプロトコルを指定するためのクラスです。
メッセージクラスの__init__のdatapath引数には、このクラス
(またはその派生クラスであるDatapathクラス)のオブジェクトを指定します。

.. rst-class:: sourcecode

::

    from ryu.ofproto import ofproto_protocol
    from ryu.ofproto import ofproto_v1_3

    dp = ofproto_protocol.ProtocolDesc(version=ofproto_v1_3.OFP_VERSION)

ネットワークアドレス
^^^^^^^^^^^^^^^^^^^^

Ryu ofprotoライブラリのAPIでは、基本的に文字列表現のネットワークアドレスが
使用されます。例えば以下のようなものです。

.. NOTE::

    ただし、OpenFlow 1.0に関しては異なる表現が使用されています。
    (2014年2月現在)

============= ===================
アドレス種別  python文字列の例
============= ===================
MACアドレス   '00:03:47:8c:a1:b3'
IPv4アドレス  '192.0.2.1'
IPv6アドレス  '2001:db8::2'
============= ===================

メッセージオブジェクトの生成
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

各メッセージクラス、構造体クラスのインスタンスを適切な引数で生成します。

引数の名前は、基本的にOpenFlowプロトコルで定められたフィールドの名前と
同じです。ただし、pythonの予約語と衝突する場合は、最後に「_」を付けます。
以下の例では「 ``type_`` 」がこれに当たります。

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

    定数モジュール、パーサーモジュールは直接importして使っても良いですが、
    使用するOpenFlowバージョンを変更する際に最小限の修正で済むよう、
    できるだけProtocolDescオブジェクトのofproto, ofproto_parser属性を
    使用することを推奨します。

メッセージオブジェクトの解析
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

メッセージオブジェクトの内容を調べることができます。

例えばOFPPacketInオブジェクトpidのmatchフィールドにはpin.matchとして
アクセスできます。

OFPMatchオブジェクトの各TLVには、以下のように名前でアクセスできます。

.. rst-class:: sourcecode

::

    print pin.match['in_port']

JSON
^^^^

メッセージオブジェクトをjson.dumps互換の辞書に変換する機能と、
json.loads互換の辞書からメッセージオブジェクトを復元する機能があります。

.. NOTE::

    ただし、OpenFlow 1.0に関しては実装が不完全です。
    (2014年2月現在)

.. rst-class:: sourcecode

::

    import json

    print json.dumps(msg.to_jsondict())

メッセージの解析 (パース)
^^^^^^^^^^^^^^^^^^^^^^^^^

メッセージのバイト列から、対応するメッセージオブジェクトを生成します。
スイッチから受信したメッセージについては、フレームワークが自動的に
この処理を行なうため、Ryuアプリケーションが意識する必要はありません。

具体的には以下のようになります。

1. ryu.ofproto.ofproto_parser.header関数を使用して、バージョン非依存部分を解析
2. 1.の結果をryu.ofproto.ofproto_parser.msg関数に渡して残りの部分を解析

メッセージの生成 (シリアライズ)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

メッセージオブジェクトから、対応するメッセージのバイト列を生成します。
スイッチに送信するメッセージについては、フレームワークが自動的に
この処理を行なうため、Ryuアプリケーションが意識する必要はありません。

具体的には以下のようになります。

1. メッセージオブジェクトのserializeメソッドを呼び出す
2. メッセージオブジェクトのbuf属性を読み出す

'len'などのいくつかのフィールドは、明示的に値を指定しなくても
serialize時に自動的に計算されます。
