.. _ch_rest_router:

Router
======

This section describes how to use a router that can be set using REST.


Example of the Operation of a Single Tenant
-------------------------------------------

The following shows an example of creating topology such as the following and adding or deleting a route or address for each switch (router) and verifying communication availability between each host.

.. only:: latex

  .. image:: images/rest_router/fig1.eps
     :scale: 80%
     :align: center

.. only:: epub

  .. image:: images/rest_router/fig1.png
     :align: center

.. only:: not latex and not epub

  .. image:: images/rest_router/fig1.png
     :scale: 40%
     :align: center


Building the environment
^^^^^^^^^^^^^^^^^^^^^^^^

First, build an environment on Mininet. Parameters of the ``mn`` command are as follows.

============ ========== ===========================================
Parameter    Value      Explanation
============ ========== ===========================================
topo         linear,3   Topology where three switches are connected serially
mac          None       Set the MAC address of the host automatically
switch       ovsk       Use Open vSwitch
controller   remote     Use an external one for OpenFlow controller
x            None       Start xterm
============ ========== ===========================================

An execution example is as follows.

.. rst-class:: console

::

    $ sudo mn --topo linear,3 --mac --switch ovsk --controller remote -x
    *** Creating network
    *** Adding controller
    Unable to contact the remote controller at 127.0.0.1:6633
    *** Adding hosts:
    h1 h2 h3
    *** Adding switches:
    s1 s2 s3
    *** Adding links:
    (h1, s1) (h2, s2) (h3, s3) (s1, s2) (s2, s3)
    *** Configuring hosts
    h1 h2 h3
    *** Running terms on localhost:10.0
    *** Starting controller
    *** Starting 3 switches
    s1 s2 s3

    *** Starting CLI:
    mininet>

Also, start another xterm for the controller.

.. rst-class:: console

::

    mininet> xterm c0
    mininet>

Next, set the version of OpenFlow to be used in each router to 1.3.

switch: s1 (root):

.. rst-class:: console

::

    # ovs-vsctl set Bridge s1 protocols=OpenFlow13

switch: s2 (root):

.. rst-class:: console

::

    # ovs-vsctl set Bridge s2 protocols=OpenFlow13

switch: s3 (root):

.. rst-class:: console

::

    # ovs-vsctl set Bridge s3 protocols=OpenFlow13

Then, delete the IP address that is assigned automatically on each host and set a new IP address.

host: h1:

.. rst-class:: console

::

    # ip addr del 10.0.0.1/8 dev h1-eth0
    # ip addr add 172.16.20.10/24 dev h1-eth0

host: h2:

.. rst-class:: console

::

    # ip addr del 10.0.0.2/8 dev h2-eth0
    # ip addr add 172.16.10.10/24 dev h2-eth0

host: h3:

.. rst-class:: console

::

    # ip addr del 10.0.0.3/8 dev h3-eth0
    # ip addr add 192.168.30.10/24 dev h3-eth0

Finally, start rest_router on xterm of controller.

controller: c0 (root):

.. rst-class:: console

::

    # ryu-manager ryu.app.rest_router
    loading app ryu.app.rest_router
    loading app ryu.controller.ofp_handler
    instantiating app None of DPSet
    creating context dpset
    creating context wsgi
    instantiating app ryu.app.rest_router of RestRouterAPI
    instantiating app ryu.controller.ofp_handler of OFPHandler
    (2212) wsgi starting up on http://0.0.0.0:8080/

After a successful connection between the router and Ryu, the following message appears.

controller: c0 (root):

.. rst-class:: console

::

    [RT][INFO] switch_id=0000000000000003: Set SW config for TTL error packet in.
    [RT][INFO] switch_id=0000000000000003: Set ARP handling (packet in) flow [cookie=0x0]
    [RT][INFO] switch_id=0000000000000003: Set L2 switching (normal) flow [cookie=0x0]
    [RT][INFO] switch_id=0000000000000003: Set default route (drop) flow [cookie=0x0]
    [RT][INFO] switch_id=0000000000000003: Start cyclic routing table update.
    [RT][INFO] switch_id=0000000000000003: Join as router.
    ...

