.. _ch_rest_api:

REST連携
========

本章では、「 :ref:`ch_switching_hub` 」で説明したスイッチングハブに、
REST連携の機能を追加します。


REST APIの組み込み
------------------

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


REST API付きスイッチングハブの実装
----------------------
「 :ref:`ch_switching_hub` 」のスイッチングハブにREST APIを追加した
ソースコードです。

.. rst-class:: sourcecode

.. literalinclude:: sources/simple_switch_rest_13.py

simple_switch_rest_13.pyでは、二つのクラスを定義しています。一つ目は、
HTTPリクエストを受けるURLとそれに対応するメソッドを定義するコントローラクラス(SimpleSwitchController)です。
また、二つ目は「 :ref:`ch_switching_hub` 」のスイッチングハブを拡張し、MACアドレステーブルの更新を
行えるようにしたクラス(SimpleSwitchRest13)です。
SimpleSwitchRest13では、任意のタイミングでフローエントリの追加ができるように、
FeatureReplyメソッドをオーバライドし、スイッチングハブのインスタンス内でdatapathオブジェクトを
保持するようにしています。

SimpleSwitchRest13クラスの実装
----------------------
.. rst-class:: sourcecode

::

    class SimpleSwitchRest13(simple_switch_13.SimpleSwitch13):

        _CONTEXTS = { 'wsgi': WSGIApplication }
    ...

クラス変数_CONTEXTで、RyuのWSGI対応Webサーバのクラスを指定しています。これにより、
「wsgi」というキーで、WSGIのWebサーバインスタンスが取得できます。

.. rst-class:: sourcecode

::

    def __init__(self, *args, **kwargs):
        super(SimpleSwitchRest13, self).__init__(*args, **kwargs)
        self.switches = {}
        wsgi = kwargs['wsgi']
        wsgi.register(SimpleSwitchController, {simple_switch_instance_name : self})
    ...

コンストラクタでは、後述するコントローラクラスを登録するために、
WSGIApplicationのインスタンスを取得しています。登録には、registerメソッドを使用します。
registerメソッド実行の際、コントローラのコンストラクタでSimpleSwitchRest13クラスのインスタンスに
アクセスできるように、第2引数で、「simple_switch_api_app」というキー名でインスタンスを保持する
ディクショナリオブジェクトを渡しています。

.. rst-class:: sourcecode

::

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        super(SimpleSwitchRest13, self).switch_features_handler(ev)
        datapath = ev.msg.datapath
        self.switches[datapath.id] = datapath
        self.mac_to_port.setdefault(datapath.id, {})
    ...

親クラスのswitch_features_handlerをオーバライドしています。
このメソッドでは、SwitchFeaturesイベントが発生したタイミングで、
イベントオブジェクトevに格納されたdatapathオブジェクトを取得し、
インスタンス変数switchesに保持しています。
また、このタイミングで、MACアドレステーブルに初期値(空のディクショナリ)をセットしています。


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

REST APIへのリクエスト時に渡されたdatapath IDに対応するスイッチに、
MACアドレスとポートを格納するためのメソッドです。REST APIがPUTで呼ばれた際にこのメソッドが
実行されます。このメソッドでは、引数entryに格納されたMACアドレスと接続ポートのペアと、
self.mac_to_portにすでに保持されているMACアドレスと接続ポートとを組み合わせてフローエントリを作成し、
親クラスのadd_flowメソッドを用いてそのフローエントリをスイッチに登録します。また続いて、
引数entryのMACアドレスとポートは、スイッチングハブ内のMACアドレスとポートアドレステーブルに格納します。

作成されるフローエントリについて、少し説明します。例えば、すでに格納されているMACアドレスと接続ポートが、

・00:00:00:00:00:01, 1

また、このメソッドに渡されたMACアドレスとポートの組が、

・00:00:00:00:00:02, 2

である場合、スイッチに登録されるフローエントリは以下となります。

(1)マッチング条件：in_port = 1, dst_mac = 00:00:00:00:00:02  アクション：output=2

(2)マッチング条件：in_port = 2, dst_mac = 00:00:00:00:00:01  アクション：output=1

なお、今回の実装では、self.mac_to_portにすでに登録済みのポートがこのメソッドに渡された場合は、
フローエントリの設定は行わず、その時点で格納済みのMACアドレスと接続ポートの組を返却するのみとしています。


SimpleSwitchControllerクラスの実装
----------------------
次はREST APIへのHTTPリクエストを受け付けるコントローラクラスです。
クラス名はSimpleSwitchControllerです。
なお、このコンストラクタはWSGIApplicationインスタンスから呼び出されます。

.. rst-class:: sourcecode

::

    class SimpleSwitchController(ControllerBase):
        def __init__(self, req, link, data, **config):
            super(SimpleSwitchController, self).__init__(req, link, data, **config)
            self.simpl_switch_spp = data[simple_switch_instance_name]
    ...

