組織架構
==============

本章介紹 Ryu 的架構。
關於每一個 Class 請參照 `API 參考資料 <http://ryu.readthedocs.org/en/latest/>`_ 來得到更細節的資料。

應用程式開發模型（ Application programming model ）
------------------------------------------------------------------------

以下是 Ryu 應用程式的開發模型


.. only:: latex

    .. image:: images/arch/fig1.eps

.. only:: not latex

    .. image:: images/arch/fig1.png


應用程式（ Application ）
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

應用程式是繼承 ``ryu.base.app_manager.RyuApp`` 而來。User logic 被視作是一個應用程式。

事件（ Event ）
^^^^^^^^^^^^^^^^^^^^

事件是繼承 ``ryu.controller.event.EventBase`` 而來，並藉由 Transmitting 和 receiving event 來相互溝通訊息。

事件佇列（ Event queue ）
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

每個應用程式都有一個自己的佇列用來接受事件訊息。

執行緒（ Thread ）
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ryu 採用 eventlet 來實現多執行緒。因為執行緒是不可插斷的（ non-preemptive ），因此在使用上要特別注意長時間運行所帶來的風險。

事件迴圈（ Event loop ）
""""""""""""""""""""""""""""
當應用程式執行時，將會有一個執行緒自動被產生用來執行該應用程式。
該執行緒將會做為事件迴圈的模式來執行。如果在事件佇列中發現有事件存在，該事件迴圈將會讀取該事件並且呼叫相對應的事件處理器來處理它。

額外的執行緒（ Additional thread ）
""""""""""""""""""""""""""""""""""""""""""""""""""""""""

如果需要的話，你可以使用 hub.spawn 產生額外的執行緒用來執行特殊的應用程式功能。

eventlet
""""""""""""""""

雖然你可以直接使用 eventlet 所提供的所有功能，但不建議你這麼做。
請使用 hub module 所包裝過的功能取代直接使用 eventlet。

事件處理器（ Event handler ）
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

藉由使用 ``ryu.controller.handler.set_ev_cls`` 裝飾器類別來定義自己的事件管理器。當定義的事件發生時，應用程式中的事件迴圈將會偵測到並呼叫對應的事件管理器。

..  XXX CONTEXTS
..  XXX Event type
..  XXX openflow message
..  XXX ryu-manager explain
