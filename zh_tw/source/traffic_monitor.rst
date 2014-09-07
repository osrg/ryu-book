.. _ch_traffic_monitor:

流量監控（Traffic Monitor）
============================

本章針對 「 :ref:`ch_switching_hub` 」 提到的 OpenFlow 交換器加入流量監控的功能。

定期檢查網路狀態
--------------------------------

網路已經成為許多服務或業務的基礎建設，所以維護一個穩定的網路環境是必要的。但是網路問題總是不斷的發生。

網路發生異常的時候，必須快速的找到原因，並且儘速恢復原狀。
這不需要多說，正在閱讀本書的人都知道，找出網路的錯誤、發現真正的原因需要清楚地知道網路的狀態。例如：假設網路中特定的連接埠正處於高流量的狀態，不論是因為他是一個不正常的狀態或是任何原因導致，變成一個由於沒有持續監控所發生的問題。

因此，為了網路的安全以及業務的正常運作，持續注意網路的健康狀況是最基本的工作。當然，網路流量的監視並不能夠保證不會發生任何問題。本章將說明如何使用 OpenFlow 來取得相關的統計資訊。

安裝 Traffic Monitor
-----------------------------------

接著說明如何在 「 :ref:`ch_switching_hub` 」 中提到的交換器中加入流量監控的功能。


.. rst-class:: sourcecode

.. literalinclude:: sources/simple_monitor.py


事實上，流量監控功能已經被實作在 SimpleMonitor 類別中並繼承自 SimpleSwitch13 ，所以這邊已經沒有轉送相關的處理功能了。

固定週期處理
^^^^^^^^^^^^^^^^^^^^

透過 Switching Hub 的平行處理，建立一個執行緒並定期的向交換器發出要求以取得統計的資料。


.. rst-class:: sourcecode

::

    from operator import attrgetter
    
    from ryu.app import simple_switch_13
    from ryu.controller import ofp_event
    from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
    from ryu.controller.handler import set_ev_cls
    from ryu.lib import hub

    class SimpleMonitor(simple_switch_13.SimpleSwitch13):

        def __init__(self, *args, **kwargs):
            super(SimpleMonitor, self).__init__(*args, **kwargs)
            self.datapaths = {}
            self.monitor_thread = hub.spawn(self._monitor)

    # ...


在 ``ryu.lib.hub`` 中實作了一些 eventlet wrapper 和基本的類別。這裡我們使用 ``hub.spawn()`` 建立執行緒。但實際上是使用 evernlet 的 green 執行緒。


.. rst-class:: sourcecode

::

    # ...

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)

    # ...


在執行緒中 ``_monitor()`` 方法確保了執行緒可以在每 10 秒的間隔中，不斷的向註冊的交換器發送要求以取得統計資訊。

為了確認連線中的交換器都可以被持續監控， ``EventOFPStateChange`` 就可以用來監測交換器的連線中斷。這個事件偵測是 Ryu 框架所提供的功能，會被觸發在 Datapath 的狀態改變時。

當 Datapath 的狀態變成 ``MAIN_DISPATCHER`` 時，代表交換器已經註冊並正處於被監視的狀態。而狀態變成  ``DEAD_DISPATCHER`` 時代表已經從註冊狀態解除。


.. rst-class:: sourcecode

::

    # ...

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    # ...


定期呼叫 ``_request_stats()`` 以驅動 ``OFPFlowStatsRequest`` 和 ``OFPPortStatsRequest`` 對交換器發出訊息。

``OFPFlowStatsRequest`` 主要用來對交換器的 Flow Entry 取得統計的資料。
對於交換器發出的要求可以使用 table ID、output port、cookie 值和 match 條件來限縮範圍，但是這邊的例子是取得所有的 Flow Entry。

``OFPPortStatsRequest`` 是用來取得關於交換器的連接埠相關資訊以及統計訊息。
使用的時候可以指定連接埠號，這邊使用 ``OFPP_ANY`` 目的是要取得所有的連接埠統計資料。

FlowStats
^^^^^^^^^^^^^^^^^^

為了接收來自交換器的回應，建立一個 event handler 來接受從交換器發送的 FlowStatsReply 訊息。


.. rst-class:: sourcecode

::

    # ...

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body

        self.logger.info('datapath         '
                         'in-port  eth-dst           '
                         'out-port packets  bytes')
        self.logger.info('---------------- '
                         '-------- ----------------- '
                         '-------- -------- --------')
        for stat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match['in_port'],
                                             flow.match['eth_dst'])):
            self.logger.info('%016x %8x %17s %8x %8d %8d',
                             ev.msg.datapath.id,
                             stat.match['in_port'], stat.match['eth_dst'],
                             stat.instructions[0].actions[0].port,
                             stat.packet_count, stat.byte_count)
    # ...


