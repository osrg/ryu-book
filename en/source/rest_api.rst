.. _ch_rest_api:

REST Linkage
============

This section describes how to add a REST link function to the switching hub explained in " :ref:`ch_switching_hub`".


Integrating REST API
--------------------

Ryu has a Web server function corresponding to WSGI.
By using this function, it is possible to create a REST API, which is useful to link with other systems or browsers.

.. NOTE::

    WSGI means a unified framework for connecting Web applications and Web servers in Python.


Implementing a Switching Hub with REST API
------------------------------------------
Let's add the following two REST APIs to the switching hub explained in " :ref:`ch_switching_hub` ".

1. MAC address table acquisition API

    Returns the content of the MAC address table held by the switching hub.
    Returns a pair of MAC address and port number in JSON format.

2. MAC address table registration API

    Registers a pair of MAC address and port number in the MAC address table and adds a flow entry to the switch.


Let's take a look at the source code.

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_rest_13.py
    :lines: 16-

With simple_switch_rest_13.py, two classes are defined.

The first class is controller class ``SimpleSwitchController``, which defines the URL to receive the HTTP request and its corresponding method.

The second class is ``SimpleSwitchRest13``, which is extension of " :ref:`ch_switching_hub` ", to be able to update the MAC address table.

With ``SimpleSwitchRest13``, because flow entry is added to the switch, the FeaturesReply method is overridden and holds the datapath object.

Implementing SimpleSwitchRest13 Class
-------------------------------------

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_rest_13.py
    :pyobject: SimpleSwitchRest13
    :end-before: __init__
    :append: # ...

Class variable ``_CONTEXT`` is used to specify Ryu's WSGI-compatible Web server class. By doing so, WSGI's Web server instance can be acquired by a key called the ``wsgi`` key.

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_rest_13.py
    :dedent: 4
    :pyobject: SimpleSwitchRest13.__init__

Constructor acquires the instance of ``WSGIApplication`` in order to register the controller class, which is explained in a later section. For registration, the ``register`` method is used.
When executing the ``register`` method, the dictionary object is passed in the key name ``simple_switch_api_app`` so that the constructor of the controller can access the instance of the ``SimpleSwitchRest13`` class.

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_rest_13.py
    :dedent: 4
    :prepend: @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    :pyobject: SimpleSwitchRest13.switch_features_handler

Parent class ``switch_features_handler`` is overridden.
This method, upon rising of the SwitchFeatures event, acquires the ``datapath`` object stored in event object ``ev`` and stores it in instance variable ``switches``.
Also, at this time, an empty dictionary is set as the initial value in the MAC address table.

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_rest_13.py
    :dedent: 4
    :pyobject: SimpleSwitchRest13.set_mac_to_port

This method registers the MAC address and port to the specified switch.
The method is executed when REST API is called by the PUT method.

In argument ``entry``. a pair of the desired MAC address and connection port is stored.

While referencing the MAC address table ``self.mac_to_port`` information, the flow entry to be registered in the switch is searched.

For example, a pair of the following MAC address and connection port is registered in the MAC address table,

* 00:00:00:00:00:01, 1

and a pair of the MAC address and port passed by the argument ``entry`` is

* 00:00:00:00:00:02, 2

, so the flow entry necessary to register in the switch is as follows:

* Matching condition: in_port = 1, dst_mac = 00:00:00:00:00:02  Action: output=2
* Matching condition: in_port = 2, dst_mac = 00:00:00:00:00:01  Action: output=1

To register flow entry, the parent class ``add_flow`` method is used. At the end, the information passed by argument ``entry`` is stored in the MAC address table.


Implementing SimpleSwitchController Class
-----------------------------------------
Next, let's talk about the controller class that accepts HTTP requests to REST API.
The class name is ``SimpleSwitchController``.

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_rest_13.py
    :pyobject: SimpleSwitchController
    :end-before: @route
    :append: # ...

