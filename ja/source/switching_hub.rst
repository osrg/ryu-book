.. _ch_switching_hub:

スイッチングハブ
================

本章では、簡単なスイッチングハブの実装を題材として、Ryuによるアプリケーションの
実装方法を解説していきます。


スイッチングハブ
----------------

世の中には様々な機能を持つスイッチングハブがありますが、ここでは
次のような単純な機能を持ったスイッチングハブの実装を見てみます。

* ポートに接続されているホストのMACアドレスを学習し、MACアドレステーブル
  に保持する
* 学習済みのホスト宛のパケットを受信したら、ホストの接続されているポートに転送する
* 未知のホスト宛のパケットを受信したら、フラッディングする

このようなスイッチをRyuを使って実現してみましょう。


OpenFlowによるスイッチングハブ
------------------------------

OpenFlowスイッチは、Ryuの様なOpenFlowコントローラからの指示を受けて、
次のようなことを行えます。

* 受信したパケットのアドレスを書き換えたり、指定のポートから転送
* 受信したパケットをコントローラへ転送(Packet-In)
* コントローラから転送されたパケットを指定のポートから転送(Packet-Out)

これらの機能を組み合わせ、スイッチングハブを実現することが出来ます。

まずは、Packet-Inの機能を利用したMACアドレスの学習です。
コントローラは、Packet-Inの機能を利用し、スイッチからパケットを受け取る事が出来ます。
受け取ったパケットを解析し、ホストのMACアドレスや接続されている
ポートの情報を学習することが出来ます。

学習の後は受信したパケットの転送です。
パケットの宛先MACアドレスが学習済みのホストのものか検索します。
検索結果によって次の処理を実行します。

* 学習済みのホストの場合…Packet-Outの機能で、接続先のポートからパケットを転送
* 未知のホストの場合…Packet-Outの機能でパケットをフラッディング

これらの動作を順を追って図とともに説明します。


1. 初期状態

    フローテーブルが空の初期状態です。

    ポート1にホストA、ポート4にホストB、ポート3にホストCが接続されているもの
    とします。

    .. only:: latex

       .. image:: images/switching_hub/fig1.eps
          :scale: 80 %
          :align: center

    .. only:: not latex

       .. image:: images/switching_hub/fig1.png
          :align: center


2. ホストA→ホストB

    ホストAからホストBへのパケットが送信されると、Packet-Inメッセージが送られ、
    ホストAのMACアドレスがポート1に学習されます。ホストBのポートはまだ分かって
    いないため、パケットはフラッディングされ、パケットはホストBとホストCで受信
    されます。

    .. only:: latex

       .. image:: images/switching_hub/fig2.eps
          :scale: 80 %
          :align: center

    .. only:: not latex

       .. image:: images/switching_hub/fig2.png
          :align: center

    Packet-In::

        in-port: 1
        eth-dst: ホストB
        eth-src: ホストA

    Packet-Out::

        action: OUTPUT:フラッディング


3. ホストB→ホストA

    ホストBからホストAにパケットが返されると、フローテーブルにエントリを追加し、
    またパケットはポート1に転送されます。そのため、このパケットはホストCでは
    受信されません。

    .. only:: latex

       .. image:: images/switching_hub/fig3.eps
          :scale: 80 %
          :align: center

    .. only:: not latex

       .. image:: images/switching_hub/fig3.png
          :align: center


    Packet-In::

        in-port: 4
        eth-dst: ホストA
        eth-src: ホストB

    Packet-Out::

        action: OUTPUT:ポート1


4. ホストA→ホストB

    再度、ホストAからホストBへのパケットが送信されると、フローテーブルに
    エントリを追加し、またパケットはポート4に転送されます。

    .. only:: latex

       .. image:: images/switching_hub/fig4.eps
          :scale: 80 %
          :align: center

    .. only:: not latex

       .. image:: images/switching_hub/fig4.png
          :align: center


    Packet-In::

        in-port: 1
        eth-dst: ホストB
        eth-src: ホストA

    Packet-Out::

        action: OUTPUT:ポート4


次に、実際にRyuを使って実装されたスイッチングハブのソースコードを見ていきます。


Ryuによるスイッチングハブの実装
-------------------------------

スイッチングハブのソースコードは、Ryuのソースツリーにあります。

    ryu/app/example_switch_13.py

OpenFlowのバージョンに応じて、他にもsimple_switch.py(OpenFlow 1.0)、
simple_switch_12.py(OpenFlow 1.2)がありますが、ここではOpenFlow 1.3に対応した
実装を見ていきます。

