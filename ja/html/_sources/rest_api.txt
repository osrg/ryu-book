.. _ch_rest_api:

REST API
====================

本章では、「 :ref:`ch_switching_hub` 」で説明したスイッチングハブに、
REST APIを追加します。


RyuにおけるREST APIの組み込み
----------------------

Ryuには、WSGIに対応したWebサーバの機能が含まれています。
コントローラにREST APIを付加することで、ブラウザやcurlコマンド等から
コントローラの振る舞いを変えるようなアプリケーションを作成することもできます。

.. NOTE::

    WSGIとは、Pythonにおいて、WebアプリケーションとWebサーバをつなぐための
    統一されたフレームワークのことを指します。


実装するREST API
----------------------
実装するREST APIは以下の二つとします。

1. MACアドレステーブル取得API

    スイッチングハブで保持されているMACアドレステーブルの内容を返却します。
    MACアドレスおよびポート番号の組をJSON形式で返却します。

2. MACアドレステーブル登録API

    REST APIへのパラメータとして入力されたMACアドレスとポート番号の組をMACアドレステーブルに
    登録します。また、あわせてフローエントリの追加も行います。


REST APIの実装
----------------------
「 :ref:`ch_switching_hub` 」のスイッチングハブにREST APIを追加した
ソースコードです。

.. rst-class:: sourcecode

.. literalinclude:: sources/simple_switch_rest_13.py

simple_switch_rest_13.pyでは、HTTPリクエストを受けるURLとそれに対応するメソッドを
定義するコントローラクラス(SimpleSwitchController)と、
「 :ref:`ch_switching_hub` 」のスイッチングハブを拡張し、MACアドレステーブルの更新を
行えるようにしたクラス(SimpleSwitchRest13)の二つを定義しています。
SimpleSwitchRest13では、任意のタイミングでフローエントリの追加ができるように、
FeatureReplyメソッドをオーバライドし、その中でdatapathオブジェクトをスイッチングハブ内で
保持するようにしています。

SimpleSwitchRest13クラスの実装
----------------------
.. rst-class:: sourcecode

::

    class SimpleSwitchRest13(simple_switch_13.SimpleSwitch13):

        _CONTEXTS = { 'wsgi': WSGIApplication }
    ...

辞書型のクラス変数_CONTEXTに、RyuのWSGI対応Webサーバのインスタンスを取得できるようにしています。
WSGIのWebサーバインスタンスを取得する際には、「wsgi」というキーで取得します。

.. rst-class:: sourcecode

::

    def __init__(self, *args, **kwargs):
        super(SimpleSwitchRest13, self).__init__(*args, **kwargs)
        self.switches = {}
        wsgi = kwargs['wsgi']
        wsgi.register(SimpleSwitchController, {simple_switch_instance_name : self})
    ...

コンストラクタでは、WSGIApplicationのインスタンスを取得しています。
また、registerメソッドを使用して、後述するコントローラクラスの登録を行っています。
コントローラクラスの登録時に、コントローラのコンストラクタでSimpleSwitchRest13クラスのインスタンスを
取得できるように、第2引数で、「simple_switch_api_app」というキー名でインスタンスを追加した
ディクショナリオブジェクトを渡しています。

.. rst-class:: sourcecode

::

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        super(SimpleSwitchRest13, self).switch_features_handler(ev)
        datapath = ev.msg.datapath
        self.switches[datapath.id] = datapath
    ...

親クラスのswitch_features_handlerをオーバライドしています。
このメソッドでは、SwitchFeaturesイベントが発生したタイミングで、
イベント内に格納されたdatapathオブジェクトをインスタンス変数switchesに保持するようにしています。

.. rst-class:: sourcecode

