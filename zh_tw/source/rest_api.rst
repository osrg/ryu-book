.. _ch_rest_api:

REST API
========

本章說明如何新增 REST 於「 :ref:`ch_switching_hub` 」提到的 switching hub 中。

整合 REST API
------------------

Ryu 本身就有提供 WSGI 對應的 Web 伺服器。透過這個機制建立相關的 REST API 可以與其他系統或瀏覽器整合。


.. NOTE::

    WSGI 是 Python 提供用來連結網頁應用程式和網頁伺服器的框架。


安裝包含 REST API 的 Switching Hub 
----------------------------------------------------------

接下來讓我們實際加入兩個先前在「 :ref:`ch_switching_hub` 」說明過的API。

1. MAC address table 取得 API

    取得 Switching hub 中儲存的 MAC address table 內容。
    成對的 MAC address 和連接埠號將以 JSON 的資料形態回傳。

2. MAC address table 註冊 API

    MAC address 和連接埠號成對的新增進 MAC address table，同時加到交換器的 Flow Entry 中。

接下來我們來看看程式碼。


.. rst-class:: sourcecode

.. literalinclude:: sources/simple_switch_rest_13.py


simple_switch_rest_13.py 是用來定義兩個類別。

前者是控制器類別 ``SimpleSwitchController`` ，其中定義收到 HTTP request 時所需要回應的相對方法。

後者是``SimpleSwitchRest13`` 的類別，用來擴充「 :ref:`ch_switching_hub` 」讓它得以更新  MAC address table.

由於在 ``SimpleSwitchRest13`` 中已經有加入 Flow Entry 的功能，因此 FeaturesReply 方法被覆寫 （overridden）並保留 datapath 物件。

安裝 SimpleSwitchRest13 class
----------------------------------------------------------------


.. rst-class:: sourcecode

::

    class SimpleSwitchRest13(simple_switch_13.SimpleSwitch13):

        _CONTEXTS = { 'wsgi': WSGIApplication }
    ...


類別變數 ``_CONTEXT`` 是用來製定 Ryu 中所支援的 WSGI 網頁伺服器所對應的類別。因此我們可以透過 ``wsgi`` Key 來取得 WSGI 網頁伺服器的實體。


.. rst-class:: sourcecode

::

    def __init__(self, *args, **kwargs):
        super(SimpleSwitchRest13, self).__init__(*args, **kwargs)
        self.switches = {}
        wsgi = kwargs['wsgi']
        wsgi.register(SimpleSwitchController, {simple_switch_instance_name : self})
    ...


建構子需要取得 ``WSGIApplication`` 的實體用來註冊 Controller 類別。稍後會有更詳細的說明。
註冊則可以使用 ``register`` 方法。在呼叫 ``register`` 方法的時候，dictionary object 會在名為 ``simple_switch_api_app`` 的 Key 中被傳遞。因此 Controller 的建構子就可以存取到 ``simple_switch_api_app`` 的實體。


.. rst-class:: sourcecode

::

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        super(SimpleSwitchRest13, self).switch_features_handler(ev)
        datapath = ev.msg.datapath
        self.switches[datapath.id] = datapath
        self.mac_to_port.setdefault(datapath.id, {})
    ...


父類別 ``switch_features_handler`` 已經被覆寫（overridden）。
這個方法會在 SwitchFeatures 事件發生時被觸發，從事件物件 ``ev`` 取得 ``datapath`` 物件後存放至``switches`` 變數中。此時 MAC address 的初始值將會設定為空白字典（empty dictionary）形態。


.. rst-class:: sourcecode