短いソースコードなので、全体をここに掲載します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/example_switch_13.py
    :lines: 16-

それでは、それぞれの実装内容について見ていきます。


クラスの定義と初期化
^^^^^^^^^^^^^^^^^^^^

Ryuアプリケーションとして実装するため、ryu.base.app_manager.RyuAppを
継承します。また、OpenFlow 1.3を使用するため、 ``OFP_VERSIONS`` に
OpenFlow 1.3のバージョンを指定しています。

また、MACアドレステーブル mac_to_port を定義しています。

OpenFlowプロトコルでは、OpenFlowスイッチとコントローラが通信を行うために
必要となるハンドシェイクなどのいくつかの手順が決められていますが、Ryuの
フレームワークが処理してくれるため、Ryuアプリケーションでは意識する必要は
ありません。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/example_switch_13.py
    :pyobject: ExampleSwitch13
    :end-before: set_ev_cls
    :append: # ...

イベントハンドラ
^^^^^^^^^^^^^^^^

Ryuでは、OpenFlowメッセージを受信するとメッセージに対応したイベントが発生
します。Ryuアプリケーションは、受け取りたいメッセージに対応したイベント
ハンドラを実装します。

イベントハンドラは、引数にイベントオブジェクトを持つ関数を定義し、
``ryu.controller.handler.set_ev_cls`` デコレータで修飾します。

set_ev_clsは、引数に受け取るメッセージに対応したイベントクラスとOpenFlow
スイッチのステートを指定します。

イベントクラス名は、 ``ryu.controller.ofp_event.EventOFP`` + <OpenFlow
メッセージ名>となっています。例えば、Packet-Inメッセージの場合は、
``EventOFPPacketIn`` になります。
詳しくは、Ryuのドキュメント `APIリファレンス <http://ryu.readthedocs.org/en/latest/>`_ を参照してください。
ステートには、以下のいずれか、またはリストを指定します。

.. tabularcolumns:: |l|L|

=========================================== ==================================
定義                                        説明
=========================================== ==================================
ryu.controller.handler.HANDSHAKE_DISPATCHER HELLOメッセージの交換
ryu.controller.handler.CONFIG_DISPATCHER    SwitchFeaturesメッセージの受信待ち
ryu.controller.handler.MAIN_DISPATCHER      通常状態
ryu.controller.handler.DEAD_DISPATCHER      コネクションの切断
=========================================== ==================================


Table-missフローエントリの追加
""""""""""""""""""""""""""""""

OpenFlowスイッチとのハンドシェイク完了後にTable-missフローエントリを
フローテーブルに追加し、Packet-Inメッセージを受信する準備を行います。

具体的には、Switch Features(Features Reply)メッセージを受け取り、そこで
Table-missフローエントリの追加を行います。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/example_switch_13.py
    :dedent: 4
    :prepend: @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    :pyobject: ExampleSwitch13.switch_features_handler
    :end-before: #
    :append: # ...

``ev.msg`` には、イベントに対応するOpenFlowメッセージクラスのインスタンスが
格納されています。この場合は、
``ryu.ofproto.ofproto_v1_3_parser.OFPSwitchFeatures`` になります。

``msg.datapath`` には、このメッセージを発行したOpenFlowスイッチに対応する
``ryu.controller.controller.Datapath`` クラスのインスタンスが格納されています。

Datapathクラスは、OpenFlowスイッチとの実際の通信処理や受信メッセージに対応
したイベントの発行などの重要な処理を行っています。

Ryuアプリケーションで利用する主な属性は以下のものです。

.. tabularcolumns:: |l|L|

============== ==============================================================
属性名         説明
============== ==============================================================
id             接続しているOpenFlowスイッチのID(データパスID)です。
ofproto        使用しているOpenFlowバージョンに対応したofprotoモジュールを
               示します。OpenFlow 1.3 の場合は下記になります。

               ``ryu.ofproto.ofproto_v1_3``

ofproto_parser ofprotoと同様に、ofproto_parserモジュールを示します。
               OpenFlow 1.3 の場合は下記になります。

               ``ryu.ofproto.ofproto_v1_3_parser``
============== ==============================================================

Ryuアプリケーションで利用するDatapathクラスの主なメソッドは以下のものです。

send_msg(msg)

    OpenFlowメッセージを送信します。
    msgは、送信OpenFlowメッセージに対応した
    ``ryu.ofproto.ofproto_parser.MsgBase`` のサブクラスです。