::

    def set_mac_to_port(self, dpid, mac_port_dict):
        datapath = self.switches.get(dpid, None)

        if datapath is not None:
            parser = datapath.ofproto_parser
            ports = mac_port_dict.values()
            for in_port in ports:
                for mac, port in mac_port_dict.items():
                    if port != in_port:
                        dst_mac = mac
                        out_port = port
                        actions = [parser.OFPActionOutput(out_port)]
                        match = parser.OFPMatch(in_port=in_port, eth_dst=dst_mac)
                        self.add_flow(datapath, 1, match, actions)

        mac_table = self.mac_to_port.get(dpid, {})
        mac_table.update(mac_port_dict)
        self.mac_to_port[dpid] = mac_table
        return {'status' : 'ok'}
    ...

MACアドレスとポートに対応するスイッチに格納するためのメソッドです。
コントローラクラスからREST APIの呼び出し契機で実行されます。
MACアドレスと接続ポートの組が引数として渡されます。
それらの組が二組以上指定された場合、それぞれのMACアドレスとポートを組み合わせて
フローエントリを作成し、親クラスのadd_flowメソッドを用いてそのフローエントリをスイッチに登録します。
また、指定されたMACアドレスとポートの組はスイッチングハブ内のMACアドレスとポートアドレステーブルに
格納されます。
たとえば、MACアドレスと接続ポートの組が、それぞれ、

・00:00:00:00:00:01, 1

・00:00:00:00:00:02, 2


の場合、

(1)マッチング条件：in_port = 1, dst_mac = 00:00:00:00:00:02  アクション：output=2

(2)マッチング条件：in_port = 2, dst_mac = 00:00:00:00:00:01  アクション：output=1

という二つのフローエントリを追加するようにしています。


SimpleSwitchControllerクラスの実装
----------------------
次はREST APIへのHTTPリクエストを受け付けるコントローラクラスです。
クラス名はSimpleSwitchControllerです。

.. rst-class:: sourcecode

::

    class SimpleSwitchController(ControllerBase):
        def __init__(self, req, link, data, **config):
            super(SimpleSwitchController, self).__init__(req, link, data, **config)
            self.simpl_switch_spp = data[simple_switch_instance_name]
    ...

コンストラクタで、SimpleSwitchRest13クラスのインスタンスを取得します。
なお、このコンストラクタはWSGIApplicationインスタンスから呼び出されます。

.. rst-class:: sourcecode

