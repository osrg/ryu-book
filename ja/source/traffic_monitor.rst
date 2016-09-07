.. _ch_traffic_monitor:

トラフィックモニター
====================

本章では、「 :ref:`ch_switching_hub` 」で説明したスイッチングハブに、OpenFlowスイッチ
の統計情報をモニターする機能を追加します。


ネットワークの定期健診
----------------------

ネットワークは既に多くのサービスや業務のインフラとなっているため、正常で
安定した稼働が維持されることが求められます。とは言え、いつも何かしらの問題
が発生するものです。

ネットワークに異常が発生した場合、迅速に原因を特定し、復旧させなければなり
ません。本書をお読みの方には言うまでもないことと思いますが、異常を検出し、
原因を特定するためには、日頃からネットワークの状態を把握しておく必要があり
ます。例えば、あるネットワーク機器のポートのトラフィック量が非常に高い値を
示していたとして、それが異常な状態なのか、いつもそうなのか、あるいはいつから
そうなったのかということは、継続してそのポートのトラフィック量を測っていな
ければ判断することができません。

というわけで、ネットワークの健康状態を常に監視しつづけるということは、その
ネットワークを使うサービスや業務の継続的な安定運用のためにも必須となります。
もちろん、トラフィック情報の監視さえしていれば万全などということはありませ
んが、本章ではOpenFlowによるスイッチの統計情報の取得方法について説明します。


トラフィックモニターの実装
--------------------------

早速ですが、「 :ref:`ch_switching_hub` 」で説明したスイッチングハブにトラフィック
モニター機能を追加したソースコードです。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_monitor_13.py
    :lines: 16-

SimpleSwitch13を継承したSimpleMonitorクラスに、トラフィックモニター機能を
実装していますので、ここにはパケット転送に関する処理は出てきません。


定周期処理
^^^^^^^^^^

スイッチングハブの処理と並行して、定期的に統計情報取得のリクエストをOpenFlow
スイッチへ発行するために、スレッドを生成します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_monitor_13.py
    :pyobject: SimpleMonitor13
    :end-before: set_ev_cls
    :append: # ...

``ryu.lib.hub`` には、いくつかのeventletのラッパーや基本的なクラスの実装
があります。ここではスレッドを生成する ``hub.spawn()`` を使用します。
実際に生成されるスレッドはeventletのグリーンスレッドです。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_monitor_13.py
    :dedent: 4
    :prepend: # ...
    :pyobject: SimpleMonitor13
    :start-after: self.monitor_thread = hub.spawn(self._monitor)
    :end-before: def _request_stats(self, datapath):
    :append: # ...

スレッド関数 ``_monitor()`` では、登録されたスイッチに対する統計情報取得
リクエストの発行を10秒間隔で無限に繰り返します。

接続中のスイッチを監視対象とするため、スイッチの接続および切断の検出に
``EventOFPStateChange`` イベントを利用しています。このイベントはRyuフレーム
ワークが発行するもので、Datapathのステートが変わったときに発行されます。

ここでは、Datapathのステートが ``MAIN_DISPATCHER`` になった時にそのスイッチ
を監視対象に登録、 ``DEAD_DISPATCHER`` になった時に登録の削除を行っています。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_monitor_13.py
    :dedent: 4
    :pyobject: SimpleMonitor13._request_stats

定期的に呼び出される ``_request_stats()`` では、スイッチに
``OFPFlowStatsRequest`` と ``OFPPortStatsRequest`` を発行しています。

``OFPFlowStatsRequest`` は、フローエントリに関する統計情報をスイッチに要求します。
テーブルID、出力ポート、cookie値、マッチの条件などで要求対象のフローエントリ
を絞ることができますが、ここではすべてのフローエントリを対象としています。

``OFPPortStatsRequest`` は、ポートに関する統計情報をスイッチに要求します。
取得したいポートの番号を指定することが出来ます。ここでは ``OFPP_ANY`` を指定し、
すべてのポートの統計情報を要求しています。


FlowStats
^^^^^^^^^
スイッチからの応答を受け取るため、FlowStatsReplyメッセージを受信するイベントハンドラを作成します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_monitor_13.py
    :dedent: 4
    :prepend: @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    :pyobject: SimpleMonitor13._flow_stats_reply_handler

``OPFFlowStatsReply`` クラスの属性 ``body`` は、 ``OFPFlowStats`` のリストで、
FlowStatsRequestの対象となった各フローエントリの統計情報が格納されています。

プライオリティが0のTable-missフローを除いて、全てのフローエントリ
を選択しています。受信ポートと宛先MACアドレスでソートして、それぞれのフローエントリに
マッチしたパケット数とバイト数を出力しています。