If the above log is displayed for the three routers, preparation is complete.


Setting the Address
^^^^^^^^^^^^^^^^^^^

Set the address for each router.

First, set the addresses "172.16.20.1/24" and "172.16.30.30/24" for router s1.

.. NOTE::

    For details of REST API used in the following description, see "`REST API List`_" at the end of the section.

Node: c0 (root):

.. rst-class:: console

::

    # curl -X POST -d '{"address":"172.16.20.1/24"}' http://localhost:8080/router/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    # curl -X POST -d '{"address": "172.16.30.30/24"}' http://localhost:8080/router/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]

.. NOTE::

    The result of the REST command is formatted for easy viewing.

Next, set the addresses "172.16.10.1/24", "172.16.30.1/24" and "192.168.10.1/24" for router s2.

Node: c0 (root):

.. rst-class:: console

::

    # curl -X POST -d '{"address":"172.16.10.1/24"}' http://localhost:8080/router/0000000000000002
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    # curl -X POST -d '{"address": "172.16.30.1/24"}' http://localhost:8080/router/0000000000000002
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]

    # curl -X POST -d '{"address": "192.168.10.1/24"}' http://localhost:8080/router/0000000000000002
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "details": "Add address [address_id=3]"
            }
          ]
        }
      ]

Then, set the addresses "192.168.30.1/24" and "192.168.10.20/24" for router s3.

Node: c0 (root):

.. rst-class:: console

::

    # curl -X POST -d '{"address": "192.168.30.1/24"}' http://localhost:8080/router/0000000000000003
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    # curl -X POST -d '{"address": "192.168.10.20/24"}' http://localhost:8080/router/0000000000000003
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]


IP addresses to the router have been set. Register as the default gateway on each host.

host: h1:

.. rst-class:: console

::

    # ip route add default via 172.16.20.1

host: h2:

.. rst-class:: console

::

    # ip route add default via 172.16.10.1

host: h3:

.. rst-class:: console

::

    # ip route add default via 192.168.30.1


Configuring the Default Route
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set the default route for each router.

First, set router s2 as the default route of router s1.

Node: c0 (root):

.. rst-class:: console

::

    # curl -X POST -d '{"gateway": "172.16.30.1"}' http://localhost:8080/router/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]

Set router s1 as the default route of router s2.

Node: c0 (root):

.. rst-class:: console

::

    # curl -X POST -d '{"gateway": "172.16.30.30"}' http://localhost:8080/router/0000000000000002
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]

Set router s2 as the default route of router s3.

Node: c0 (root):

.. rst-class:: console

::

    # curl -X POST -d '{"gateway": "192.168.10.1"}' http://localhost:8080/router/0000000000000003
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]



Setting Static Routes
^^^^^^^^^^^^^^^^^^^^^

For s2 router, set a static route to the host (192.168.30.0/24) under router s3.

Node: c0 (root):

.. rst-class:: console

::

    # curl -X POST -d '{"destination": "192.168.30.0/24", "gateway": "192.168.10.20"}' http://localhost:8080/router/0000000000000002
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "details": "Add route [route_id=2]"
            }
          ]
        }
      ]


The setting status of the route and address are as follows.

.. only:: latex

  .. image:: images/rest_router/fig4.eps
     :scale: 80%
     :align: center

.. only:: epub

  .. image:: images/rest_router/fig4.png
     :align: center

.. only:: not latex and not epub

  .. image:: images/rest_router/fig4.png
     :scale: 40%
     :align: center


Verifying the Setting
^^^^^^^^^^^^^^^^^^^^^

Check the contents of the setting of each router.

Node: c0 (root):

.. rst-class:: console