``OPFFlowStatsReply`` 類別的屬性 ``body`` 是 ``OFPFlowStats`` 的列表，當中儲存了每一個 Flow Entry 的統計資訊，並做為 FlowStatsRequest 的回應。

權限為零的 Table-miss Flow 除外的全部 Flow Entry 將會被選擇，通過並符合該 Flow Entry 的封包數和位元數統計資料將會被回傳，並以接收埠號和目的 MAC address 的方式排序。

為了持續的收集以及分析，僅有一部份的資料會被輸出到 log。因此若要進行分析，連結到外部的程式是必須的。在這樣的情況下 ``OFPFlowStatsReply`` 的內容可以被轉換成為 JSON 的格式進行輸出。

可以設定如下格式


.. rst-class:: sourcecode

::

    import json

    # ...

    self.logger.info('%s', json.dumps(ev.msg.to_jsondict(), ensure_ascii=True,
                                      indent=3, sort_keys=True))


上述的設定將會產生結果如下


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

為了接收交換器所回覆的訊息，PortStatsReply 訊息接收的事件接收處理必須要被實作。


.. rst-class:: sourcecode

::

    # ...

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body

        self.logger.info('datapath         port     '
                         'rx-pkts  rx-bytes rx-error '
                         'tx-pkts  tx-bytes tx-error')
        self.logger.info('---------------- -------- '
                         '-------- -------- -------- '
                         '-------- -------- --------')
        for stat in sorted(body, key=attrgetter('port_no')):
            self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d', 
                             ev.msg.datapath.id, stat.port_no,
                             stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                             stat.tx_packets, stat.tx_bytes, stat.tx_errors)


``OPFPortStatsReply`` 類別的屬性 ``body`` 會列出在 ``OFPPortStats`` 中的資料列表。

``OFPPortStats`` 連接埠號儲存接收端的封包數量、位元數量、丟棄封包數量、錯誤數量、frame錯誤數量、overrrun數量、CRC錯誤數量、collection數量等等的統計資訊。

依據連接埠號的排序列出接收的封包數量、接收位元數量、接收錯誤數量、發送封包數量、發送位元數、發送錯誤數量。

執行 Traffic Monitor
--------------------------

接下來實際的執行流量監控。

首先，跟「 :ref:`ch_switching_hub` 」一樣的執行 Mininet。這邊別忘了交換器的 OpenFlow 版本設定為 OpenFlow13。 

下一步，執行流量監控程式。

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


在「 :ref:`ch_switching_hub` 」中，我們使用 ryu-manager 指令來設定 SimpleSwitch13 模組名稱 （ryu.app.simple_switch_13）。
至於這邊則自定 SimpleMonitor 的檔案名稱（./simple_monitor.py）。

在這個時候 Flow Entry 是空白的（Table-miss Flow Entry 沒有被顯示出來），每個連接埠的計數器也都為零。

從 host 1 向 host 2 執行 ping 的指令。

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


封包的轉送、Flow Entry 的註冊狀況，統計資料開始有了變化。

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


Flow Entry 的統計資訊中，在接收埠 1 的 Flow match 流量訊息中，1 個封包，42 個位元組的資訊被記錄下來。接收埠 2 則是 2 個封包，140 個位元組。

連接埠的統計資訊，連接埠 1 的封包接收（rx-pkts）數量為 3，接收位元組（rx-bytes）數量為 102 bytes，連接埠 2 也是 3個封包，182 位元組。

Flow Entry 的統計資訊和連接埠的統計資訊是不可以混為一談的，這是因為 Flow Entry 的統計資訊是記錄 match 的 Entry 所轉送封包的統計資料。也就是說被 Table-miss 觸發的 Packet-In 以及 Packet-Out 轉送封包都不能算在統計資料內。

在這個案例中，host 1 最初的廣播訊息是 ARP request，而 host 2 回覆了 host 1 的 ARP 訊息，host 1 對 host 2 發送了 echo request 總共 3 個封包，這些都是透過觸發 Packet-Out 所傳送的。
因此連接埠的流量會遠大於 Flow Entry 的流量。

本章總結
--------

本章藉由取得統計資料做為題目，嘗試說明下列事項。

* 產生 Ryu 應用程式執行緒的方法
* 取得 Datapath 狀態的改變
* 取得 FlowStats 和 PortStats 資訊的方法
