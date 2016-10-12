.. _ch_rest_api:

REST連携
========

本章では、「 :ref:`ch_switching_hub` 」で説明したスイッチングハブに、
REST連携の機能を追加します。


REST APIの組み込み
------------------

RyuにはWSGIに対応したWebサーバの機能があります。
この機能を利用することで、他のシステムやブラウザなどとの連携をする際に役に立つ、
REST APIを作成することができます。

.. NOTE::

    WSGIとは、Pythonにおいて、WebアプリケーションとWebサーバをつなぐための
    統一されたフレームワークのことを指します。


REST API付きスイッチングハブの実装
----------------------------------

「 :ref:`ch_switching_hub` 」で説明したスイッチングハブに、次の二つのREST APIを追加してみましょう。

1. MACアドレステーブル取得API

    スイッチングハブが保持しているMACアドレステーブルの内容を返却します。
    MACアドレスおよびポート番号の組をJSON形式で返却します。

2. MACアドレステーブル登録API

    MACアドレスとポート番号の組をMACアドレステーブルに
    登録し、スイッチへフローエントリの追加を行います。


それではソースコードを見てみましょう。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_rest_13.py
    :lines: 16-

simple_switch_rest_13.pyでは、二つのクラスを定義しています。

一つ目は、
HTTPリクエストを受けるURLとそれに対応するメソッドを定義するコントローラクラス ``SimpleSwitchController`` です。

二つ目は「 :ref:`ch_switching_hub` 」を拡張し、MACアドレステーブルの更新を
行えるようにしたクラス ``SimpleSwitchRest13`` です。

``SimpleSwitchRest13`` では、スイッチにフローエントリを追加するため、
FeaturesReplyメソッドをオーバライドし、datapathオブジェクトを
保持しています。

SimpleSwitchRest13クラスの実装
------------------------------

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_rest_13.py
    :pyobject: SimpleSwitchRest13
    :end-before: __init__
    :append: # ...

クラス変数 ``_CONTEXT`` で、RyuのWSGI対応Webサーバのクラスを指定しています。これにより、
``wsgi`` というキーで、WSGIのWebサーバインスタンスが取得できます。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_rest_13.py
    :dedent: 4
    :pyobject: SimpleSwitchRest13.__init__

コンストラクタでは、後述するコントローラクラスを登録するために、
``WSGIApplication`` のインスタンスを取得しています。登録には、 ``register`` メソッドを使用します。
``register`` メソッド実行の際、コントローラのコンストラクタで ``SimpleSwitchRest13`` クラスのインスタンスに
アクセスできるように、 ``simple_switch_api_app`` というキー名で
ディクショナリオブジェクトを渡しています。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_rest_13.py
    :dedent: 4
    :prepend: @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    :pyobject: SimpleSwitchRest13.switch_features_handler

親クラスの ``switch_features_handler`` をオーバライドしています。
このメソッドでは、SwitchFeaturesイベントが発生したタイミングで、
イベントオブジェクト ``ev`` に格納された ``datapath`` オブジェクトを取得し、
インスタンス変数 ``switches`` に保持しています。
また、このタイミングで、MACアドレステーブルに初期値として空のディクショナリをセットしています。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_rest_13.py
    :dedent: 4
    :pyobject: SimpleSwitchRest13.set_mac_to_port

指定のスイッチにMACアドレスとポートを登録するメソッドです。
REST APIがPUTメソッドで呼ばれると実行されます。

引数　``entry`` には、登録をしたいMACアドレスと接続ポートのペアが格納されています。

MACアドレステーブル ``self.mac_to_port`` の情報を参照しながら、
スイッチに登録するフローエントリを求めていきます。

例えば、MACアドレステーブルに、次のMACアドレスと接続ポートのペアが登録されていて、

* 00:00:00:00:00:01, 1

引数 ``entry`` で渡されたMACアドレスとポートのペアが、

* 00:00:00:00:00:02, 2

の場合、スイッチに登録する必要のあるフローエントリは次の通りです。

* マッチング条件：in_port = 1, dst_mac = 00:00:00:00:00:02  アクション：output=2
* マッチング条件：in_port = 2, dst_mac = 00:00:00:00:00:01  アクション：output=1

フローエントリの登録は親クラスの ``add_flow`` メソッドを利用しています。最後に、
引数 ``entry`` で渡された情報をMACアドレステーブルに格納しています。


SimpleSwitchControllerクラスの実装
----------------------------------

次はREST APIへのHTTPリクエストを受け付けるコントローラクラスです。
クラス名は ``SimpleSwitchController`` です。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_rest_13.py
    :pyobject: SimpleSwitchController
    :end-before: @route
    :append: # ...