::

    # curl http://localhost:8080/router/0000000000000001
      [
        {
          "internal_network": [
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "172.16.30.1"
                }
              ],
              "address": [
                {
                  "address_id": 1,
                  "address": "172.16.20.1/24"
                },
                {
                  "address_id": 2,
                  "address": "172.16.30.30/24"
                }
              ]
            }
          ],
          "switch_id": "0000000000000001"
        }
      ]

    # curl http://localhost:8080/router/0000000000000002
      [
        {
          "internal_network": [
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "172.16.30.30"
                },
                {
                  "route_id": 2,
                  "destination": "192.168.30.0/24",
                  "gateway": "192.168.10.20"
                }
              ],
              "address": [
                {
                  "address_id": 2,
                  "address": "172.16.30.1/24"
                },
                {
                  "address_id": 3,
                  "address": "192.168.10.1/24"
                },
                {
                  "address_id": 1,
                  "address": "172.16.10.1/24"
                }
              ]
            }
          ],
          "switch_id": "0000000000000002"
        }
      ]

    # curl http://localhost:8080/router/0000000000000003
      [
        {
          "internal_network": [
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "192.168.10.1"
                }
              ],
              "address": [
                {
                  "address_id": 1,
                  "address": "192.168.30.1/24"
                },
                {
                  "address_id": 2,
                  "address": "192.168.10.20/24"
                }
              ]
            }
          ],
          "switch_id": "0000000000000003"
        }
      ]

Check communication using ping in this state. First, run a ping from h3 to h2. You can verify that it can communicate successfully.

host: h2:

.. rst-class:: console

::

    # ping 192.168.30.10
    PING 192.168.30.10 (192.168.30.10) 56(84) bytes of data.
    64 bytes from 192.168.30.10: icmp_req=1 ttl=62 time=48.8 ms
    64 bytes from 192.168.30.10: icmp_req=2 ttl=62 time=0.402 ms
    64 bytes from 192.168.30.10: icmp_req=3 ttl=62 time=0.089 ms
    64 bytes from 192.168.30.10: icmp_req=4 ttl=62 time=0.065 ms
    ...

Next, run a ping from h2 to h1. You can also verify that it can communicate successfully.

host: h2:

.. rst-class:: console

::

    # ping 172.16.20.10
    PING 172.16.20.10 (172.16.20.10) 56(84) bytes of data.
    64 bytes from 172.16.20.10: icmp_req=1 ttl=62 time=43.2 ms
    64 bytes from 172.16.20.10: icmp_req=2 ttl=62 time=0.306 ms
    64 bytes from 172.16.20.10: icmp_req=3 ttl=62 time=0.057 ms
    64 bytes from 172.16.20.10: icmp_req=4 ttl=62 time=0.048 ms
    ...


Deleting the Static Route
^^^^^^^^^^^^^^^^^^^^^^^^^

Delete the static route to router s3 set in router s2.

Node: c0 (root):

.. rst-class:: console

::

    # curl -X DELETE -d '{"route_id": "2"}' http://localhost:8080/router/0000000000000002
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "details": "Delete route [route_id=2]"
            }
          ]
        }
      ]

Check the information that has been configured on router s2. You can see that the static route to router s3 has been deleted.

Node: c0 (root):

.. rst-class:: console

::

    # curl http://localhost:8080/router/0000000000000002
      [
        {
          "internal_network": [
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "172.16.30.30"
                }
              ],
              "address": [
                {
                  "address_id": 2,
                  "address": "172.16.30.1/24"
                },
                {
                  "address_id": 3,
                  "address": "192.168.10.1/24"
                },
                {
                  "address_id": 1,
                  "address": "172.16.10.1/24"
                }
              ]
            }
          ],
          "switch_id": "0000000000000002"
        }
      ]


Check communication using ping. Since the root information from h3 to h2 was deleted, you will find that it cannot communicate.

host: h2:

.. rst-class:: console

::

    # ping 192.168.30.10
    PING 192.168.30.10 (192.168.30.10) 56(84) bytes of data.
    ^C
    --- 192.168.30.10 ping statistics ---
    12 packets transmitted, 0 received, 100% packet loss, time 11088ms


