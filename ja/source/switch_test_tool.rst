.. _ch_switch_test_tool:

OpenFlowスイッチテストツール
============================

本章では、OpenFlowスイッチのOpenFlow仕様への準拠の度合いを検証する、Ryuの
OpenFlowスイッチテストツールの使用方法を解説します。


テストツールの概要
------------------

本ツールは、

1. テストパターンファイルに従って試験対象のOpenFlowスイッチに
   対してフローエントリ登録、パケット印加を実施
2. OpenFlowスイッチのパケット編集や転送(または破棄)の処理結果と
   テストパターンファイルに記述された"期待する処理結果"の比較

を行うことにより、OpenFlowスイッチのOpenFlow仕様への準拠の度合いを
検証するテストツールです。

ツールは、OpenFlowバージョン1.3の以下のOpenFlowメッセージの試験に
対応しています。


    ================== ================================
    試験対象メッセージ 対応パラメータ
    ================== ================================
    FlowModメッセージ  match (IN_PHY_PORTを除く)
                                                       
                       actions (SET_QUEUE、GROUPを除く)
    ================== ================================


また印加パケットとして、Ryuのパケットライブラリで定義されたプロトコルを
用いることが出来ます。


動作概要
^^^^^^^^

試験実行イメージ
""""""""""""""""

テストツールを実行した際の動作イメージを示します。テストパターンファイル
には、「登録するフローエントリ」「印加パケット」「期待する処理結果」
が記述されます。また、ツール実行のための環境設定については後述
( `ツール実行環境`_ を参照)します。


    .. only:: latex

       .. image:: images/switch_test_tool/fig1.eps

    .. only:: not latex

       .. image:: images/switch_test_tool/fig1.png



試験結果の出力イメージ
""""""""""""""""""""""

指定されたテストパターンファイルのテスト項目を順番に実行し、試験結果
(OK/ERROR)を出力します。試験結果がERRORの場合はエラー詳細を併せて出力します。


.. rst-class:: console

::

    --- Test start ---

    match: 29_ICMPV6_TYPE
        ethernet/ipv6/icmpv6(type=128)-->'icmpv6_type=128,actions=output:2'               OK
        ethernet/ipv6/icmpv6(type=128)-->'icmpv6_type=128,actions=output:CONTROLLER'      OK
        ethernet/ipv6/icmpv6(type=135)-->'icmpv6_type=128,actions=output:2'               OK
        ethernet/vlan/ipv6/icmpv6(type=128)-->'icmpv6_type=128,actions=output:2'          ERROR
            Received incorrect packet-in: ethernet(ethertype=34525)
        ethernet/vlan/ipv6/icmpv6(type=128)-->'icmpv6_type=128,actions=output:CONTROLLER' ERROR
            Received incorrect packet-in: ethernet(ethertype=34525)
    match: 30_ICMPV6_CODE
        ethernet/ipv6/icmpv6(code=0)-->'icmpv6_code=0,actions=output:2'                   OK
        ethernet/ipv6/icmpv6(code=0)-->'icmpv6_code=0,actions=output:CONTROLLER'          OK
        ethernet/ipv6/icmpv6(code=1)-->'icmpv6_code=0,actions=output:2'                   OK
        ethernet/vlan/ipv6/icmpv6(code=0)-->'icmpv6_code=0,actions=output:2'              ERROR
            Received incorrect packet-in: ethernet(ethertype=34525)
        ethernet/vlan/ipv6/icmpv6(code=0)-->'icmpv6_code=0,actions=output:CONTROLLER'     ERROR
            Received incorrect packet-in: ethernet(ethertype=34525)

    ---  Test end  ---




エラーメッセージ一覧
^^^^^^^^^^^^^^^^^^^^

本ツールで出力されるエラーメッセージの一覧を示します。

========================================================== ======================================
エラーメッセージ                                           説明
========================================================== ======================================
Failed to initialize flow tables: barrier request timeout. 初期化タイムアウトエラー
Failed to initialize flow tables: [err_msg]                初期化時にOpenFlowエラーメッセージ受信
...                                                        ...
========================================================== ======================================




