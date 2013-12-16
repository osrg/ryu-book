.. _ch_switch_test_tool:

OpenFlowスイッチテストツール
============================

本章では、OpenFlowスイッチのOpenFlow仕様への準拠の度合いを検証する、Ryuの
OpenFlowスイッチテストツールの使用方法を解説します。


テストツールの概要
------------------

本ツールは、"テストパターンファイル"に従って試験対象のOpenFlowスイッチに
対してフローエントリ登録・パケット印加を行い、OpenFlowスイッチのパケット
編集や転送(または破棄)の処理結果を確認することにより、OpenFlowスイッチの
OpenFlow仕様への準拠の度合いを検証するテストツールです。

OpenFlowバージョン1.3の以下のメッセージの試験に対応しています。


    ================== ================================
    試験対象メッセージ 対応パラメータ
    ================== ================================
    FlowModメッセージ  match (IN_PHY_PORTを除く)
                                                       
                       actions (SET_QUEUE、GROUPを除く)
    ================== ================================


* 試験実行イメージ

    テストツールを実行した際の動作イメージを示します。ツール実行のための
    環境設定については後述( `環境`_ を参照)します。


    .. only:: latex

       .. image:: images/switch_test_tool/fig1.eps

    .. only:: not latex

       .. image:: images/switch_test_tool/fig1.png



* 試験結果の出力イメージ

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

テストツールはRyuのソースツリー上で公開されています。

    =============================== ===============================
    ソースコード                    説明
    =============================== ===============================
    ryu/tests/switch/tester.py      テストツール
    ryu/tests/switch/of13           テストパターンファイルのサンプル
    ryu/tests/switch/run_mininet.py 試験環境構築スクリプト
    =============================== ===============================






テストパターンファイル
^^^^^^^^^^^^^^^^^^^^^^

テストパターンファイルの拡張子は「.json」としてください。

テストパターンファイルは以下の形式で記述します。


.. rst-class:: sourcecode

::

    [
        "xxxxxxxxxx",                    # 試験項目名
        {
            "description": "xxxxxxxxxx", # 試験項目の説明
            "prerequisite": [
                {
                    "OFPFlowMod": {...}  # 登録するフローエントリ
                },                       # (RyuのOFPFlowMod形式で記述)
                {
                    "OFPFlowMod": {...}
                }
            ],
            "tests": [
                {
                    "ingress": [         # 印加するパケット
                        "ethernet()",
                        "ipv4()",
                        "tcp()"
                    ],

                    # 実施する試験種別に応じて(a)(b)(c)のいずれかを記載
                    #  (a) パケット転送(actions=output:X)の確認試験
                    "egress": [          # 期待する転送パケット
                        "ethernet()",
                        "ipv4()",
                        "tcp()"
                    ]
                    #  (b) パケットイン(actions=CONTROLLER)の確認試験
                    "PACKET_IN": [       # 期待するPacket-Inデータ
                        "ethernet()",
                        "ipv4()",
                        "tcp()"
                    ]
                    #  (c) table-missの確認試験
                    "table-miss": [      # table-missの確認対象のフローテーブルID
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



環境
^^^^

テストツール




テストツール使用例
------------------