Deleting an Address
^^^^^^^^^^^^^^^^^^^

Delete the address "172.16.20.1/24", which is set in router s1.

Node: c0 (root):

.. rst-class:: console

::

    # curl -X DELETE -d '{"address_id": "1"}' http://localhost:8080/router/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Delete address [address_id=1]"
            }
          ]
        }
      ]

Check the information that has been configured on router s1. You can see that of the IP addresses configured on router s1, "172.16.20.1/24" has been deleted.

Node: c0 (root):

.. rst-class:: console

::

    # curl http://localhost:8080/router/0000000000000001
      [
        {
          "internal_network": [
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "172.16.30.1"
                }
              ],
              "address": [
                {
                  "address_id": 2,
                  "address": "172.16.30.30/24"
                }
              ]
            }
          ],
          "switch_id": "0000000000000001"
        }
      ]


Check communication using ping. Since the information about the subnet to which h1 belongs has been removed from router s1, you can tell that communication from h2 to h1 is not possible.

host: h2:

.. rst-class:: console

::

    # ping 172.16.20.10
    PING 172.16.20.10 (172.16.20.10) 56(84) bytes of data.
    ^C
    --- 172.16.20.10 ping statistics ---
    19 packets transmitted, 0 received, 100% packet loss, time 18004ms


Example of the Operation of a Multi-tenant
------------------------------------------

The following shows an example of creating a topology where tenants are divided by VLAN such as the following and routes or addresses for each switch (router) are added or deleted and communication availability between each host is verified.

.. only:: latex

  .. image:: images/rest_router/fig5.eps
     :scale: 80%
     :align: center

.. only:: epub

  .. image:: images/rest_router/fig5.png
     :align: center

.. only:: not latex and not epub

  .. image:: images/rest_router/fig5.png
     :scale: 40%
     :align: center

Environment building
^^^^^^^^^^^^^^^^^^^^

First, build an environment on Mininet. Parameters of the ``mn`` command are as follows.

============ ============ ===========================================
Parameter    Value        Example
============ ============ ===========================================
topo         linear,3,2   Topology where three switches are connected serially 

                          (Two hosts are connected to each switch)
mac          None         Set the MAC address of the host automatically
switch       ovsk         Use Open vSwitch
controller   remote       Use an external one for OpenFlow controller
x            None         Start the xterm
============ ============ ===========================================

A execution example is as follows.

.. rst-class:: console

::

    $ sudo mn --topo linear,3,2 --mac --switch ovsk --controller remote -x
    *** Creating network
    *** Adding controller
    Unable to contact the remote controller at 127.0.0.1:6633
    *** Adding hosts:
    h1s1 h1s2 h1s3 h2s1 h2s2 h2s3
    *** Adding switches:
    s1 s2 s3
    *** Adding links:
    (h1s1, s1) (h1s2, s2) (h1s3, s3) (h2s1, s1) (h2s2, s2) (h2s3, s3) (s1, s2) (s2, s3)
    *** Configuring hosts
    h1s1 h1s2 h1s3 h2s1 h2s2 h2s3
    *** Running terms on localhost:10.0
    *** Starting controller
    *** Starting 3 switches
    s1 s2 s3
    *** Starting CLI:
    mininet>

Also, start another xterm for the controller.

.. rst-class:: console

::

    mininet> xterm c0
    mininet>

Next, set the version of OpenFlow to be used in each router to 1.3.

switch: s1 (root):

.. rst-class:: console

::

    # ovs-vsctl set Bridge s1 protocols=OpenFlow13

switch: s2 (root):

.. rst-class:: console

::

    # ovs-vsctl set Bridge s2 protocols=OpenFlow13

switch: s3 (root):

.. rst-class:: console

::

    # ovs-vsctl set Bridge s3 protocols=OpenFlow13

Then, set the VLAN ID to the interface of each host and set the new IP address.

host: h1s1:

.. rst-class:: console