スイッチングハブでは、受信したSwitch Featuresメッセージ自体は特に
使いません。Table-missフローエントリを追加するタイミングを得るための
イベントとして扱っています。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/example_switch_13.py
    :dedent: 4
    :prepend: def switch_features_handler(self, ev):
              # ...
    :pyobject: ExampleSwitch13.switch_features_handler
    :start-after: parser = datapath.ofproto_parser

Table-missフローエントリは、優先度が最低(0)で、すべてのパケットにマッチ
するエントリです。このエントリのインストラクションにコントローラポート
への出力アクションを指定することで、受信パケットが、すべての通常のフロー
エントリにマッチしなかった場合、Packet-Inを発行するようになります。

すべてのパケットにマッチさせるため、空のマッチを生成します。マッチは
``OFPMatch`` クラスで表されます。

次に、コントローラポートへ転送するためのOUTPUTアクションクラス(
``OFPActionOutput``)のインスタンスを生成します。
出力先にコントローラ、パケット全体をコントローラに送信するためにmax_lenには
``OFPCML_NO_BUFFER`` を指定しています。

.. NOTE::

    コントローラにはパケットの先頭部分(Ethernetヘッダー分)だけを送信
    させ、残りはスイッチにバッファーさせた方が効率の点では望ましいの
    ですが、Open vSwitchのバグを回避するために、ここではパケット全体を
    送信させます。このバグはOpen vSwitch 2.1.0で修正されました。

最後に、優先度に0(最低)を指定して ``add_flow()`` メソッドを実行してFlow Mod
メッセージを送信します。add_flow()メソッドの内容については後述します。




Packet-inメッセージ
"""""""""""""""""""

未知の宛先の受信パケットを受け付けるため、Packet-Inイベントのハンドラを作成します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/example_switch_13.py
    :dedent: 4
    :prepend: @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    :pyobject: ExampleSwitch13._packet_in_handler
    :end-before: #
    :append: # ...

OFPPacketInクラスのよく使われる属性には以下のようなものがあります。

.. tabularcolumns:: |l|L|

========= ===================================================================
属性名    説明
========= ===================================================================
match     ``ryu.ofproto.ofproto_v1_3_parser.OFPMatch`` クラスのインスタンス
          で、受信パケットのメタ情報が設定されています。
data      受信パケット自体を示すバイナリデータです。
total_len 受信パケットのデータ長です。
buffer_id 受信パケットがOpenFlowスイッチ上でバッファされている場合、
          そのIDが示されます。バッファされていない場合は、
          ``ryu.ofproto.ofproto_v1_3.OFP_NO_BUFFER`` がセットされます。
========= ===================================================================


MACアドレステーブルの更新
"""""""""""""""""""""""""

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/example_switch_13.py
    :dedent: 4
    :prepend: def _packet_in_handler(self, ev):
              # ...
    :pyobject: ExampleSwitch13._packet_in_handler
    :start-after: src = eth_pkt.src
    :end-before: # if the destination mac address is already learned,
    :append: # ...

OFPPacketInクラスのmatchから、受信ポート(``in_port``)を取得します。
宛先MACアドレスと送信元MACアドレスは、Ryuのパケットライブラリを使って、
受信パケットのEthernetヘッダから取得しています。

取得した送信元MACアドレスと受信ポート番号で、MACアドレステーブルを更新します。

複数のOpenFlowスイッチとの接続に対応するため、MACアドレステーブルはOpenFlow
スイッチ毎に管理するようになっています。OpenFlowスイッチの識別にはデータパスID
を用いています。


転送先ポートの判定
""""""""""""""""""

宛先MACアドレスが、MACアドレステーブルに存在する場合は対応するポート番号を、
見つからなかった場合はフラッディング(``OFPP_FLOOD``)を出力ポートに指定した
OUTPUTアクションクラスのインスタンスを生成します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/example_switch_13.py
    :dedent: 4
    :prepend: def _packet_in_handler(self, ev):
              # ...
    :pyobject: ExampleSwitch13._packet_in_handler
    :start-after: self.mac_to_port[dpid][src] = in_port
    :end-before: # construct packet_out message and send it.
    :append: # ...

宛先MACアドレスが見つかった場合は、OpenFlowスイッチのフローテーブルに
エントリを追加します。

Table-missフローエントリの追加と同様に、マッチとアクションを指定して
add_flow()を実行し、フローエントリを追加します。