なお、ここでは一部の数値をログに出しているだけですが、継続的に情報
を収集、分析するには、外部プログラムとの連携が必要になるでしょう。そのような
場合、 ``OFPFlowStatsReply`` の内容をJSONフォーマットに変換することができます。

例えば次のように書くことができます。

.. rst-class:: sourcecode

::

    import json

    # ...

    self.logger.info('%s', json.dumps(ev.msg.to_jsondict(), ensure_ascii=True,
                                      indent=3, sort_keys=True))

この場合、以下のように出力されます。

.. rst-class:: console

::

    {
       "OFPFlowStatsReply": {
          "body": [
             {
                "OFPFlowStats": {
                   "byte_count": 0, 
                   "cookie": 0, 
                   "duration_nsec": 680000000, 
                   "duration_sec": 4, 
                   "flags": 0, 
                   "hard_timeout": 0, 
                   "idle_timeout": 0, 
                   "instructions": [
                      {
                         "OFPInstructionActions": {
                            "actions": [
                               {
                                  "OFPActionOutput": {
                                     "len": 16, 
                                     "max_len": 65535, 
                                     "port": 4294967293, 
                                     "type": 0
                                  }
                               }
                            ], 
                            "len": 24, 
                            "type": 4
                         }
                      }
                   ], 
                   "length": 80, 
                   "match": {
                      "OFPMatch": {
                         "length": 4, 
                         "oxm_fields": [], 
                         "type": 1
                      }
                   }, 
                   "packet_count": 0, 
                   "priority": 0, 
                   "table_id": 0
                }
             }, 
             {
                "OFPFlowStats": {
                   "byte_count": 42, 
                   "cookie": 0, 
                   "duration_nsec": 72000000, 
                   "duration_sec": 57, 
                   "flags": 0, 
                   "hard_timeout": 0, 
                   "idle_timeout": 0, 
                   "instructions": [
                      {
                         "OFPInstructionActions": {
                            "actions": [
                               {
                                  "OFPActionOutput": {
                                     "len": 16, 
                                     "max_len": 65509, 
                                     "port": 1, 
                                     "type": 0
                                  }
                               }
                            ], 
                            "len": 24, 
                            "type": 4
                         }
                      }
                   ], 
                   "length": 96, 
                   "match": {
                      "OFPMatch": {
                         "length": 22, 
                         "oxm_fields": [
                            {
                               "OXMTlv": {
                                  "field": "in_port", 
                                  "mask": null, 
                                  "value": 2
                               }
                            }, 
                            {
                               "OXMTlv": {
                                  "field": "eth_dst", 
                                  "mask": null, 
                                  "value": "00:00:00:00:00:01"
                               }
                            }
                         ], 
                         "type": 1
                      }
                   }, 
                   "packet_count": 1, 
                   "priority": 1, 
                   "table_id": 0
                }
             }
          ], 
          "flags": 0, 
          "type": 1
       }
    }


PortStats
^^^^^^^^^

スイッチからの応答を受け取るため、PortStatsReplyメッセージを受信するイベントハンドラを作成します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_monitor_13.py
    :dedent: 4
    :prepend: @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    :pyobject: SimpleMonitor13._port_stats_reply_handler

``OPFPortStatsReply`` クラスの属性 ``body`` は、``OFPPortStats`` のリストになって
います。

``OFPPortStats`` には、ポート番号、送受信それぞれのパケット数、バイト数、ドロップ
数、エラー数、フレームエラー数、オーバーラン数、CRCエラー数、コリジョン数など
の統計情報が格納されます。

ここでは、ポート番号でソートし、受信パケット数、受信バイト数、受信エラー数、
送信パケット数、送信バイト数、送信エラー数を出力しています。


トラフィックモニターの実行
--------------------------

それでは、実際にこのトラフィックモニターを実行してみます。

まず、「 :ref:`ch_switching_hub` 」と同様にMininetを実行します。ここで、
スイッチのOpenFlowバージョンにOpenFlow13を設定することを忘れないでください。

次にいよいよトラフィックモニターの実行です。

controller: c0:

.. rst-class:: console