::

    # ip addr del 10.0.0.1/8 dev h1s1-eth0
    # ip link add link h1s1-eth0 name h1s1-eth0.2 type vlan id 2
    # ip addr add 172.16.10.10/24 dev h1s1-eth0.2
    # ip link set dev h1s1-eth0.2 up

host: h2s1:

.. rst-class:: console

::

    # ip addr del 10.0.0.4/8 dev h2s1-eth0
    # ip link add link h2s1-eth0 name h2s1-eth0.110 type vlan id 110
    # ip addr add 172.16.10.11/24 dev h2s1-eth0.110
    # ip link set dev h2s1-eth0.110 up

host: h1s2:

.. rst-class:: console

::

    # ip addr del 10.0.0.2/8 dev h1s2-eth0
    # ip link add link h1s2-eth0 name h1s2-eth0.2 type vlan id 2
    # ip addr add 192.168.30.10/24 dev h1s2-eth0.2
    # ip link set dev h1s2-eth0.2 up

host: h2s2:

.. rst-class:: console

::

    # ip addr del 10.0.0.5/8 dev h2s2-eth0
    # ip link add link h2s2-eth0 name h2s2-eth0.110 type vlan id 110
    # ip addr add 192.168.30.11/24 dev h2s2-eth0.110
    # ip link set dev h2s2-eth0.110 up

host: h1s3:

.. rst-class:: console

::

    # ip addr del 10.0.0.3/8 dev h1s3-eth0
    # ip link add link h1s3-eth0 name h1s3-eth0.2 type vlan id 2
    # ip addr add 172.16.20.10/24 dev h1s3-eth0.2
    # ip link set dev h1s3-eth0.2 up

host: h2s3:

.. rst-class:: console

::

    # ip addr del 10.0.0.6/8 dev h2s3-eth0
    # ip link add link h2s3-eth0 name h2s3-eth0.110 type vlan id 110
    # ip addr add 172.16.20.11/24 dev h2s3-eth0.110
    # ip link set dev h2s3-eth0.110 up

Finally, start rest_router on xterm of controller.

controller: c0 (root):

.. rst-class:: console

::

    # ryu-manager ryu.app.rest_router
    loading app ryu.app.rest_router
    loading app ryu.controller.ofp_handler
    instantiating app None of DPSet
    creating context dpset
    creating context wsgi
    instantiating app ryu.app.rest_router of RestRouterAPI
    instantiating app ryu.controller.ofp_handler of OFPHandler
    (2447) wsgi starting up on http://0.0.0.0:8080/

After a successful connection between the router and Ryu, the following message appears.

controller: c0 (root):

.. rst-class:: console

::

    [RT][INFO] switch_id=0000000000000003: Set SW config for TTL error packet in.
    [RT][INFO] switch_id=0000000000000003: Set ARP handling (packet in) flow [cookie=0x0]
    [RT][INFO] switch_id=0000000000000003: Set L2 switching (normal) flow [cookie=0x0]
    [RT][INFO] switch_id=0000000000000003: Set default route (drop) flow [cookie=0x0]
    [RT][INFO] switch_id=0000000000000003: Start cyclic routing table update.
    [RT][INFO] switch_id=0000000000000003: Join as router.
    ...

If the above log is displayed for the three routers, preparation is complete.


Setting an Address
^^^^^^^^^^^^^^^^^^

Set the address for each router.

First, set the addresses "172.16.10.1/24" and "10.10.10.1/24" to router s1. They must be set to each VLAN ID respectively.

Node: c0 (root):

.. rst-class:: console

::

    # curl -X POST -d '{"address": "172.16.10.1/24"}' http://localhost:8080/router/0000000000000001/2
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    # curl -X POST -d '{"address": "10.10.10.1/24"}' http://localhost:8080/router/0000000000000001/2
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]

    # curl -X POST -d '{"address": "172.16.10.1/24"}' http://localhost:8080/router/0000000000000001/110
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    # curl -X POST -d '{"address": "10.10.10.1/24"}' http://localhost:8080/router/0000000000000001/110
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]