使用方法
--------

テストツールの使用方法を解説します。


テストパターンファイル
^^^^^^^^^^^^^^^^^^^^^^

試験したいテストパターンに応じたテストパターンファイルを作成する必要が
あります。

.. NOTE::

    Ryuのソースツリーにはサンプルテストパターンとして、OpenFlow1.3 FlowMod
    メッセージのmatch/actionsに指定できる各パラメータがそれぞれ正常に動作
    するかを確認するテストパターンファイルが用意されています。

        ryu/tests/switch/of13


テストパターンファイルは拡張子を「.json」としたテキストファイルです。
以下の形式で記述します。


.. rst-class:: sourcecode

::

    [
        "xxxxxxxxxx",                    # 試験項目名
        {
            "description": "xxxxxxxxxx", # 試験内容の説明
            "prerequisite": [
                {
                    "OFPFlowMod": {...}  # 登録するフローエントリ
                },                       # (RyuのOFPFlowModをjson形式で記述)
                {...},
                {...}
            ],
            "tests": [
                {
                    "ingress": [         # 印加するパケット
                        "ethernet(...)", # (Ryuパケットライブラリのコンストラクタの形式で記述)
                        "ipv4(...)",
                        "tcp(...)"
                    ],

                    # 期待する処理結果
                    # 処理結果の種別に応じて(a)(b)(c)のいずれかを記述
                    #  (a) パケット転送(actions=output:X)の確認試験
                    "egress": [          # 期待する転送パケット
                        "ethernet(...)",
                        "ipv4(...)",
                        "tcp(...)"
                    ]
                    #  (b) パケットイン(actions=CONTROLLER)の確認試験
                    "PACKET_IN": [       # 期待するPacket-Inデータ
                        "ethernet(...)",
                        "ipv4(...)",
                        "tcp(...)"
                    ]
                    #  (c) table-missの確認試験
                    "table-miss": [      # table-missとなることを期待するフローテーブルID
                        0
                    ]
                },
                {...},
                {...}
            ]
        },                               # 試験1
        {...},                           # 試験2
        {...}                            # 試験3
    ]



ツール実行環境
^^^^^^^^^^^^^^

テストツール実行のための環境を構築する必要があります。


    .. only:: latex

       .. image:: images/switch_test_tool/fig2.eps
          :scale: 80 %

    .. only:: not latex

       .. image:: images/switch_test_tool/fig2.png
          :scale: 80 %


補助スイッチとして、以下の動作を正常に行うことが出来るOpenFlowスイッチが必要です。

* actions=CONTROLLERのフローエントリ登録

* actions=CONTROLLERのフローエントリによるPacket-Inメッセージ送信

* Packet-Outメッセージ受信によるパケット送信




.. NOTE::

    この環境をmininet上で実現する環境構築スクリプトが、Ryuのソースツリーに
    用意されています。

        ryu/tests/switch/run_mininet.py

    スクリプトの使用例を「 `テストツール使用例`_ 」に記載しています。




テストツールの実行方法
^^^^^^^^^^^^^^^^^^^^^^

テストツールはRyuのソースツリー上で公開されています。

    =============================== ===============================
    ソースコード                    説明
    =============================== ===============================
    ryu/tests/switch/tester.py      テストツール
    ryu/tests/switch/of13           テストパターンファイルのサンプル
    ryu/tests/switch/run_mininet.py 試験環境構築スクリプト
    =============================== ===============================


テストツールは次のコマンドで実行します。

.. rst-class:: console

::

    $ ryu-manager [--test-switch-target DPID] [--test-switch-tester DPID] [--test-switch-dir DIRECTORY] ryu/tests/switch/tester.py

..


    ==================== ======================================== =====================
    オプション           説明                                     デフォルト値
    ==================== ======================================== =====================
    --test-switch-target 試験対象スイッチのデータパスID           0000000000000001
    --test-switch-tester 補助スイッチのデータパスID               0000000000000002
    --test-switch-dir    テストパターンファイルのディレクトリパス ryu/tests/switch/of13
    ==================== ======================================== =====================