コンストラクタで、SimpleSwitchRest13クラスのインスタンスを取得します。

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

REST APIのURLとそれに対応する処理を実装する部分です。このメソッドとURLとの対応づけに
Ryuで定義されたrouteデコレータを用いています。このデコレータを用いることで、
HTTPリクエストがデコレータの第2引数で指定したURLにマッチした時、list_mac_tableメソッドが
呼ばれるようになります。

なお、デコレータで指定する内容は、それぞれ以下となります。

1. 第1引数

    任意の名前

2. 第2引数

    URLを指定します。
    ここでは、URLがhttp://<サーバIP>:8080/simpleswitch/mactable/<データパスID>
    となるようにします。

3. 第3引数

    HTTPメソッドを指定します。
    ここではGETメソッドを指定しています。

4. 第4引数

    指定箇所の形式を指定します。
    ここでは、URL(/simpleswitch/mactable/{dpid})の{dpid}の部分が、
    ryu/lib/dpid.pyのDPID_PATTERNで規定されたパターン(16桁の16進数値)に合致することを条件としています。

第2引数で指定したURLでREST APIが呼ばれ、その時のHTTPメソッドがGETの場合に、
このlist_mac_tableメソッドが呼ばれます。
このメソッドでは、{dpid}の部分で指定されたデータパスIDに該当するMACアドレステーブルを取得し、
JSON形式に変換後クライアントに返却しています。

なお、Ryuに接続していない未知のスイッチのデータパスIDを指定するとレスポンスコード404を返します。

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

次は、MACアドレステーブルを登録するREST APIです。
URLはMACアドレステーブル取得時のAPIと同じですが、HTTPメソッドがPUTの場合に
このput_mac_tableメソッドが呼ばれます。
このメソッドでは、内部でスイッチングハブインスタンスのset_mac_to_portメソッドを呼び出しています。
なお、put_mac_tableメソッド内で例外が発生した場合、レスポンスコード500のレスポンスを返却します。
また、list_mac_tableメソッドと同様、Ryuに接続していない未知のスイッチのデータパスIDを指定すると
レスポンスコード404を返します。

REST API搭載スイッチングハブの実行
--------------------------
実際に、REST API搭載スイッチングハブを実行してみます。
最初に「 :ref:`ch_switching_hub` 」と同様にMininetを実行します。ここでも
スイッチのOpenFlowバージョンにOpenFlow13を設定することを忘れないでください。
続いて、REST APIを追加したスイッチングハブを起動します。

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

起動時のメッセージの中に、「(31135) wsgi starting up on http://0.0.0.0:8080/」という行がありますが、
これは、Webサーバがポート番号8080で起動したことを表しています。

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

    ryu@ryu-vm:~$ curl -X GET http://127.0.0.1:8080/simpleswitch/mactable/0000000000000001
    {"00:00:00:00:00:02": 2, "00:00:00:00:00:01": 1}

h1とh2の二つのホストがMACアドレステーブル上で学習済みであることがわかります。

今度は、h1,h2の2台のホストをあらかじめMACアドレステーブルに格納し、
pingを実行してみます。いったんスイッチングハブとMininetを停止します。
次に、再度Mininetを起動し、OpenFlowバージョンをOpenFlow13に設定後、
スイッチングハブを起動します。

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

次に、MACアドレステーブル更新用のREST APIを1ホストごとに呼び出します。
REST APIを呼び出す際のデータ形式は、{"mac" : "MACアドレス", "port" : 接続ポート番号}となるようにします。

.. rst-class:: console

::

    ryu@ryu-vm:~$ curl -X PUT -d '{"mac" : "00:00:00:00:00:01", "port" : 1}' http://127.0.0.1:8080/simpleswitch/mactable/0000000000000001
    {"00:00:00:00:00:01": 1}
    ryu@ryu-vm:~$ curl -X PUT -d '{"mac" : "00:00:00:00:00:02", "port" : 2}' http://127.0.0.1:8080/simpleswitch/mactable/0000000000000001
    {"00:00:00:00:00:02": 2, "00:00:00:00:00:01": 1}

これらのコマンド実行の際に、h1,h2に対応したフローエントリがスイッチに登録されます。

続いて、h1からh2へpingを実行します。

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

この時、スイッチにはすでにフローエントリが存在するため、パケットインはh1からh2へのARPリクエストの
時だけ発生し、それ以降のパケットのやりとりについては発生していません。

まとめ
------

本章では、MACアドレステーブルの参照/更新機能の実装追加を題材として、
REST APIの追加方法について説明しました。その他の応用として、スイッチに任意のフローエントリを追加できる
ようなREST APIを作成し、ブラウザから操作できるようにするのもよいのではないでしょうか。