コンストラクタで、 ``SimpleSwitchRest13`` クラスのインスタンスを取得します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_rest_13.py
    :dedent: 4
    :prepend: @route('simpleswitch', url, methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    :pyobject: SimpleSwitchController.list_mac_table

REST APIのURLとそれに対応する処理を実装する部分です。このメソッドとURLとの対応づけに
Ryuで定義された ``route`` デコレータを用いています。

デコレータで指定する内容は、次の通りです。

* 第1引数

    任意の名前

* 第2引数

    URLを指定します。
    URLがhttp://<サーバIP>:8080/simpleswitch/mactable/<データパスID>
    となるようにします。

* 第3引数

    HTTPメソッドを指定します。
    GETメソッドを指定しています。

* 第4引数

    指定箇所の形式を指定します。
    URL(/simpleswitch/mactable/{dpid})の{dpid}の部分が、
    ryu/lib/dpid.pyの ``DPID_PATTERN`` で定義された16桁の16進数値の表現に合致することを条件としています。

第2引数で指定したURLでREST APIが呼ばれ、その時のHTTPメソッドがGETの場合に、
``list_mac_table`` メソッドが呼ばれます。
このメソッドは、{dpid}の部分で指定されたデータパスIDに該当するMACアドレステーブルを取得し、
JSON形式に変換し呼び出し元に返却しています。

なお、Ryuに接続していない未知のスイッチのデータパスIDを指定するとレスポンスコード404を返します。

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_rest_13.py
    :dedent: 4
    :prepend: @route('simpleswitch', url, methods=['PUT'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    :pyobject: SimpleSwitchController.put_mac_table

次は、MACアドレステーブルを登録するREST APIです。

URLはMACアドレステーブル取得時のAPIと同じですが、HTTPメソッドがPUTの場合に
``put_mac_table`` メソッドが呼ばれます。
このメソッドでは、内部でスイッチングハブインスタンスの ``set_mac_to_port`` メソッドを呼び出しています。
なお、 ``put_mac_table`` メソッド内で例外が発生した場合、レスポンスコード500を返却します。
また、 ``list_mac_table`` メソッドと同様、Ryuに接続していない未知のスイッチのデータパスIDを指定すると
レスポンスコード404を返します。

REST API搭載スイッチングハブの実行
----------------------------------

REST APIを追加したスイッチングハブを実行してみましょう。

最初に「 :ref:`ch_switching_hub` 」と同様にMininetを実行します。ここでも
スイッチのOpenFlowバージョンにOpenFlow13を設定することを忘れないでください。
続いて、REST APIを追加したスイッチングハブを起動します。

.. rst-class:: console

::

    $ sudo ovs-vsctl set Bridge s1 protocols=OpenFlow13
    $ ryu-manager --verbose ryu.app.simple_switch_rest_13
    loading app ryu.app.simple_switch_rest_13
    loading app ryu.controller.ofp_handler
    creating context wsgi
    instantiating app ryu.app.simple_switch_rest_13 of SimpleSwitchRest13
    instantiating app ryu.controller.ofp_handler of OFPHandler
    BRICK SimpleSwitchRest13
      CONSUMES EventOFPPacketIn
      CONSUMES EventOFPSwitchFeatures
    BRICK ofp_event
      PROVIDES EventOFPPacketIn TO {'SimpleSwitchRest13': set(['main'])}
      PROVIDES EventOFPSwitchFeatures TO {'SimpleSwitchRest13': set(['config'])}
      CONSUMES EventOFPSwitchFeatures
      CONSUMES EventOFPPortDescStatsReply
      CONSUMES EventOFPErrorMsg
      CONSUMES EventOFPEchoRequest
      CONSUMES EventOFPEchoReply
      CONSUMES EventOFPHello
      CONSUMES EventOFPPortStatus
    (24728) wsgi starting up on http://0.0.0.0:8080
    connected socket:<eventlet.greenio.base.GreenSocket object at 0x7f2daf3d7850> address:('127.0.0.1', 37968)
    hello ev <ryu.controller.ofp_event.EventOFPHello object at 0x7f2daf38c890>
    move onto config mode
    EVENT ofp_event->SimpleSwitchRest13 EventOFPSwitchFeatures
    switch features ev version=0x4,msg_type=0x6,msg_len=0x20,xid=0x86fc9d2f,OFPSwitchFeatures(auxiliary_id=0,capabilities=79,datapath_id=1,n_buffers=256,n_tables=254)
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


この時、RyuへのPacket-Inは3回発生しています。

.. rst-class:: console

::

    EVENT ofp_event->SimpleSwitchRest13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 ff:ff:ff:ff:ff:ff 1
    EVENT ofp_event->SimpleSwitchRest13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:02 00:00:00:00:00:01 2
    EVENT ofp_event->SimpleSwitchRest13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 00:00:00:00:00:02 1

ここで、スイッチングハブのMACテーブルを取得するREST APIを実行してみましょう。
今回は、REST APIの呼び出しにcurlコマンドを使用します。

.. rst-class:: console

::

    $ curl -X GET http://127.0.0.1:8080/simpleswitch/mactable/0000000000000001
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

    $ curl -X PUT -d '{"mac" : "00:00:00:00:00:01", "port" : 1}' http://127.0.0.1:8080/simpleswitch/mactable/0000000000000001
    {"00:00:00:00:00:01": 1}
    $ curl -X PUT -d '{"mac" : "00:00:00:00:00:02", "port" : 2}' http://127.0.0.1:8080/simpleswitch/mactable/0000000000000001
    {"00:00:00:00:00:02": 2, "00:00:00:00:00:01": 1}

これらのコマンドを実行すると、h1,h2に対応したフローエントリがスイッチに登録されます。

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

この時、スイッチにはすでにフローエントリが存在するため、Packet-Inはh1からh2へのARPリクエストの
時だけ発生し、それ以降のパケットのやりとりでは発生していません。

まとめ
------

本章では、MACアドレステーブルの参照や更新をする機能を題材として、
REST APIの追加方法について説明しました。その他の応用として、スイッチに任意のフローエントリを追加できる
ようなREST APIを作成し、ブラウザから操作できるようにするのもよいのではないでしょうか。