::

    def set_mac_to_port(self, dpid, entry):
        mac_table = self.mac_to_port.setdefault(dpid, {})
        datapath = self.switches.get(dpid)

        entry_port = entry['port']
        entry_mac = entry['mac']

        if datapath is not None:
            parser = datapath.ofproto_parser
            if entry_port not in mac_table.values():

                for mac, port in mac_table.items():

                    # from known device to new device
                    actions = [parser.OFPActionOutput(entry_port)]
                    match = parser.OFPMatch(in_port=port, eth_dst=entry_mac)
                    self.add_flow(datapath, 1, match, actions)

                    # from new device to known device
                    actions = [parser.OFPActionOutput(port)]
                    match = parser.OFPMatch(in_port=entry_port, eth_dst=mac)
                    self.add_flow(datapath, 1, match, actions)

                mac_table.update({entry_mac : entry_port})
        return mac_table
    ...


本方法用來註冊 MAC address 和連接埠號至指定的交換器。當 REST API 的 PUT 方法被觸發時，本方法就會被執行。

參數 ``entry`` 則是用來儲存已經註冊的 MAC address 和連結埠的資訊。

參照 MAC address table 的 ``self.mac_to_port`` 資訊，被註冊到交換器的 Flow Entry 將被搜尋。

例如：一個成對的 MAC address 和連接埠號將被登錄在 MAC address table 中。

* 00:00:00:00:00:01, 1

而且成對的 MAC address 和連接埠號將被當作參數 ``entry`` 。

* 00:00:00:00:00:02, 2

最後被加入交換器當中的 Flow Entry 將會如下所示。

* match 條件：in_port = 1, dst_mac = 00:00:00:00:00:02  action：output=2
* match 條件：in_port = 2, dst_mac = 00:00:00:00:00:01  action：output=1

Flow Entry 的加入是透過父類別的 ``add_flow`` 方法達成。最後經由參數 ``entry`` 傳遞的訊息將會被儲存在 MAC address table.

安裝 SimpleSwitchController Class
--------------------------------------------------------------------------

接下來是控制器類別（controller class）中 REST API 的 HTTP request 。 類別名稱是``SimpleSwitchController`` 。


.. rst-class:: sourcecode

::

    class SimpleSwitchController(ControllerBase):
        def __init__(self, req, link, data, **config):
            super(SimpleSwitchController, self).__init__(req, link, data, **config)
            self.simpl_switch_spp = data[simple_switch_instance_name]
    ...


從建構子（constructor）中取得 ``SimpleSwitchRest13`` 的實體。


.. rst-class:: sourcecode