Next, set the addresses "192.168.30.1/24" and "10.10.10.2/24" to router s2.

Node: c0 (root):

.. rst-class:: console

::

    # curl -X POST -d '{"address": "192.168.30.1/24"}' http://localhost:8080/router/0000000000000002/2
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    # curl -X POST -d '{"address": "10.10.10.2/24"}' http://localhost:8080/router/0000000000000002/2
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]

    # curl -X POST -d '{"address": "192.168.30.1/24"}' http://localhost:8080/router/0000000000000002/110
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    # curl -X POST -d '{"address": "10.10.10.2/24"}' http://localhost:8080/router/0000000000000002/110
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]

Then, set the addresses "172.16.20.1/24" and "10.10.10.3/24" to router s3.

Node: c0 (root):

.. rst-class:: console

::

    # curl -X POST -d '{"address": "172.16.20.1/24"}' http://localhost:8080/router/0000000000000003/2
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    # curl -X POST -d '{"address": "10.10.10.3/24"}' http://localhost:8080/router/0000000000000003/2
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]

    # curl -X POST -d '{"address": "172.16.20.1/24"}' http://localhost:8080/router/0000000000000003/110
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add address [address_id=1]"
            }
          ]
        }
      ]

    # curl -X POST -d '{"address": "10.10.10.3/24"}' http://localhost:8080/router/0000000000000003/110
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add address [address_id=2]"
            }
          ]
        }
      ]

IP addresses to the routers have been set. Register as the default gateway on each host.

host: h1s1:

.. rst-class:: console

::

    # ip route add default via 172.16.10.1

host: h2s1:

.. rst-class:: console

::

    # ip route add default via 172.16.10.1

host: h1s2:

.. rst-class:: console

::

    # ip route add default via 192.168.30.1

host: h2s2:

.. rst-class:: console

::

    # ip route add default via 192.168.30.1

host: h1s3:

.. rst-class:: console

::

    # ip route add default via 172.16.20.1

host: h2s3:

.. rst-class:: console

::

    # ip route add default via 172.16.20.1

The addresses that have been set are as follows.

.. only:: latex

  .. image:: images/rest_router/fig7.eps
     :scale: 80%
     :align: center

.. only:: epub

  .. image:: images/rest_router/fig7.png
     :align: center

.. only:: not latex and not epub

  .. image:: images/rest_router/fig7.png
     :scale: 40%
     :align: center


Setting Static Routes and the Default Route
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set static routes and the default route for each router.


First, set router s2 as the default route of router s1.

Node: c0 (root):

.. rst-class:: console

::

    # curl -X POST -d '{"gateway": "10.10.10.2"}' http://localhost:8080/router/0000000000000001/2
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]

    # curl -X POST -d '{"gateway": "10.10.10.2"}' http://localhost:8080/router/0000000000000001/110
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]

Set router s1 as the default route of router s2.

Node: c0 (root):

.. rst-class:: console

::

    # curl -X POST -d '{"gateway": "10.10.10.1"}' http://localhost:8080/router/0000000000000002/2
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]

    # curl -X POST -d '{"gateway": "10.10.10.1"}' http://localhost:8080/router/0000000000000002/110
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]

Set router s2 as default route of router s3.

Node: c0 (root):

.. rst-class:: console

::

    # curl -X POST -d '{"gateway": "10.10.10.2"}' http://localhost:8080/router/0000000000000003/2
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]

    # curl -X POST -d '{"gateway": "10.10.10.2"}' http://localhost:8080/router/0000000000000003/110
      [
        {
          "switch_id": "0000000000000003",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 110,
              "details": "Add route [route_id=1]"
            }
          ]
        }
      ]


Next, for s2 router, set a static route to the host (172.16.20.0/24) under router s3. Only set if vlan_id=2.

Node: c0 (root):

.. rst-class:: console