Table-missフローエントリとは違って、今回はマッチに条件を設定します。
今回のスイッチングハブの実装では、受信ポート(in_port)と宛先MACアドレス
(eth_dst)を指定しています。例えば、「ポート1で受信したホストB宛」のパケット
が対象となります。

今回のフローエントリでは、優先度に1を指定しています。値が大きい
ほど優先度が高くなるので、ここで追加するフローエントリは、Table-missフロー
エントリより先に評価されるようになります。

前述のアクションを含めてまとめると、以下のようなエントリをフローテーブル
に追加します。

    ポート1で受信した、ホストB宛(宛先MACアドレスがB)のパケットを、
    ポート4に転送する

.. HINT::

    OpenFlowでは、NORMALポートという論理的な出力ポートがオプションで規定
    されており、出力ポートにNORMALを指定すると、スイッチのL2/L3機能を使っ
    てパケットを処理するようになります。つまり、すべてのパケットをNORMAL
    ポートに出力するように指示するだけで、スイッチングハブとして動作する
    ようにできますが、ここでは各々の処理をOpenFlowを使って実現するものとします。


フローエントリの追加処理
""""""""""""""""""""""""

Packet-Inハンドラの処理がまだ終わっていませんが、ここで一旦フローエントリ
を追加するメソッドの方を見ていきます。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/example_switch_13.py
    :dedent: 4
    :pyobject: ExampleSwitch13.add_flow
    :end-before: mod = parser.OFPFlowMod
    :append: # ...

フローエントリには、対象となるパケットの条件を示すマッチと、そのパケット
に対する操作を示すインストラクション、エントリの優先度、有効時間などを
設定します。

スイッチングハブの実装では、インストラクションにApply Actionsを使用して、
指定したアクションを直ちに適用するように設定しています。

最後に、Flow Modメッセージを発行してフローテーブルにエントリを追加します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/example_switch_13.py
    :dedent: 4
    :prepend: def add_flow(self, datapath, priority, match, actions):
              # ...
    :pyobject: ExampleSwitch13.add_flow
    :start-after: actions)]

Flow Modメッセージに対応するクラスは ``OFPFlowMod`` クラスです。OFPFlowMod
クラスのインスタンスを生成して、Datapath.send_msg() メソッドでOpenFlow
スイッチにメッセージを送信します。

OFPFlowModクラスのコンストラクタには多くの引数がありますが、多くのものは
大抵の場合、デフォルト値のままで済みます。かっこ内はデフォルト値です。

datapath

    フローテーブルを操作する対象となるOpenFlowスイッチに対応するDatapath
    クラスのインスタンスです。通常は、Packet-Inメッセージなどのハンドラ
    に渡されるイベントから取得したものを指定します。

cookie (0)

    コントローラが指定する任意の値で、エントリの更新または削除を行う際の
    フィルタ条件として使用できます。パケットの処理では使用されません。

cookie_mask (0)

    エントリの更新または削除の場合に、0以外の値を指定すると、エントリの
    cookie値による操作対象エントリのフィルタとして使用されます。

table_id (0)

    操作対象のフローテーブルのテーブルIDを指定します。

command (ofproto_v1_3.OFPFC_ADD)

    どのような操作を行うかを指定します。

    ==================== ========================================
    値                   説明
    ==================== ========================================
    OFPFC_ADD            新しいフローエントリを追加します
    OFPFC_MODIFY         フローエントリを更新します
    OFPFC_MODIFY_STRICT  厳格に一致するフローエントリを更新します
    OFPFC_DELETE         フローエントリを削除します
    OFPFC_DELETE_STRICT  厳格に一致するフローエントリを削除します
    ==================== ========================================

idle_timeout (0)

    このエントリの有効期限を秒単位で指定します。エントリが参照されずに
    idle_timeoutで指定した時間を過ぎた場合、そのエントリは削除されます。
    エントリが参照されると経過時間はリセットされます。

    エントリが削除されるとFlow Removedメッセージがコントローラに通知され
    ます。

hard_timeout (0)

    このエントリの有効期限を秒単位で指定します。idle_timeoutと違って、
    hard_timeoutでは、エントリが参照されても経過時間はリセットされません。
    つまり、エントリの参照の有無に関わらず、指定された時間が経過すると
    エントリが削除されます。

    idle_timeoutと同様に、エントリが削除されるとFlow Removedメッセージが
    通知されます。