ツールを実行すると次のように表示され、試験対象スイッチと補助スイッチが
コントローラに接続されるまで待機します。


.. rst-class:: console

::

    $ ryu-manager ryu/tests/switch/tester.py
    loading app ryu/tests/switch/tester.py
    loading app ryu.controller.ofp_handler
    instantiating app ryu.controller.ofp_handler of OFPHandler
    instantiating app ryu/tests/switch/tester.py of OfTester
    target_dpid=0000000000000001
    tester_dpid=0000000000000002
    Test files directory = ryu/tests/switch/of13
    --- Test start ---
    waiting for switches connection...


試験対象スイッチと補助スイッチがコントローラに接続されると、試験が開始されます。


.. rst-class:: console

::

    $ ryu-manager ryu/tests/switch/tester.py
    loading app ryu/tests/switch/tester.py
    loading app ryu.controller.ofp_handler
    instantiating app ryu.controller.ofp_handler of OFPHandler
    instantiating app ryu/tests/switch/tester.py of OfTester
    target_dpid=0000000000000001
    tester_dpid=0000000000000002
    Test files directory = ryu/tests/switch/of13
    --- Test start ---
    waiting for switches connection...
    dpid=0000000000000002 : Join tester SW.
    dpid=0000000000000001 : Join target SW.
    action: 00_OUTPUT
        ethernet/ipv4/tcp-->'actions=output:2'      OK
        ethernet/ipv6/tcp-->'actions=output:2'      OK
        ethernet/arp-->'actions=output:2'           OK




テストツール使用例
------------------

XXXを例に、オリジナルのテストパターンファイルを作成しテストツールを
実行する手順を示します。



テストパターンファイルの作成
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

テストパターンファイルのサンプルを示します。

OpenFlowスイッチがmatch条件としてeth_dstパラメータに対応しているかを
確認する試験サンプルです。match条件にeth_dstを指定するフローエントリを
登録し、match条件に合致するeth_dstが設定されたパケットを印加することで
パケットがフローエントリにmatchし転送されることを期待する試験を記述しています。


ファイル名： ``sample_test_pattern.json``

.. rst-class:: sourcecode

::

    [
        "match: 03_ETH_DST",
        {
            "description":"ethernet(dst='22:22:22:22:22:22')/ipv4/tcp-->'eth_dst=22:22:22:22:22:22,actions=output:2'",
            "prerequisite":[
                {
                    "OFPFlowMod":{
                        "table_id":0,
                        "match":{
                            "OFPMatch":{
                                "oxm_fields":[
                                    {
                                        "OXMTlv":{
                                            "field":"eth_dst",
                                            "value":"22:22:22:22:22:22"
                                        }
                                    }
                                ]
                            }
                        },
                        "instructions":[
                            {
                                "OFPInstructionActions":{
                                    "actions":[
                                        {
                                            "OFPActionOutput":{
                                                "port":2
                                            }
                                        }
                                    ],
                                    "type":4
                                }
                            }
                        ]
                    }
                }
            ],
            "tests":[
                {
                    "ingress":[
                        "ethernet(dst='22:22:22:22:22:22', src='11:11:11:11:11:11', ethertype=2048)",
                        "ipv4(tos=32, proto=6, src='192.168.10.10', dst='192.168.20.20', ttl=64)",
                        "tcp(dst_port=2222, option='\\x00\\x00\\x00\\x00', src_port=11111)",
                        "'\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e'"
                    ],
                    "egress":[
                        "ethernet(dst='22:22:22:22:22:22', src='11:11:11:11:11:11', ethertype=2048)",
                        "ipv4(tos=32, proto=6, src='192.168.10.10', dst='192.168.20.20', ttl=64)",
                        "tcp(dst_port=2222, option='\\x00\\x00\\x00\\x00', src_port=11111)",
                        "'\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e'"
                    ]
                }
            ]
        }
    ]


環境構築
^^^^^^^^

テストツール実行
^^^^^^^^^^^^^^^^