::

    @route('simpleswitch', url, methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def list_mac_table(self, req, **kwargs):

        simple_switch = self.simpl_switch_spp
        dpid = dpid_lib.str_to_dpid(kwargs['dpid'])

        if dpid not in simple_switch.mac_to_port:
            return Response(status=404)

        mac_table = simple_switch.mac_to_port.get(dpid, {})
        body = json.dumps(mac_table)
        return Response(content_type='application/json', body=body)
    ...


這部分是用來實作 REST API 的 URL， 還有其相對定的處理動作。為了結合 URL 和其對應的方法， ``route`` 這個裝飾器將在 Ryu 中被使用。

被裝飾器（Decorator）處理的內容說明如下。

* 第一個參數

    任意的名稱

* 第二個參數

    指定 URL。
    使得 URL 為 http://<伺服器IP>:8080/simpleswitch/mactable/<datapath ID>

* 第三參數

    指定 HTTP 相對應的方法。
    指定 GET 相對應的方法。

* 第四參數

    指定 URL 的形式。
    URL(/simpleswitch/mactable/{dpid}) 中 {dpid} 的部分必須與 ryu/lib/dpid.py 中 ``DPID_PATTERN`` 16 個 16 進味的數字定義相吻合。

當 REST API 被第二參數所指定的 URL 呼叫時，相對的 HTTP GET ``list_mac_table`` 方法就會被觸發。該方法將會取得 {dpid} 中儲存的 data path ID 以得到 MAC address 並轉換成 JSON 的格式進行回傳。

如果連結到 Ryu 的未知交換器 data path ID 被指定時，Ryu 會返回編碼為 404 的回應。


.. rst-class:: sourcecode

::

    @route('simpleswitch', url, methods=['PUT'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def put_mac_table(self, req, **kwargs):

        simple_switch = self.simpl_switch_spp
        dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
        new_entry = eval(req.body)

        if dpid not in simple_switch.mac_to_port:
            return Response(status=404)

        try:
            mac_table = simple_switch.set_mac_to_port(dpid, new_entry)
            body = json.dumps(mac_table)
            return Response(content_type='application/json', body=body)
        except Exception as e:
            return Response(status=500)
    ...


然後是註冊 MAC address table 的 REST API。

URL 跟取得 MAC address table 時的 API 相同，但是 HTTP 在 PUT 的情況下會呼叫 ``put_mac_table`` 方法。這個方法的內部會呼叫 switching hub 實體的 ``set_mac_to_port`` 方法。

當 ``put_mac_table`` 方法產生的例外的時候，回應碼 500 將會被回傳。
同樣的， ``list_mac_table`` 方法在 Ryu 所連接的交換器使用未知的 data path ID 的話，會回傳回應碼 404。

執行包含 REST API 的 Switching Hub
--------------------------------------------------------------------

接著讓我們執行已經加入 REST API 的 switching hub 吧。

首先執行「 :ref:`ch_switching_hub` 」和 Mininet。這邊不要忘了設定交換器的 OpenFlow 版本為 OpenFlow13。接著啟動已經加入 REST API 的 switching hub。


.. rst-class:: console

::

    ryu@ryu-vm:~/ryu/ryu/app$ cd ~/ryu/ryu/app
    ryu@ryu-vm:~/ryu/ryu/app$ sudo ovs-vsctl set Bridge s1 protocols=OpenFlow13
    ryu@ryu-vm:~/ryu/ryu/app$ ryu-manager --verbose ./simple_switch_rest_13.py
    loading app ./simple_switch_rest_13.py
    loading app ryu.controller.ofp_handler
    creating context wsgi
    instantiating app ryu.controller.ofp_handler
    instantiating app ./simple_switch_rest_13.py
    BRICK SimpleSwitchRest13
      CONSUMES EventOFPPacketIn
      CONSUMES EventOFPSwitchFeatures
    BRICK ofp_event
      PROVIDES EventOFPPacketIn TO {'SimpleSwitchRest13': set(['main'])}
      PROVIDES EventOFPSwitchFeatures TO {'SimpleSwitchRest13': set(['config'])}
      CONSUMES EventOFPErrorMsg
      CONSUMES EventOFPPortDescStatsReply
      CONSUMES EventOFPEchoRequest
      CONSUMES EventOFPSwitchFeatures
      CONSUMES EventOFPHello
    (31135) wsgi starting up on http://0.0.0.0:8080/
    connected socket:<eventlet.greenio.GreenSocket object at 0x318c6d0> address:('127.0.0.1', 48914)
    hello ev <ryu.controller.ofp_event.EventOFPHello object at 0x318cc10>
    move onto config mode
    EVENT ofp_event->SimpleSwitchRest13 EventOFPSwitchFeatures
    switch features ev version: 0x4 msg_type 0x6 xid 0x78dd7a72 OFPSwitchFeatures(auxiliary_id=0,capabilities=71,datapath_id=1,n_buffers=256,n_tables=254)
    move onto main mode


上述啟動時的訊息中有一行 「(31135) wsgi starting up on http://0.0.0.0:8080/」 ，這是表示網頁伺服器和埠號8080已經被啟動。

接下來是在 mininet 的 shell 上從 h1 對 h2 執行 ping 的動作。


.. rst-class:: console

::

    mininet> h1 ping -c 1 h2
    PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
    64 bytes from 10.0.0.2: icmp_req=1 ttl=64 time=84.1 ms

    --- 10.0.0.2 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 84.171/84.171/84.171/0.000 ms


這時後會發生三次往 Ryu 方向的 Packet-In 。


.. rst-class:: console

::

    EVENT ofp_event->SimpleSwitchRest13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 ff:ff:ff:ff:ff:ff 1
    EVENT ofp_event->SimpleSwitchRest13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:02 00:00:00:00:00:01 2
    EVENT ofp_event->SimpleSwitchRest13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 00:00:00:00:00:02 1


再來執行 REST API 以便在 switching hub 中取得 MAC table。 
這次我們使用 curl 指令來驅動 REST API。


.. rst-class:: console

::

    ryu@ryu-vm:~$ curl -X GET http://127.0.0.1:8080/simpleswitch/mactable/0000000000000001
    {"00:00:00:00:00:02": 2, "00:00:00:00:00:01": 1}


你會發現 h1 和 h2 的 MAC address table 已經學習並更新完畢。

這次 h1 和 h2 的 MAC address table 提前在執行 ping 之前被設定好。
暫時停止 switching hub 和 mininet 的執行。
然後再次啟動 mininet 並在 OpenFlow 版本設定為 OpenFlow13 之後接著啟動。


.. rst-class:: console

::

    ...
    (26759) wsgi starting up on http://0.0.0.0:8080/
    connected socket:<eventlet.greenio.GreenSocket object at 0x2afe6d0> address:('127.0.0.1', 48818)
    hello ev <ryu.controller.ofp_event.EventOFPHello object at 0x2afec10>
    move onto config mode
    EVENT ofp_event->SimpleSwitchRest13 EventOFPSwitchFeatures
    switch features ev version: 0x4 msg_type 0x6 xid 0x96681337 OFPSwitchFeatures(auxiliary_id=0,capabilities=71,datapath_id=1,n_buffers=256,n_tables=254)
    switch_features_handler inside sub class
    move onto main mode


接著在每個 host 上呼叫 MAC address table 更新的 REST API。 
REST API 呼叫的形式是 {"mac" : "MAC address", "port" : 連接的連接埠號}


.. rst-class:: console

::

    ryu@ryu-vm:~$ curl -X PUT -d '{"mac" : "00:00:00:00:00:01", "port" : 1}' http://127.0.0.1:8080/simpleswitch/mactable/0000000000000001
    {"00:00:00:00:00:01": 1}
    ryu@ryu-vm:~$ curl -X PUT -d '{"mac" : "00:00:00:00:00:02", "port" : 2}' http://127.0.0.1:8080/simpleswitch/mactable/0000000000000001
    {"00:00:00:00:00:02": 2, "00:00:00:00:00:01": 1}


執行上述的指令，h1 和 h2 對應的 Flow Entry 會被加入交換器中。

然後從 h1 對 h2 執行 ping 指令。


.. rst-class:: console

::

    mininet> h1 ping -c 1 h2
    PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
    64 bytes from 10.0.0.2: icmp_req=1 ttl=64 time=4.62 ms

    --- 10.0.0.2 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 4.623/4.623/4.623/0.000 ms


.. rst-class:: console

::

    ...
    move onto main mode
    (28293) accepted ('127.0.0.1', 44453)
    127.0.0.1 - - [19/Nov/2013 19:59:45] "PUT /simpleswitch/mactable/0000000000000001 HTTP/1.1" 200 124 0.002734
    EVENT ofp_event->SimpleSwitchRest13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 ff:ff:ff:ff:ff:ff 1


這時候交換器中已經存在著 Flow Entry。
Packet-In 只會發生在當 h1 到 h2 的 ARP 出現且沒有接連發生的封包交換時。

本章總結
-------------

本章使用 MAC address table 的處理作為題材，來說明如何新增 REST API。
至於其他的練習應用，如果可以做個從網頁直接加入 Flow Entry 的 REST API 將會是一個很好的想法。