The instance of the ``SimpleSwitchRest13`` class is acquired by the contractor.

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_rest_13.py
    :dedent: 4
    :prepend: @route('simpleswitch', url, methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    :pyobject: SimpleSwitchController.list_mac_table

This part is to implement REST API's URL and its corresponding processing. To associate this method and URL, the ``route`` decorator defined in Ryu is used.

The content specified by the decorator is as follows:

* First argument

    Any name

* Second argument

    Specify URL.
    Make URL to be ``http://<server IP>:8080/simpleswitch/mactable/<data path ID>``.

* Third argument

    Specify the HTTP method.
    Specify the GET method.

* Fourth argument

    Specify the format of the specified location.
    The condition is that the {dpid} part of the URL(/simpleswitch/mactable/{dpid}) matches the expression of a 16-digit hex value defined by ``DPID_PATTERN`` of ryu/lib/dpid.py.

The REST API is called by the URL specified by the second argument. If the HTTP method at that time is GET, the ``list_mac_table`` method is called.
This method acquires the MAC address table corresponding to the data path ID specified in the {dpid} part, converts it to the JSON format and returns it to the caller.

If the data path ID of an unknown switch, which is not connected to Ryu, is specified, response code 404 is returned.

.. rst-class:: sourcecode

.. literalinclude:: ../../ryu/app/simple_switch_rest_13.py
    :dedent: 4
    :prepend: @route('simpleswitch', url, methods=['PUT'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    :pyobject: SimpleSwitchController.put_mac_table

Let's talk about REST API that registers MAC address table.

URL is the same as API when the MAC address table is acquired but when the HTTP method is PUT, the ``put_mac_table`` method is called.
With this method, the ``set_mac_to_port`` method of the switching hub instance is called inside.
When an exception is raised inside the ``put_mac_table`` method, response code 500 is returned.
Also, as with the ``list_mac_table`` method, if the data path ID of an unknown switch, which is not connected to Ryu, is specified, response code 404 is returned.

Executing REST API Added Switching Hub
--------------------------------------
Let's execute the switching hub to which REST API has been added.

First, as with " :ref:`ch_switching_hub` ", execute Mininet. Here again, don't forget to set OpenFlow13 for the OpenFlow version.
Then, start the switching hub added with REST API.

.. rst-class:: console

::

    ryu@ryu-vm:~/ryu/ryu/app$ sudo ovs-vsctl set Bridge s1 protocols=OpenFlow13
    ryu@ryu-vm:~/ryu/ryu/app$ ryu-manager --verbose ryu.app.simple_switch_rest_13
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

In the message at the time of start, there is a line stating "(31135) wsgi starting up on http://0.0.0.0:8080/" and this indicates that the Web server started at port number 8080.

Next, issue a ping from host 1 to host 2 on the mininet shell.

.. rst-class:: console

::

    mininet> h1 ping -c 1 h2
    PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
    64 bytes from 10.0.0.2: icmp_req=1 ttl=64 time=84.1 ms

    --- 10.0.0.2 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 84.171/84.171/84.171/0.000 ms


At this time, Packet-In to Ryu occurred three times.

.. rst-class:: console

::

    EVENT ofp_event->SimpleSwitchRest13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 ff:ff:ff:ff:ff:ff 1
    EVENT ofp_event->SimpleSwitchRest13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:02 00:00:00:00:00:01 2
    EVENT ofp_event->SimpleSwitchRest13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 00:00:00:00:00:02 1

Let's execute REST API that acquires the MAC table of the switching hub.
This time, use the curl command to call REST API.

.. rst-class:: console

::

    ryu@ryu-vm:~$ curl -X GET http://127.0.0.1:8080/simpleswitch/mactable/0000000000000001
    {"00:00:00:00:00:02": 2, "00:00:00:00:00:01": 1}

You can find that two hosts host 1 and host 2 have been learned on the MAC address table.

This time, store the two hosts, host 1 and host 2, in the MAC address table beforehand and execute ping. Temporarily stop the switching hub and Mininet once.
Then, start Mininet again, set the OpenFlow version to OpenFlow13 and then start the switching hub.

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

Next, call REST API for updating of the MAC address table for each host.
The data format when calling REST API shall be {"mac" : "MAC address", "port" : Connection port number}.

.. rst-class:: console

::

    ryu@ryu-vm:~$ curl -X PUT -d '{"mac" : "00:00:00:00:00:01", "port" : 1}' http://127.0.0.1:8080/simpleswitch/mactable/0000000000000001
    {"00:00:00:00:00:01": 1}
    ryu@ryu-vm:~$ curl -X PUT -d '{"mac" : "00:00:00:00:00:02", "port" : 2}' http://127.0.0.1:8080/simpleswitch/mactable/0000000000000001
    {"00:00:00:00:00:02": 2, "00:00:00:00:00:01": 1}

When those commands are executed, the flow entry corresponding to host 1 and host 2 are registered.

Now, let's execute a ping from host 1 to host 2.

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

At this time, the flow entry exists for the switches, Packet-In only occurs when an ARP request is sent from host 1 to host 2 and is not raised for subsequent packet exchange.

Conclusion
----------

This section used a function to reference or update the MAC address table as material to explain how to add REST API. As another practical application, it may be a good idea to create REST API that can add the desired flow entry to a switch and make it possible to operate from a browser.