priority (0)

    このエントリの優先度を指定します。
    値が大きいほど、優先度も高くなります。

buffer_id (ofproto_v1_3.OFP_NO_BUFFER)

    OpenFlowスイッチ上でバッファされたパケットのバッファIDを指定します。
    バッファIDはPacket-Inメッセージで通知されたものであり、指定すると
    OFPP_TABLEを出力ポートに指定したPacket-OutメッセージとFlow Modメッセージ
    の2つのメッセージを送ったのと同じように処理されます。
    commandがOFPFC_DELETEまたはOFPFC_DELETE_STRICTの場合は無視されます。

    バッファIDを指定しない場合は、 ``OFP_NO_BUFFER`` をセットします。

out_port (0)

    OFPFC_DELETEまたはOFPFC_DELETE_STRICTの場合に、対象となるエントリを
    出力ポートでフィルタします。OFPFC_ADD、OFPFC_MODIFY、OFPFC_MODIFY_STRICT
    の場合は無視されます。

    出力ポートでのフィルタを無効にするには、 ``OFPP_ANY`` を指定します。

out_group (0)

    out_portと同様に、出力グループでフィルタします。

    無効にするには、 ``OFPG_ANY`` を指定します。

flags (0)

    以下のフラグの組み合わせを指定することができます。

    .. tabularcolumns:: |l|L|

    ===================== ===================================================
    値                    説明
    ===================== ===================================================
    OFPFF_SEND_FLOW_REM   このエントリが削除された時に、コントローラにFlow
                          Removedメッセージを発行します。
    OFPFF_CHECK_OVERLAP   OFPFC_ADDの場合に、重複するエントリのチェックを行い
                          ます。重複するエントリがあった場合にはFlow Modは失
                          敗し、エラーが返されます。
    OFPFF_RESET_COUNTS    該当エントリのパケットカウンタとバイトカウンタを
                          リセットします。
    OFPFF_NO_PKT_COUNTS   このエントリのパケットカウンタを無効にします。
    OFPFF_NO_BYT_COUNTS   このエントリのバイトカウンタを無効にします。
    ===================== ===================================================

match (None)

    マッチを指定します。

instructions ([])

    インストラクションのリストを指定します。


パケットの転送
""""""""""""""

Packet-Inハンドラに戻り、最後の処理の説明です。

宛先MACアドレスがMACアドレステーブルから見つかったかどうかに関わらず、最終的
にはPacket-Outメッセージを発行して、受信パケットを転送します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/example_switch_13.py
    :dedent: 4
    :prepend: def _packet_in_handler(self, ev):
              # ...
    :pyobject: ExampleSwitch13._packet_in_handler
    :start-after: self.add_flow(datapath, 1, match, actions)

Packet-Outメッセージに対応するクラスは ``OFPPacketOut`` クラスです。

OFPPacketOutのコンストラクタの引数は以下のようになっています。

datapath

    OpenFlowスイッチに対応するDatapathクラスのインスタンスを指定します。

buffer_id

    OpenFlowスイッチ上でバッファされたパケットのバッファIDを指定します。
    バッファを使用しない場合は、 ``OFP_NO_BUFFER`` を指定します。

in_port

    パケットを受信したポートを指定します。受信パケットでない場合は、
    ``OFPP_CONTROLLER`` を指定します。

actions

    アクションのリストを指定します。

data

    パケットのバイナリデータを指定します。buffer_idに ``OFP_NO_BUFFER``
    が指定された場合に使用されます。OpenFlowスイッチのバッファを利用す
    る場合は省略します。


スイッチングハブの実装では、buffer_idにPacket-Inメッセージのbuffer_idを
指定しています。Packet-Inメッセージのbuffer_idが無効だった場合は、
Packet-Inの受信パケットをdataに指定して、パケットを送信しています。


これで、スイッチングハブのソースコードの説明は終わりです。
次は、このスイッチングハブを実行して、実際の動作を確認します。


Ryuアプリケーションの実行
-------------------------

スイッチングハブの実行のため、OpenFlowスイッチにはOpen vSwitch、実行
環境としてmininetを使います。

Ryu用のOpenFlow Tutorial VMイメージが用意されているので、このVMイメージ
を利用すると実験環境を簡単に準備することができます。

VMイメージ

    http://sourceforge.net/projects/ryu/files/vmimages/OpenFlowTutorial/

    OpenFlow_Tutorial_Ryu3.2.ova (約1.4GB)

