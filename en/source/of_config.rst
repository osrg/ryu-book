.. _ch_of_config:

OF-Config Library
=================

This section describes Client library of OF-Config that comes with Ryu.

OF-Config Protocol
------------------

OF-Config is a protocol for the management of the OpenFlow switch.
It has been defined as the NETCONF (RFC 6241) schema and can perform status acquisition and settings of logical switch, port, and queue.

It's formulated by ONF the same as OpenFlow and specifications can be obtained from the following website.

https://www.opennetworking.org/sdn-resources/onf-specifications/openflow-config

This library is in compliance with OF-Config 1.1.1.

.. NOTE::
    Currently Open vSwitch does not support OF-Config, but it does offer a service called OVSDB for the same purpose. OF-Config is a relatively new standard and did not yet exist when Open vSwitch implemented OVSDB.

    The OVSDB protocol specification is published as 7047 RFC, but for all practical purposes it is become a protocol only for Open vSwitch. OF-Config only recently appeared but it is expected to be implemented a lot in future OpenFlow switches.

Library Configuration
---------------------

ryu.lib.of_config.capable_switch.OFCapableSwitch Class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A class to handle NETCONF sessions.

.. rst-class:: sourcecode

::

        from ryu.lib.of_config.capable_switch import OFCapableSwitch

ryu.lib.of_config.classes Module
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A module to provide a set of classes to treat setting contents as python objects.

.. NOTE::
    The class name is basically the same as the names used by the grouping keyword in the yang specification of OF-Config 1.1.1.
    Example: OFPortType

.. rst-class:: sourcecode

::

        import ryu.lib.of_config.classes as ofc

Usage Example
-------------

Connection to the Switch
^^^^^^^^^^^^^^^^^^^^^^^^

Connect to the switch using SSH transport. 
For unknown_host_cb, specify a callback function that performs processing of an unknown SSH host key, but right now it is set to continue the connection unconditionally.

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

The following is an example to obtain the state using NETCONF GET.
It displays /resources/port/resource-id and /resources/port/current-rate of all ports.

.. rst-class:: sourcecode

::

        csw = sess.get()
        for p in csw.resources.port:
            print p.resource_id, p.current_rate

GET-CONFIG
^^^^^^^^^^

The following is an example to obtain settings using NETCONF GET-CONFIG.

.. NOTE::
    running is a currently running setting at data store of NETCONF. It depends on the implementation, but you can also use a data store such as startup (settings that are loaded when you start the device) and candidate (candidate set).

It displays the /resources/port/resource-id and /resources/port/configuration/admin-state of all ports.

.. rst-class:: sourcecode

::

        csw = sess.get_config('running')
        for p in csw.resources.port:
            print p.resource_id, p.configuration.admin_state

EDIT-CONFIG
^^^^^^^^^^^

The following is an example of how you can change settings using NETCONF EDIT-CONFIG.
The basic procedure is to obtain settings using GET-CONFIG, edit them and send them back using EDIT-CONFIG.

.. NOTE::
    You can also partially edit settings in EDIT-CONFIG on the protocol, but this usage is safer.

Set /resources/port/configuration/admin-state of all ports to down.

.. rst-class:: sourcecode

::

        csw = sess.get_config('running')
        for p in csw.resources.port:
            p.configuration.admin_state = 'down'
        sess.edit_config('running', csw)