::

    ryu@ryu-vm:~# ryu-manager --verbose ./simple_monitor.py
    loading app ./simple_monitor.py
    loading app ryu.controller.ofp_handler
    instantiating app ./simple_monitor.py
    instantiating app ryu.controller.ofp_handler
    BRICK SimpleMonitor
      CONSUMES EventOFPStateChange
      CONSUMES EventOFPFlowStatsReply
      CONSUMES EventOFPPortStatsReply
      CONSUMES EventOFPPacketIn
      CONSUMES EventOFPSwitchFeatures
    BRICK ofp_event
      PROVIDES EventOFPStateChange TO {'SimpleMonitor': set(['main', 'dead'])}
      PROVIDES EventOFPFlowStatsReply TO {'SimpleMonitor': set(['main'])}
      PROVIDES EventOFPPortStatsReply TO {'SimpleMonitor': set(['main'])}
      PROVIDES EventOFPPacketIn TO {'SimpleMonitor': set(['main'])}
      PROVIDES EventOFPSwitchFeatures TO {'SimpleMonitor': set(['config'])}
      CONSUMES EventOFPErrorMsg
      CONSUMES EventOFPPortDescStatsReply
      CONSUMES EventOFPHello
      CONSUMES EventOFPEchoRequest
      CONSUMES EventOFPSwitchFeatures
    connected socket:<eventlet.greenio.GreenSocket object at 0x343fb10> address:('127.0.0.1', 55598)
    hello ev <ryu.controller.ofp_event.EventOFPHello object at 0x343fed0>
    move onto config mode
    EVENT ofp_event->SimpleMonitor EventOFPSwitchFeatures
    switch features ev version: 0x4 msg_type 0x6 xid 0x7dd2dc58 OFPSwitchFeatures(auxiliary_id=0,capabilities=71,datapath_id=1,n_buffers=256,n_tables=254)
    move onto main mode
    EVENT ofp_event->SimpleMonitor EventOFPStateChange
    register datapath: 0000000000000001
    send stats request: 0000000000000001
    EVENT ofp_event->SimpleMonitor EventOFPFlowStatsReply
    datapath         in-port  eth-dst           out-port packets  bytes
    ---------------- -------- ----------------- -------- -------- --------
    EVENT ofp_event->SimpleMonitor EventOFPPortStatsReply
    datapath         port     rx-pkts  rx-bytes rx-error tx-pkts  tx-bytes tx-error
    ---------------- -------- -------- -------- -------- -------- -------- --------
    0000000000000001        1        0        0        0        0        0        0
    0000000000000001        2        0        0        0        0        0        0
    0000000000000001        3        0        0        0        0        0        0
    0000000000000001 fffffffe        0        0        0        0        0        0

「 :ref:`ch_switching_hub` 」では、ryu-managerコマンド
にSimpleSwitch13のモジュール名(ryu.app.simple_switch_13)を指定しましたが、
ここでは、SimpleMonitorのファイル名(./simple_monitor.py)を指定しています。

この時点では、フローエントリが無く(Table-missフローエントリは表示して
いません)、各ポートのカウントもすべて0です。

ホスト1からホスト2へpingを実行してみましょう。

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ping -c1 10.0.0.2
    PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
    64 bytes from 10.0.0.2: icmp_req=1 ttl=64 time=94.4 ms

    --- 10.0.0.2 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 94.489/94.489/94.489/0.000 ms
    root@ryu-vm:~# 

パケットの転送や、フローエントリが登録され、統計情報
が変化します。

controller: c0:

.. rst-class:: console

::

    datapath         in-port  eth-dst           out-port packets  bytes
    ---------------- -------- ----------------- -------- -------- --------
    0000000000000001        1 00:00:00:00:00:02        2        1       42
    0000000000000001        2 00:00:00:00:00:01        1        2      140
    datapath         port     rx-pkts  rx-bytes rx-error tx-pkts  tx-bytes tx-error
    ---------------- -------- -------- -------- -------- -------- -------- --------
    0000000000000001        1        3      182        0        3      182        0
    0000000000000001        2        3      182        0        3      182        0
    0000000000000001        3        0        0        0        1       42        0
    0000000000000001 fffffffe        0        0        0        1       42        0

フローエントリの統計情報では、受信ポート1のフローにマッチしたトラフィッ
クは、1パケット、42バイトと記録されています。受信ポート2では、2パケット、140
バイトとなっています。

ポートの統計情報では、ポート1の受信パケット数(rx-pkts)は3、受信バイト数
(rx-bytes)は182バイト、ポート2も3パケット、182バイトとなっています。

フローエントリの統計情報とポートの統計情報で数字が合っていませんが、これは
フローエントリの統計情報は、そのエントリにマッチし転送されたパケットの情報だから
です。つまり、Table-missによりPacket-Inを発行し、Packet-Outで転送された
パケットは、この統計の対象になっていないためです。

このケースでは、ホスト1が最初にブロードキャストしたARPリクエスト、ホスト2が
ホスト1に返したARPリプライ、ホスト1がホスト2へ発行したecho requestの3パケット
が、Packet-Outによって転送されています。
そのため、ポートの統計量は、フローエントリの統計量よりも多くなっています。


まとめ
------

本章では、統計情報の取得機能を題材として、以下の項目について
説明しました。

* Ryuアプリケーションでのスレッドの生成方法
* Datapathの状態遷移の捕捉
* FlowStatsおよびPortStatsの取得方法