関連ドキュメント(Wikiページ)

    https://github.com/osrg/ryu/wiki/OpenFlow_Tutorial

ドキュメントにあるVMイメージは、Open vSwitchとRyuのバージョンが古いため
ご注意ください。


このVMイメージを使わず、自分で環境を構築することも当然できます。VMイメージ
で使用している各ソフトウェアのバージョンは最新版を想定しています。
自身で構築する場合は参考にしてください。

Mininet VM
  http://mininet.org/download/

  インストール手順(githubページ)
    https://github.com/mininet/mininet/blob/master/INSTALL


Open vSwitch
  http://openvswitch.org/download/

  インストール手順(githubページ)
    https://github.com/openvswitch/ovs/blob/master/INSTALL.md


Ryu
  https://github.com/osrg/ryu/

  インストール手順

  .. rst-class:: console

  ::

      $ sudo apt-get install git python-dev python-setuptools python-pip
      $ git clone https://github.com/osrg/ryu.git
      $ cd ryu
      $ sudo pip install .


ここでは、Ryu用OpenFlow TutorialのVMイメージを利用します。

Mininetの実行
^^^^^^^^^^^^^

mininetからxtermを起動するため、Xが使える環境が必要です。

ここでは、OpenFlow TutorialのVMを利用しているため、
sshでX11 Forwardingを有効にしてログインします。

    ::

        $ ssh -X ryu@<VMのアドレス>

ユーザー名は ``ryu`` 、パスワードも ``ryu`` です。


ログインできたら、 ``mn`` コマンドによりMininet環境を起動します。

構築する環境は、ホスト3台、スイッチ1台のシンプルな構成です。

mnコマンドのパラメータは、以下のようになります。

============ ========== ===========================================
パラメータ   値         説明
============ ========== ===========================================
topo         single,3   スイッチが1台、ホストが3台のトポロジ
mac          なし       自動的にホストのMACアドレスをセットする
switch       ovsk       Open vSwitchを使用する
controller   remote     OpenFlowコントローラは外部のものを利用する
x            なし       xtermを起動する
============ ========== ===========================================

実行例は以下のようになります。

.. rst-class:: console

::

    $ sudo mn --topo single,3 --mac --switch ovsk --controller remote -x
    *** Creating network
    *** Adding controller
    Unable to contact the remote controller at 127.0.0.1:6633
    *** Adding hosts:
    h1 h2 h3
    *** Adding switches:
    s1
    *** Adding links:
    (h1, s1) (h2, s1) (h3, s1)
    *** Configuring hosts
    h1 h2 h3
    *** Running terms on localhost:10.0
    *** Starting controller
    *** Starting 1 switches
    s1
    *** Starting CLI:
    mininet>

実行するとデスクトップPC上でxtermが5つ起動します。
それぞれ、ホスト1～3、スイッチ、コントローラに対応します。

スイッチのxtermからコマンドを実行して、使用するOpenFlowのバージョンを
セットします。ウインドウタイトルが「switch: s1 (root)」となっている
ものがスイッチ用のxtermです。

まずはOpen vSwitchの状態を見てみます。

switch: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl show
    fdec0957-12b6-4417-9d02-847654e9cc1f
    Bridge "s1"
        Controller "ptcp:6634"
        Controller "tcp:127.0.0.1:6633"
        fail_mode: secure
        Port "s1-eth3"
            Interface "s1-eth3"
        Port "s1-eth2"
            Interface "s1-eth2"
        Port "s1-eth1"
            Interface "s1-eth1"
        Port "s1"
            Interface "s1"
                type: internal
    ovs_version: "1.11.0"
    root@ryu-vm:~# ovs-dpctl show
    system@ovs-system:
            lookups: hit:14 missed:14 lost:0
            flows: 0
            port 0: ovs-system (internal)
            port 1: s1 (internal)
            port 2: s1-eth1
            port 3: s1-eth2
            port 4: s1-eth3
    root@ryu-vm:~#

スイッチ(ブリッジ) *s1* ができていて、ホストに対応するポートが
3つ追加されています。

次にOpenFlowのバージョンとして1.3を設定します。

switch: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13
    root@ryu-vm:~#

空のフローテーブルを確認してみます。

switch: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O OpenFlow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
    root@ryu-vm:~#

ovs-ofctlコマンドには、オプションで使用するOpenFlowのバージョンを
指定する必要があります。デフォルトは *OpenFlow10* です。


スイッチングハブの実行
^^^^^^^^^^^^^^^^^^^^^^