::

    # curl -X POST -d '{"destination": "172.16.20.0/24", "gateway": "10.10.10.3"}' http://localhost:8080/router/0000000000000002/2
      [
        {
          "switch_id": "0000000000000002",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Add route [route_id=2]"
            }
          ]
        }
      ]


Verifying the Settings
^^^^^^^^^^^^^^^^^^^^^^

Check the contents of the settings for each router.

Node: c0 (root):

.. rst-class:: console

::

    # curl http://localhost:8080/router/all/all
      [
        {
          "internal_network": [
            {},
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "10.10.10.2"
                }
              ],
              "vlan_id": 2,
              "address": [
                {
                  "address_id": 2,
                  "address": "10.10.10.1/24"
                },
                {
                  "address_id": 1,
                  "address": "172.16.10.1/24"
                }
              ]
            },
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "10.10.10.2"
                }
              ],
              "vlan_id": 110,
              "address": [
                {
                  "address_id": 2,
                  "address": "10.10.10.1/24"
                },
                {
                  "address_id": 1,
                  "address": "172.16.10.1/24"
                }
              ]
            }
          ],
          "switch_id": "0000000000000001"
        },
        {
          "internal_network": [
            {},
            {
              "route": [
                {
                  "route_id": 2,
                  "destination": "172.16.20.0/24",
                  "gateway": "10.10.10.3"
                },
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "10.10.10.1"
                }
              ],
              "vlan_id": 2,
              "address": [
                {
                  "address_id": 2,
                  "address": "10.10.10.2/24"
                },
                {
                  "address_id": 1,
                  "address": "192.168.30.1/24"
                }
              ]
            },
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "10.10.10.1"
                }
              ],
              "vlan_id": 110,
              "address": [
                {
                  "address_id": 2,
                  "address": "10.10.10.2/24"
                },
                {
                  "address_id": 1,
                  "address": "192.168.30.1/24"
                }
              ]
            }
          ],
          "switch_id": "0000000000000002"
        },
        {
          "internal_network": [
            {},
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "10.10.10.2"
                }
              ],
              "vlan_id": 2,
              "address": [
                {
                  "address_id": 1,
                  "address": "172.16.20.1/24"
                },
                {
                  "address_id": 2,
                  "address": "10.10.10.3/24"
                }
              ]
            },
            {
              "route": [
                {
                  "route_id": 1,
                  "destination": "0.0.0.0/0",
                  "gateway": "10.10.10.2"
                }
              ],
              "vlan_id": 110,
              "address": [
                {
                  "address_id": 1,
                  "address": "172.16.20.1/24"
                },
                {
                  "address_id": 2,
                  "address": "10.10.10.3/24"
                }
              ]
            }
          ],
          "switch_id": "0000000000000003"
        }
      ]

A table of settings for each router is as follows.

.. csv-table::
    :header: "Router", "VLAN ID", "IP address", "Default route", "Static route"

    "s1", 2, "172.16.10.1/24, 10.10.10.1/24", "10.10.10.2(s2)"
    "s1", 110, "172.16.10.1/24, 10.10.10.1/24", "10.10.10.2(s2)"
    "s2", 2, "192.168.30.1/24, 10.10.10.2/24", "10.10.10.1(s1)", " Destination: 172.16.20.0/24, Gateway:10.10.10.3(s3)"
    "s2", 110, "192.168.30.1/24, 10.10.10.2/24", "10.10.10.1(s1)"
    "s3", 2, "172.16.20.1/24, 10.10.10.3/24", "10.10.10.2(s2)"
    "s3", 110, "172.16.20.1/24, 10.10.10.3/24", "10.10.10.2(s2)"


Send a ping from h1s1 to h1s3. Since they're the same host of vlan_id=2 and router 2 has a static route set to s3, it can communicate successfully.

host: h1s1:

.. rst-class:: console

