OF-Config 函式庫
================

本章將介紹 Ryu 內建的 OF-Config 客戶端函式庫。

OF-Config 通訊協定
--------------------------------------

OF-Config 是用來管理 OpenFlow 交換器的一個通訊協定。
OF-Config 通訊協定被定義在 NETCONF（ RFC 6241 ）的標準中，它可以對邏輯交換器的通訊埠（ Port ）和佇列（ Queue ）進行設定以及資料擷取。

OF-Config 是被同樣制訂 OpenFlow 的 ONF（ Open Network Foundation ）所研擬，請參考下列資料以取得更詳盡的資訊。

https://www.opennetworking.org/sdn-resources/onf-specifications/openflow-config

Ryu 提供的函式庫完全相容于 OF-Config 1.1.1 版本


.. NOTE::

    目前 Open vSwitch 並不支援 OF-Config，僅提供 OVSDB 作為替代使用。
    由於 OF-Config 還算是比較新的規格，因此 Open vSwitch 的 OVSDB 並不實作 OF-Config。

    OVSDB 通訊協定雖然公開規範在 RFC 7047 作為標準，但事實上目前僅作為 Open vSwitch 專用的通訊協定。
    而 OF-Config 相對來說還是相對新的協定，期望在不久的將來會有更多實作它的 OpenFlow 交換器出現。


函式庫架構
----------------------------

ryu.lib.of_config.capable_switch.OFCapableSwitch Class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

本 Class 主要用來處理 NETCONF 會話（ Session ）。


.. rst-class:: sourcecode

::

        from ryu.lib.of_config.capable_switch import OFCapableSwitch


ryu.lib.of_config.classes 模組（ Module ）
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

本模組用來將協定相關的設定對應至 Python 物件。


.. NOTE::

    類別名稱基本上遵照 OF-Config 1.1.1 中 yang specification 的 Grouping 關鍵字名稱來命名。

    例如：OFPortType


.. rst-class:: sourcecode

::

        import ryu.lib.of_config.classes as ofc


使用範例
------------------

交換器的連結
^^^^^^^^^^^^^^^^

使用 SSH Transport 連線到交換器。
回呼（ callback ）函式 unknown_host_cb 是用來對應未知的 SSH Host Key 時所被執行的函式。
下面的範例中我們使用無條件信任對方並繼續進行連結。


.. rst-class:: sourcecode

::

        sess = OFCapableSwitch(
            host='localhost',
            port=1830,
            username='linc',
            password='linc',
            unknown_host_cb=lambda host, fingeprint: True)


GET
^^^^^^

使用 NETCONF GET 來取得交換器的狀態。
下面的範例將會用
/resources/port/resource-id 和 /resources/port/current-rate 表示所有連接埠的狀態。


.. rst-class:: sourcecode

::

        csw = sess.get()
        for p in csw.resources.port:
            print p.resource_id, p.current_rate


GET-CONFIG
^^^^^^^^^^^^^^^^^^^^

下面的範例是使用 NETCONF GET-CONFIG 來取得目前的交換器設定值。


.. NOTE::

    running 用來表示現在儲存在 NETCONF 中目前的設定狀態。
    但這跟交換器的實作有關，或者你也可以儲存相關設定在 startup（ 設備啟動時 ）或 candidate（ Candidate set ）。

其結果會使用
/resources/port/resource-id 和
/resources/port/configuration/admin-state 表示所有連接埠的狀態。


.. rst-class:: sourcecode

::

        csw = sess.get_config('running')
        for p in csw.resources.port:
            print p.resource_id, p.configuration.admin_state


EDIT-CONFIG
^^^^^^^^^^^^^^^^^^^^^^

這個範例說明如何使用 NETCONF EDIT-CONFIG 來對設定進行變更。
首先使用 GET-CONFIG 取得交換器的設定，進行相關的編輯動作，最後使用 EDIT-CONFIG 將變更傳送至交換器。


.. NOTE::

    另外也可以使用 EDIT-CONFIG 直接修改部分的設定，這樣做將更為安全。


將全部的連接埠狀態在
/resources/port/configuration/admin-state 中設定為 down。


.. rst-class:: sourcecode

::

        csw = sess.get_config('running')
        for p in csw.resources.port:
            p.configuration.admin_state = 'down'
        sess.edit_config('running', csw)