準備が整ったので、Ryuアプリケーションを実行します。

ウインドウタイトルが「controller: c0 (root)」となっているxtermから
次のコマンドを実行します。

controller: c0:

.. rst-class:: console

::

    root@ryu-vm:~# ryu-manager --verbose ryu.app.simple_switch_13
    loading app ryu.app.simple_switch_13
    loading app ryu.controller.ofp_handler
    instantiating app ryu.app.simple_switch_13
    instantiating app ryu.controller.ofp_handler
    BRICK SimpleSwitch13
      CONSUMES EventOFPSwitchFeatures
      CONSUMES EventOFPPacketIn
    BRICK ofp_event
      PROVIDES EventOFPSwitchFeatures TO {'SimpleSwitch13': set(['config'])}
      PROVIDES EventOFPPacketIn TO {'SimpleSwitch13': set(['main'])}
      CONSUMES EventOFPErrorMsg
      CONSUMES EventOFPHello
      CONSUMES EventOFPEchoRequest
      CONSUMES EventOFPPortDescStatsReply
      CONSUMES EventOFPSwitchFeatures
    connected socket:<eventlet.greenio.GreenSocket object at 0x2e2c050> address:('127.0.0.1', 53937)
    hello ev <ryu.controller.ofp_event.EventOFPHello object at 0x2e2a550>
    move onto config mode
    EVENT ofp_event->SimpleSwitch13 EventOFPSwitchFeatures
    switch features ev version: 0x4 msg_type 0x6 xid 0xff9ad15b OFPSwitchFeatures(auxiliary_id=0,capabilities=71,datapath_id=1,n_buffers=256,n_tables=254)
    move onto main mode

OVSとの接続に時間がかかる場合がありますが、少し待つと上のように

.. rst-class:: console

::

    connected socket:<....
    hello ev ...
    ...
    move onto main mode

と表示されます。

これで、OVSと接続し、ハンドシェイクが行われ、Table-missフローエントリが
追加され、Packet-Inを待っている状態になっています。

Table-missフローエントリが追加されていることを確認します。

switch: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=105.975s, table=0, n_packets=0, n_bytes=0, priority=0 actions=CONTROLLER:65535
    root@ryu-vm:~#

優先度が0で、マッチがなく、アクションにCONTROLLER、送信データサイズ65535
(0xffff = OFPCML_NO_BUFFER)が指定されています。


動作の確認
^^^^^^^^^^

ホスト1からホスト2へpingを実行します。

1. ARP request

    この時点では、ホスト1はホスト2のMACアドレスを知らないので、ICMP echo
    requestに先んじてARP requestをブロードキャストするはずです。
    このブロードキャストパケットはホスト2とホスト3で受信されます。

2. ARP reply

    ホスト2がARPに応答して、ホスト1にARP replyを返します。

3. ICMP echo request

    これでホスト1はホスト2のMACアドレスを知ることができたので、echo request
    をホスト2に送信します。

4. ICMP echo reply

    ホスト2はホスト1のMACアドレスを既に知っているので、echo replyをホスト1
    に返します。

このような通信が行われるはずです。

pingコマンドを実行する前に、各ホストでどのようなパケットを受信したかを確認
できるようにtcpdumpコマンドを実行しておきます。

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h1-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h1-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h2-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h2-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes

host: h3:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h3-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h3-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes


それでは、最初にmnコマンドを実行したコンソールで、次のコマンドを実行して
ホスト1からホスト2へpingを発行します。

.. rst-class:: console

::

    mininet> h1 ping -c1 h2
    PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
    64 bytes from 10.0.0.2: icmp_req=1 ttl=64 time=97.5 ms

    --- 10.0.0.2 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 97.594/97.594/97.594/0.000 ms
    mininet>


ICMP echo replyは正常に返ってきました。

まずはフローテーブルを確認してみましょう。

switch: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=417.838s, table=0, n_packets=3, n_bytes=182, priority=0 actions=CONTROLLER:65535
     cookie=0x0, duration=48.444s, table=0, n_packets=2, n_bytes=140, priority=1,in_port=2,dl_dst=00:00:00:00:00:01 actions=output:1
     cookie=0x0, duration=48.402s, table=0, n_packets=1, n_bytes=42, priority=1,in_port=1,dl_dst=00:00:00:00:00:02 actions=output:2
    root@ryu-vm:~#

Table-missフローエントリ以外に、優先度が1のフローエントリが2つ登録されて
います。

