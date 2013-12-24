OF-Configライブラリ
===================

本章では、Ryuに付属しているOF-Configのクライアントライブラリについて
紹介します。

OF-Configプロトコル
-------------------

OF-ConfigはOpenFlowスイッチ(OF-Configサーバー)の管理のための
プロトコルです。
OpenFlowと同じONFが策定したもので、以下のサイトから仕様が入手できます。

https://www.opennetworking.org/sdn-resources/onf-specifications/openflow-config

本ライブラリはOF-Config 1.1.1に準拠しています。

OF-ConfigはNETCONF(RFC 6241)のスキーマとして定義されており、
論理スイッチ、ポート、キューなどの状態取得や設定を行なうことができます。

.. NOTE::
    現在Open vSwitchはOF-Configをサポートしていませんが、
    同じ目的のためにOVSDBというサービスを提供しています。
    OF-Configは比較的新しい規格で、Open vSwitchがOVSDBを
    実装したときにはまだ存在していませんでした。

    OVSDBプロトコルはRFC 7047として仕様が公開されていますが、
    事実上Open vSwitch専用のプロトコルとなっています。
    OF-Configはまだ登場から日が浅いですが、将来的に
    多くのOpenFlowスイッチで実装されることが期待されます。

ライブラリ構成
--------------

ryu.lib.of_config.capable_switch.OFCapableSwitchクラス
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

NETCONFセッションを扱うためのクラスです。

.. rst-class:: sourcecode

::

        from ryu.lib.of_config.capable_switch import OFCapableSwitch

ryu.lib.of_config.classesモジュール
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

設定内容をpythonオブジェクトとして扱うためのクラス群を提供する
モジュールです。

.. NOTE::
    クラス名は基本的にOF-Config 1.1.1のyang specification上の
    groupingキーワードで使われている名前と同じです。
    例. OFPortType

.. rst-class:: sourcecode

::

        import ryu.lib.of_config.classes as ofc

使用例
------

スイッチへの接続
^^^^^^^^^^^^^^^^

SSHトランスポートを使用してスイッチに接続します。
unknown_host_cbには、不明なSSHホスト鍵の処理を行なうコールバック関数を
指定しますが、ここでは無条件に接続を継続するようにしています。

.. rst-class:: sourcecode

::

        sess = OFCapableSwitch(
            host='localhost',
            port=1830,
            username='linc',
            password='linc',
            unknown_host_cb=lambda host, fingeprint: True)

GET
^^^

NETCONF GETを使用して状態を取得する例です。
全てのポートの
/resources/port/resource-idと
/resources/port/current-rateを表示します。

.. rst-class:: sourcecode

::

        csw = sess.get()
        for p in csw.resources.port:
            print p.resource_id, p.current_rate

GET-CONFIG
^^^^^^^^^^

NETCONF GET-CONFIGを使用して設定を取得する例です。

.. NOTE::
    runningというのはNETCONFのデータストアで、現在動作している設定です。
    実装によりますが、他にもstartup(デバイスの起動時に読み込まれる設定)
    やcandidate(候補設定)などのデータストアが利用できます。

全てのポートの
/resources/port/resource-idと
/resources/port/configuration/admin-stateを表示します。

.. rst-class:: sourcecode

::

        csw = sess.get_config('running')
        for p in csw.resources.port:
            print p.resource_id, p.configuration.admin_state

EDIT-CONFIG
^^^^^^^^^^^

NETCONF EDIT-CONFIGを使用して設定を変更する例です。
基本的に、GET-CONFIGで取得した設定を編集してEDIT-CONFIGで
送り返す、という手順になります。

.. NOTE::
    プロトコル上はEDIT-CONFIGで設定の部分的な編集を行なうことも
    できますが、このような使い方が無難です。

全てのポートの
/resources/port/configuration/admin-stateをdownに設定します。

.. rst-class:: sourcecode

::

        csw = sess.get_config('running')
        for p in csw.resources.port:
            p.configuration.admin_state = 'down'
        sess.edit_config('running', csw)