::

    # ping 172.16.20.10
    PING 172.16.20.10 (172.16.20.10) 56(84) bytes of data.
    64 bytes from 172.16.20.10: icmp_req=1 ttl=61 time=45.9 ms
    64 bytes from 172.16.20.10: icmp_req=2 ttl=61 time=0.257 ms
    64 bytes from 172.16.20.10: icmp_req=3 ttl=61 time=0.059 ms
    64 bytes from 172.16.20.10: icmp_req=4 ttl=61 time=0.182 ms

Send a ping from h2s1 to h2s3. They're the same host of vlan_id=2 but since router s2 doesn't have a static route set to s3, it cannot communicate successfully.

host: h2s1:

.. rst-class:: console

::

    # ping 172.16.20.11
    PING 172.16.20.11 (172.16.20.11) 56(84) bytes of data.
    ^C
    --- 172.16.20.11 ping statistics ---
    8 packets transmitted, 0 received, 100% packet loss, time 7009ms

.. only:: latex

  .. image:: images/rest_router/fig8.eps
     :scale: 80%
     :align: center

.. only:: epub

  .. image:: images/rest_router/fig8.png
     :align: center

.. only:: not latex and not epub

  .. image:: images/rest_router/fig8.png
     :scale: 40%
     :align: center

In this section, you learned how to use routers with specific examples. 


REST API List
-------------

A list of REST API of rest_router introduced in this section.


Acquiring the Setting
^^^^^^^^^^^^^^^^^^^^^

=============  ========================================
**Method**     GET
**URL**        /router/{**switch**}[/{**vlan**}]

               --**switch**: [ "all" \| *Switch ID* ]

               --**vlan**: [ "all" \| *VLAN ID* ]
**Remarks**    Specification of VLAN ID is optional.
=============  ========================================


Setting an Address
^^^^^^^^^^^^^^^^^^

=============  ================================================
**Method**     POST
**URL**        /router/{**switch**}[/{**vlan**}]

               --**switch**: [ "all" \| *Switch ID* ]

               --**vlan**: [ "all" \| *VLAN ID* ]
**Data**       **address**:"<xxx.xxx.xxx.xxx/xx>"

**Remarks**    Perform address setting before performing route setting.

               Specification of VLAN ID is optional.
=============  ================================================


Setting Static Routes
^^^^^^^^^^^^^^^^^^^^^

=============  ================================================
**Method**     POST
**URL**        /router/{**switch**}[/{**vlan**}]

               --**switch**: [ "all" \| *Switch ID* ]

               --**vlan**: [ "all" \| *VLAN ID* ]
**Data**       **destination**:"<xxx.xxx.xxx.xxx/xx>"

               **gateway**:"<xxx.xxx.xxx.xxx>"
**Remarks**    Specification of VLAN ID is optional.
=============  ================================================


Setting Default Route
^^^^^^^^^^^^^^^^^^^^^^

=============  ================================================
**Method**     POST
**URL**        /router/{**switch**}[/{**vlan**}]

               --**switch**: [ "all" \| *Switch ID* ]

               --**vlan**: [ "all" \| *VLAN ID* ]
**Data**       **gateway**:"<xxx.xxx.xxx.xxx>"
**Remarks**    Specification of VLAN ID is optional.
=============  ================================================


Deleting an Address
^^^^^^^^^^^^^^^^^^^

=============  ==========================================
**Method**     DELETE
**URL**        /router/{**switch**}[/{**vlan**}]

               --**switch**: [ "all" \| *Switch ID* ]

               --**vlan**: [ "all" \| *VLAN ID* ]
**Data**       **address_id**:[ 1 - ... ]
**Remarks**    Specification of VLAN ID is optional.
=============  ==========================================


Deleting a Route
^^^^^^^^^^^^^^^^

=============  ==========================================
**Method**     DELETE
**URL**        /router/{**switch**}[/{**vlan**}]

               --**switch**: [ "all" \| *Switch ID* ]

               --**vlan**: [ "all" \| *VLAN ID* ]
**Data**       **route_id**:[ 1 - ... ]
**Remarks**    Specification of VLAN ID is optional.
=============  ==========================================
