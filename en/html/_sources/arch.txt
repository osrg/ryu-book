.. _ch_arch:

Architecture
============

This section introduces the Ryu architecture. 
Refer to the API reference <http://ryu.readthedocs.org/en/latest/> for how to use each class.

Application Programming Model
-----------------------------

The following section explains the programming model used for Ryu applications.

.. only:: latex

    .. image:: images/arch/fig1.eps

.. only:: not latex

    .. image:: images/arch/fig1.png

Applications
^^^^^^^^^^^^

Applications are a class that inherits ``ryu.base.app_manager.RyuApp``. User logic is described as an application.


Event
^^^^^

Events are class objects that inherit ``ryu.controller.event.EventBase``. Communication between applications is performed by transmitting and receiving events.

Event Queue
^^^^^^^^^^^

Each application has a single queue for receiving events.

Threads
^^^^^^^

Ryu runs in multi-thread using eventlets. Because threads are non-preemptive, you need to be careful when performing time-consuming processes.

Event loops
"""""""""""

One thread is automatically created for each application. This thread runs an event loop. If there is an event in the event queue, the event loop will load the event and call the corresponding event handler (described later).

Additional threads
""""""""""""""""""

You can create additional threads using the hub.spawn function to perform application-specific processing.

eventlets
"""""""""

It can also be used directly from the application function of eventlet, but it's not recommended. Please be sure to use the wrapper provided by the hub module if possible.

Event handlers
^^^^^^^^^^^^^^

You can define an event handler by decorating application class method with an ``ryu.controller.handler.set_ev_cls`` decorator. When an event of the specified type occurs, the event handler is called from the application's event loop.

..  XXX CONTEXTS
..  XXX Event type
..  XXX openflow message
..  XXX To which chapter should the descriptions of ryu-manager, etc. be put?