::

    @route('simpleswitch', url, methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def list_mac_table(self, req, **kwargs):
        simple_switch = self.simpl_switch_spp
        mac_table = {}

        if 'dpid' in kwargs:
            dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
            mac_table = simple_switch.mac_to_port.get(dpid, {})

        body = json.dumps(mac_table)
        return Response(content_type='application/json', body=body)
    ...

REST APIのURLとそれにひもづく処理を実装する部分です。
Ryuで定義されたrouteデコレータを用いることで、REST APIへのHTTPリクエストと
そのリクエストが来た場合に実行するメソッドの対応付けができます。
デコレータへの引数は以下のようにします。

1. 第1引数

    任意の名前

2. 第2引数

    URLを指定します。
    ここでは、URLがhttp://<サーバIP>:8080/v1/simpleswitch/mactable/<データパスID>
    となるようにします。

3. 第3引数

    HTTPメソッドを指定します。
    ここではGETメソッドを指定しています。

4. 第4引数

    指定箇所の形式を指定します。
    ここでは、{dpid}の部分が、dpid.pyのDPID_PATTERNで規定されたパターンに合致することを
    条件としています。

指定したURLでHTTPメソッドがGETの場合に、このlist_mac_tableメソッドが呼ばれます。
このメソッドの中で、スイッチングハブのインスタンスから指定されたデータパスIDに該当する
MACテーブルを取得し、JSON形式に返還後、HTTPレスポンスを返却しています。


.. rst-class:: sourcecode

::

    @route('simpleswitch', url, methods=['PUT'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def put_mac_table(self, req, **kwargs):
        simple_switch = self.simpl_switch_spp
        result = {}
        if 'dpid' in kwargs:
            dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
            mac_table = eval(req.body)
            result = simple_switch.set_mac_to_port(dpid, mac_table)

        body = json.dumps(result)
        return Response(content_type='application/json', body=body)
    ...

次は、MACアドレステーブルを登録するREST APIです。
URLはMACアドレステーブル取得用APIと同じで、HTTPメソッドがPUTの際に
このput_mac_tableメソッドが呼ばれます。このメソッドの中で、スイッチングハブの
set_mac_to_portメソッドを呼び出します。このREST APIへのHTTPリクエスト
パラメータについては後述します。


REST API搭載スイッチングハブの実行
--------------------------
実際に、REST API搭載スイッチングハブを実行してみます。
最初に「 :ref:`ch_switching_hub` 」と同様にMininetを実行します。ここでも
スイッチのOpenFlowバージョンにOpenFlow13を設定することを忘れないでください。

次に、REST APIを追加したスイッチングハブを起動します。

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

次にmininetのシェル上で、h1からh2へpingを発行します。

.. rst-class:: console

::

    mininet> h1 ping -c 1 h2
    PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
    64 bytes from 10.0.0.2: icmp_req=1 ttl=64 time=84.1 ms

    --- 10.0.0.2 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 84.171/84.171/84.171/0.000 ms


この時、Ryuへのパケットインは3回発生しています。

.. rst-class:: console

::

    EVENT ofp_event->SimpleSwitchRest13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 ff:ff:ff:ff:ff:ff 1
    EVENT ofp_event->SimpleSwitchRest13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:02 00:00:00:00:00:01 2
    EVENT ofp_event->SimpleSwitchRest13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 00:00:00:00:00:02 1

ここで、スイッチングハブのMACテーブルを取得するREST APIを実行してみましょう。
REST APIの呼び出しには、curlコマンドを使用します。

.. rst-class:: console

::

    ryu@ryu-vm:~$ curl -X GET http://127.0.0.1:8080/v1/simpleswitch/mactable/0000000000000001
    {"00:00:00:00:00:02": 2, "00:00:00:00:00:01": 1}

h1とh2の二つのホストがMACアドレステーブル上で学習済みであることがわかります。

今度は、h1,h2,h3の3台のホストをあらかじめMACアドレステーブルに格納し、
pingを実行してみることにします。いったんスイッチングハブを停止します。
再度、Mininetを起動し、OpenFlowバージョンをOpenFlow13に設定後、
スイッチングハブの再起動します。

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

ここでMACアドレステーブル更新用のREST APIを呼び出します。

.. rst-class:: console

::

    ryu@ryu-vm:~$ curl -X PUT -d '{"00:00:00:00:00:01": 1, "00:00:00:00:00:02": 2, "00:00:00:00:00:03": 3}' http://127.0.0.1:8080/v1/simpleswitch/mactable/0000000000000001
    {"status": "ok"}

この時、h1,h2,h3に対応したフローエントリがスイッチに登録されます。

次に、再度、h1からh2へpingを実行します。

.. rst-class:: console

::

    mininet> h1 ping -c 1 h2
    PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
    64 bytes from 10.0.0.2: icmp_req=1 ttl=64 time=4.62 ms

    --- 10.0.0.2 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 4.623/4.623/4.623/0.000 ms

この時、すでにスイッチにはフローエントリが存在するため、パケットインのイベントはARPリクエストの
1回だけ発生するようになります。

.. rst-class:: console

::

    ...
    move onto main mode
    (28293) accepted ('127.0.0.1', 44453)
    127.0.0.1 - - [19/Nov/2013 19:59:45] "PUT /v1/simpleswitch/mactable/0000000000000001 HTTP/1.1" 200 124 0.002734
    EVENT ofp_event->SimpleSwitchRest13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 ff:ff:ff:ff:ff:ff 1


まとめ
------

本章では、MACアドレステーブルの参照/更新機能の実装追加を題材として、
REST APIの追加方法について説明しました。その他の応用として、スイッチにフローエントリを追加できる
ようなREST APIを作成し、ブラウザから操作できるようにするのもよいのではないでしょうか。