(1) 受信ポート(in_port):2, 宛先MACアドレス(dl_dst):ホスト1 →
    動作(actions):ポート1に転送
(2) 受信ポート(in_port):1, 宛先MACアドレス(dl_dst):ホスト2 →
    動作(actions):ポート2に転送

(1)のエントリは2回参照され(n_packets)、(2)のエントリは1回参照されています。
(1)はホスト2からホスト1宛の通信なので、ARP replyとICMP echo replyの2つが
マッチしたものでしょう。
(2)はホスト1からホスト2宛の通信で、ARP requestはブロードキャストされるので、
これはICMP echo requestによるもののはずです。


それでは、simple_switch_13のログ出力を見てみます。

controller: c0:

.. rst-class:: console

::

    EVENT ofp_event->SimpleSwitch13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 ff:ff:ff:ff:ff:ff 1
    EVENT ofp_event->SimpleSwitch13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:02 00:00:00:00:00:01 2
    EVENT ofp_event->SimpleSwitch13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 00:00:00:00:00:02 1


1つ目のPacket-Inは、ホスト1が発行したARP requestで、ブロードキャストなので
フローエントリは登録されず、Packet-Outのみが発行されます。

2つ目は、ホスト2から返されたARP replyで、宛先MACアドレスがホスト1となって
いるので前述のフローエントリ(1)が登録されます。

3つ目は、ホスト1からホスト2へ送信されたICMP echo requestで、フローエントリ
(2)が登録されます。

ホスト2からホスト1に返されたICMP echo replyは、登録済みのフローエントリ(1)
にマッチするため、Packet-Inは発行されずにホスト1へ転送されます。


最後に各ホストで実行したtcpdumpの出力を見てみます。

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h1-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h1-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes
    20:38:04.625473 00:00:00:00:00:01 > ff:ff:ff:ff:ff:ff, ethertype ARP (0x0806), length 42: Request who-has 10.0.0.2 tell 10.0.0.1, length 28
    20:38:04.678698 00:00:00:00:00:02 > 00:00:00:00:00:01, ethertype ARP (0x0806), length 42: Reply 10.0.0.2 is-at 00:00:00:00:00:02, length 28
    20:38:04.678731 00:00:00:00:00:01 > 00:00:00:00:00:02, ethertype IPv4 (0x0800), length 98: 10.0.0.1 > 10.0.0.2: ICMP echo request, id 3940, seq 1, length 64
    20:38:04.722973 00:00:00:00:00:02 > 00:00:00:00:00:01, ethertype IPv4 (0x0800), length 98: 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 3940, seq 1, length 64


ホスト1では、最初にARP requestがブロードキャストされていて、続いてホスト2から
返されたARP replyを受信しています。
次にホスト1が発行したICMP echo request、ホスト2から返されたICMP echo replyが
受信されています。

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h2-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h2-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes
    20:38:04.637987 00:00:00:00:00:01 > ff:ff:ff:ff:ff:ff, ethertype ARP (0x0806), length 42: Request who-has 10.0.0.2 tell 10.0.0.1, length 28
    20:38:04.638059 00:00:00:00:00:02 > 00:00:00:00:00:01, ethertype ARP (0x0806), length 42: Reply 10.0.0.2 is-at 00:00:00:00:00:02, length 28
    20:38:04.722601 00:00:00:00:00:01 > 00:00:00:00:00:02, ethertype IPv4 (0x0800), length 98: 10.0.0.1 > 10.0.0.2: ICMP echo request, id 3940, seq 1, length 64
    20:38:04.722747 00:00:00:00:00:02 > 00:00:00:00:00:01, ethertype IPv4 (0x0800), length 98: 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 3940, seq 1, length 64


ホスト2では、ホスト1が発行したARP requestを受信し、ホスト1にARP replyを
返しています。続いて、ホスト1からのICMP echo requestを受信し、ホスト1に
echo replyを返しています。

host: h3:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h3-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h3-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes
    20:38:04.637954 00:00:00:00:00:01 > ff:ff:ff:ff:ff:ff, ethertype ARP (0x0806), length 42: Request who-has 10.0.0.2 tell 10.0.0.1, length 28


ホスト3では、最初にホスト1がブロードキャストしたARP requestのみを受信
しています。



まとめ
------

本章では、簡単なスイッチングハブの実装を題材に、Ryuアプリケーションの実装
の基本的な手順と、OpenFlowによるOpenFlowスイッチの簡単な制御方法について
説明しました。

