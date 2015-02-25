.. _ch_rest_firewall:

Firewall
========

This section describes how to use Firewall, which can be set using REST.


Example of operation of a single tenant (IPv4)
----------------------------------------------

The following shows an example of creating a topology such as the following and adding or deleting a route or address for switch s1.

.. only:: latex

  .. image:: images/rest_firewall/fig1.eps
     :scale: 80%
     :align: center

.. only:: epub

  .. image:: images/rest_firewall/fig1.png
     :align: center

.. only:: not latex and not epub

  .. image:: images/rest_firewall/fig1.png
     :scale: 40%
     :align: center


Environment Building
^^^^^^^^^^^^^^^^^^^^

First, build an environment on Mininet. The commands to be entered are the same as ":ref:`ch_switching_hub`"

.. rst-class:: console

::

    ryu@ryu-vm:~$ sudo mn --topo single,3 --mac --switch ovsk --controller remote -x
    *** Creating network
    *** Adding controller
    Unable to contact the remote controller at 127.0.0.1:6633
    *** Adding hosts:
    h1 h2 h3
    *** Adding switches:
    s1
    *** Adding links:
    (h1, s1) (h2, s1) (h3, s1)
    *** Configuring hosts
    h1 h2 h3
    *** Running terms on localhost:10.0
    *** Starting controller
    *** Starting 1 switches
    s1

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

    root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13

Finally, start rest_firewall on xterm of the controller.

controller: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ryu-manager ryu.app.rest_firewall
    loading app ryu.app.rest_firewall
    loading app ryu.controller.ofp_handler
    instantiating app None of DPSet
    creating context dpset
    creating context wsgi
    instantiating app ryu.app.rest_firewall of RestFirewallAPI
    instantiating app ryu.controller.ofp_handler of OFPHandler
    (2210) wsgi starting up on http://0.0.0.0:8080/

After a successful connection between the router and Ryu, the following message appears.

controller: c0 (root):

.. rst-class:: console

::

    [FW][INFO] switch_id=0000000000000001: Join as firewall



Changing in the initial state
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Immediately after starting the firewall, it was set to disable status to cut off all communication. Enable it with the following command.

.. NOTE::

    For details of REST API used in the following description, please see "`REST API List`_" at the end of the section.



Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X PUT http://localhost:8080/firewall/module/enable/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": {
            "result": "success",
            "details": "firewall running."
          }
        }
      ]

    root@ryu-vm:~# curl http://localhost:8080/firewall/module/status
      [
        {
          "status": "enable",
          "switch_id": "0000000000000001"
        }
      ]

.. NOTE::

    The result of the REST command is formatted for easy viewing.


Check ping communication from h1 to h2. Since access permission rules are not set, communication will be blocked.

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ping 10.0.0.2
    PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
    ^C
    --- 10.0.0.2 ping statistics ---
    20 packets transmitted, 0 received, 100% packet loss, time 19003ms

Packets that are blocked are output to the log.

controller: c0 (root):

.. rst-class:: console

::

    [FW][INFO] dpid=0000000000000001: Blocked packet = ethernet(dst='00:00:00:00:00:02',ethertype=2048,src='00:00:00:00:00:01'), ipv4(csum=9895,dst='10.0.0.2',flags=2,header_length=5,identification=0,offset=0,option=None,proto=1,src='10.0.0.1',tos=0,total_length=84,ttl=64,version=4), icmp(code=0,csum=55644,data=echo(data='K\x8e\xaeR\x00\x00\x00\x00=\xc6\r\x00\x00\x00\x00\x00\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./01234567',id=6952,seq=1),type=8)
    ...

Adding a Rule
^^^^^^^^^^^^^

Add a rule to permit pinging between h1 and h2. You need to add the rule for both ways.

Let's add the following rules. Rule ID is assigned automatically.

============  ============  ===========  ===========  ===========
Source        Destination   Protocol     Permission   (Rule ID)
============  ============  ===========  ===========  ===========
10.0.0.1/32   10.0.0.2/32   ICMP         Allow        1
10.0.0.2/32   10.0.0.1/32   ICMP         Allow        2
============  ============  ===========  ===========  ===========

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"nw_src": "10.0.0.1/32", "nw_dst": "10.0.0.2/32", "nw_proto": "ICMP"}' http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Rule added. : rule_id=1"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"nw_src": "10.0.0.2/32", "nw_dst": "10.0.0.1/32", "nw_proto": "ICMP"}' http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Rule added. : rule_id=2"
            }
          ]
        }
      ]

Added rules are registered in the switch as flow entries.

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=823.705s, table=0, n_packets=10, n_bytes=420, priority=65534,arp actions=NORMAL
     cookie=0x0, duration=542.472s, table=0, n_packets=20, n_bytes=1960, priority=0 actions=CONTROLLER:128
     cookie=0x1, duration=145.05s, table=0, n_packets=0, n_bytes=0, priority=1,icmp,nw_src=10.0.0.1,nw_dst=10.0.0.2 actions=NORMAL
     cookie=0x2, duration=118.265s, table=0, n_packets=0, n_bytes=0, priority=1,icmp,nw_src=10.0.0.2,nw_dst=10.0.0.1 actions=NORMAL

In addition, add a rule to allow all IPv4 packets, including ping, between h3 and h2.

============  ============  ===========  ===========  ===========
Source        Destination   Protocol     Permission   (Rule ID)
============  ============  ===========  ===========  ===========
10.0.0.2/32   10.0.0.3/32   any          Allow        3
10.0.0.3/32   10.0.0.2/32   any          Allow        4
============  ============  ===========  ===========  ===========

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"nw_src": "10.0.0.2/32", "nw_dst": "10.0.0.3/32"}' http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Rule added. : rule_id=3"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"nw_src": "10.0.0.3/32", "nw_dst": "10.0.0.2/32"}' http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Rule added. : rule_id=4"
            }
          ]
        }
      ]

Added rules are registered in the switch as flow entries.

switch: s1 (root):

.. rst-class:: console

::

    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x3, duration=12.724s, table=0, n_packets=0, n_bytes=0, priority=1,ip,nw_src=10.0.0.2,nw_dst=10.0.0.3 actions=NORMAL
     cookie=0x4, duration=3.668s, table=0, n_packets=0, n_bytes=0, priority=1,ip,nw_src=10.0.0.3,nw_dst=10.0.0.2 actions=NORMAL
     cookie=0x0, duration=1040.802s, table=0, n_packets=10, n_bytes=420, priority=65534,arp actions=NORMAL
     cookie=0x0, duration=759.569s, table=0, n_packets=20, n_bytes=1960, priority=0 actions=CONTROLLER:128
     cookie=0x1, duration=362.147s, table=0, n_packets=0, n_bytes=0, priority=1,icmp,nw_src=10.0.0.1,nw_dst=10.0.0.2 actions=NORMAL
     cookie=0x2, duration=335.362s, table=0, n_packets=0, n_bytes=0, priority=1,icmp,nw_src=10.0.0.2,nw_dst=10.0.0.1 actions=NORMAL

Priority can be set to rules.

Try to add a rule to block pings (ICMP) between h3 and h2.
Set a value greater than 1, which is default value of priority.

==========  ============  ============  =========  ===========  ===========
(Priority)  Source        Destination   Protocol    Permission   (Rule ID)
==========  ============  ============  =========  ===========  ===========
10          10.0.0.2/32   10.0.0.3/32   ICMP        Block        5
10          10.0.0.3/32   10.0.0.2/32   ICMP        Block        6
==========  ============  ============  =========  ===========  ===========

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d  '{"nw_src": "10.0.0.2/32", "nw_dst": "10.0.0.3/32", "nw_proto": "ICMP", "actions": "DENY", "priority": "10"}' http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Rule added. : rule_id=5"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d  '{"nw_src": "10.0.0.3/32", "nw_dst": "10.0.0.2/32", "nw_proto": "ICMP", "actions": "DENY", "priority": "10"}' http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Rule added. : rule_id=6"
            }
          ]
        }
      ]

Added rules are registered in the switch as flow entries.

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x3, duration=242.155s, table=0, n_packets=0, n_bytes=0, priority=1,ip,nw_src=10.0.0.2,nw_dst=10.0.0.3 actions=NORMAL
     cookie=0x4, duration=233.099s, table=0, n_packets=0, n_bytes=0, priority=1,ip,nw_src=10.0.0.3,nw_dst=10.0.0.2 actions=NORMAL
     cookie=0x0, duration=1270.233s, table=0, n_packets=10, n_bytes=420, priority=65534,arp actions=NORMAL
     cookie=0x0, duration=989s, table=0, n_packets=20, n_bytes=1960, priority=0 actions=CONTROLLER:128
     cookie=0x5, duration=26.984s, table=0, n_packets=0, n_bytes=0, priority=10,icmp,nw_src=10.0.0.2,nw_dst=10.0.0.3 actions=CONTROLLER:128
     cookie=0x1, duration=591.578s, table=0, n_packets=0, n_bytes=0, priority=1,icmp,nw_src=10.0.0.1,nw_dst=10.0.0.2 actions=NORMAL
     cookie=0x6, duration=14.523s, table=0, n_packets=0, n_bytes=0, priority=10,icmp,nw_src=10.0.0.3,nw_dst=10.0.0.2 actions=CONTROLLER:128
     cookie=0x2, duration=564.793s, table=0, n_packets=0, n_bytes=0, priority=1,icmp,nw_src=10.0.0.2,nw_dst=10.0.0.1 actions=NORMAL


Confirming Rules
^^^^^^^^^^^^^^^^

Confirm the rules that have been set.

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "access_control_list": [
            {
              "rules": [
                {
                  "priority": 1,
                  "dl_type": "IPv4",
                  "nw_dst": "10.0.0.3",
                  "nw_src": "10.0.0.2",
                  "rule_id": 3,
                  "actions": "ALLOW"
                },
                {
                  "priority": 1,
                  "dl_type": "IPv4",
                  "nw_dst": "10.0.0.2",
                  "nw_src": "10.0.0.3",
                  "rule_id": 4,
                  "actions": "ALLOW"
                },
                {
                  "priority": 10,
                  "dl_type": "IPv4",
                  "nw_proto": "ICMP",
                  "nw_dst": "10.0.0.3",
                  "nw_src": "10.0.0.2",
                  "rule_id": 5,
                  "actions": "DENY"
                },
                {
                  "priority": 1,
                  "dl_type": "IPv4",
                  "nw_proto": "ICMP",
                  "nw_dst": "10.0.0.2",
                  "nw_src": "10.0.0.1",
                  "rule_id": 1,
                  "actions": "ALLOW"
                },
                {
                  "priority": 10,
                  "dl_type": "IPv4",
                  "nw_proto": "ICMP",
                  "nw_dst": "10.0.0.2",
                  "nw_src": "10.0.0.3",
                  "rule_id": 6,
                  "actions": "DENY"
                },
                {
                  "priority": 1,
                  "dl_type": "IPv4",
                  "nw_proto": "ICMP",
                  "nw_dst": "10.0.0.1",
                  "nw_src": "10.0.0.2",
                  "rule_id": 2,
                  "actions": "ALLOW"
                }
              ]
            }
          ],
          "switch_id": "0000000000000001"
        }
      ]

The following shows the rules set.

.. only:: latex

  .. image:: images/rest_firewall/fig2.eps
     :scale: 80%
     :align: center

.. only:: epub

  .. image:: images/rest_firewall/fig2.png
     :align: center

.. only:: not latex and not epub

  .. image:: images/rest_firewall/fig2.png
     :scale: 40%
     :align: center

Try to send a ping from h1 to h2. Since rules to allow communication are set, the ping will go through.

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ping 10.0.0.2
    PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
    64 bytes from 10.0.0.2: icmp_req=1 ttl=64 time=0.419 ms
    64 bytes from 10.0.0.2: icmp_req=2 ttl=64 time=0.047 ms
    64 bytes from 10.0.0.2: icmp_req=3 ttl=64 time=0.060 ms
    64 bytes from 10.0.0.2: icmp_req=4 ttl=64 time=0.033 ms
    ...

Packets from h1 to h2 other than ping are blocked by the firewall. For example, if you execute wget from h1 to h2, a log is output that packets were blocked.

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# wget http://10.0.0.2
    --2013-12-16 15:00:38--  http://10.0.0.2/
    Connecting to 10.0.0.2:80... ^C

controller: c0 (root):

.. rst-class:: console

::

    [FW][INFO] dpid=0000000000000001: Blocked packet = ethernet(dst='00:00:00:00:00:02',ethertype=2048,src='00:00:00:00:00:01'), ipv4(csum=4812,dst='10.0.0.2',flags=2,header_length=5,identification=5102,offset=0,option=None,proto=6,src='10.0.0.1',tos=0,total_length=60,ttl=64,version=4), tcp(ack=0,bits=2,csum=45753,dst_port=80,offset=10,option='\x02\x04\x05\xb4\x04\x02\x08\n\x00H:\x99\x00\x00\x00\x00\x01\x03\x03\t',seq=1021913463,src_port=42664,urgent=0,window_size=14600)
    ...

Between h2 and 3h, packets other than ping can communicate. For example, if you execute ssh from h2 to h3, it will not output a log that packets were blocked. (Since sshd is not operating in h3, communication by ssh will fail.)

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# ssh 10.0.0.3
    ssh: connect to host 10.0.0.3 port 22: Connection refused

If you execute ping from h2 to h3, a log is output that packets were blocked by the firewall.

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# ping 10.0.0.3
    PING 10.0.0.3 (10.0.0.3) 56(84) bytes of data.
    ^C
    --- 10.0.0.3 ping statistics ---
    8 packets transmitted, 0 received, 100% packet loss, time 7055ms

controller: c0 (root):

.. rst-class:: console

::

    [FW][INFO] dpid=0000000000000001: Blocked packet = ethernet(dst='00:00:00:00:00:03',ethertype=2048,src='00:00:00:00:00:02'), ipv4(csum=9893,dst='10.0.0.3',flags=2,header_length=5,identification=0,offset=0,option=None,proto=1,src='10.0.0.2',tos=0,total_length=84,ttl=64,version=4), icmp(code=0,csum=35642,data=echo(data='\r\x12\xcaR\x00\x00\x00\x00\xab\x8b\t\x00\x00\x00\x00\x00\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./01234567',id=8705,seq=1),type=8)
    ...


Deleting a Rule
^^^^^^^^^^^^^^^

Delete the "rule_id:5" and "rule_id:6" rules.

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X DELETE -d '{"rule_id": "5"}' http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Rule deleted. : ruleID=5"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X DELETE -d '{"rule_id": "6"}' http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Rule deleted. : ruleID=6"
            }
          ]
        }
      ]


The following shows the current rules.

.. only:: latex

  .. image:: images/rest_firewall/fig3.eps
     :scale: 80%
     :align: center

.. only:: epub

  .. image:: images/rest_firewall/fig3.png
     :align: center

.. only:: not latex and not epub

  .. image:: images/rest_firewall/fig3.png
     :scale: 40%
     :align: center


Let's confirm them. Since the rule to block pings (ICMP) between h2 and h3 is deleted, you can see that ping can now communicate.

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# ping 10.0.0.3
    PING 10.0.0.3 (10.0.0.3) 56(84) bytes of data.
    64 bytes from 10.0.0.3: icmp_req=1 ttl=64 time=0.841 ms
    64 bytes from 10.0.0.3: icmp_req=2 ttl=64 time=0.036 ms
    64 bytes from 10.0.0.3: icmp_req=3 ttl=64 time=0.026 ms
    64 bytes from 10.0.0.3: icmp_req=4 ttl=64 time=0.033 ms
    ...


Example of the Operation of a Multi-tenant (IPv4)
-------------------------------------------------

The following shows an example of creating a topology where tenants are divided by VLAN such as the following and routes or addresses for each switch s1 are added or deleted and communication availability between each host is verified.

.. only:: latex

  .. image:: images/rest_firewall/fig4.eps
     :scale: 80%
     :align: center

.. only:: epub

  .. image:: images/rest_firewall/fig4.png
     :align: center

.. only:: not latex and not epub

  .. image:: images/rest_firewall/fig4.png
     :scale: 40%
     :align: center


Building an Environment
^^^^^^^^^^^^^^^^^^^^^^^

As with the example of Single-tenant, build an environment on Mininet and start another xterm for controller. Note that there is one more host to be used than before.

.. rst-class:: console

::

    ryu@ryu-vm:~$ sudo mn --topo single,4 --mac --switch ovsk --controller remote -x
    *** Creating network
    *** Adding controller
    Unable to contact the remote controller at 127.0.0.1:6633
    *** Adding hosts:
    h1 h2 h3 h4
    *** Adding switches:
    s1
    *** Adding links:
    (h1, s1) (h2, s1) (h3, s1) (h4, s1)
    *** Configuring hosts
    h1 h2 h3 h4
    *** Running terms on localhost:10.0
    *** Starting controller
    *** Starting 1 switches
    s1

    *** Starting CLI:
    mininet> xterm c0
    mininet>

Next, set the VLAN ID to the interface of each host.

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.1/8 dev h1-eth0
    root@ryu-vm:~# ip link add link h1-eth0 name h1-eth0.2 type vlan id 2
    root@ryu-vm:~# ip addr add 10.0.0.1/8 dev h1-eth0.2
    root@ryu-vm:~# ip link set dev h1-eth0.2 up

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.2/8 dev h2-eth0
    root@ryu-vm:~# ip link add link h2-eth0 name h2-eth0.2 type vlan id 2
    root@ryu-vm:~# ip addr add 10.0.0.2/8 dev h2-eth0.2
    root@ryu-vm:~# ip link set dev h2-eth0.2 up

host: h3:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.3/8 dev h3-eth0
    root@ryu-vm:~# ip link add link h3-eth0 name h3-eth0.110 type vlan id 110
    root@ryu-vm:~# ip addr add 10.0.0.3/8 dev h3-eth0.110
    root@ryu-vm:~# ip link set dev h3-eth0.110 up

host: h4:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del 10.0.0.4/8 dev h4-eth0
    root@ryu-vm:~# ip link add link h4-eth0 name h4-eth0.110 type vlan id 110
    root@ryu-vm:~# ip addr add 10.0.0.4/8 dev h4-eth0.110
    root@ryu-vm:~# ip link set dev h4-eth0.110 up

Then, set the version of OpenFlow to be used in each router to 1.3.

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13

Finally, start rest_firewall on an xterm of the controller.

controller: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ryu-manager ryu.app.rest_firewall
    loading app ryu.app.rest_firewall
    loading app ryu.controller.ofp_handler
    instantiating app None of DPSet
    creating context dpset
    creating context wsgi
    instantiating app ryu.app.rest_firewall of RestFirewallAPI
    instantiating app ryu.controller.ofp_handler of OFPHandler
    (13419) wsgi starting up on http://0.0.0.0:8080/

After a successful connection between the router and Ryu, the following message appears.

controller: c0 (root):

.. rst-class:: console

::

    [FW][INFO] switch_id=0000000000000001: Join as firewall


Changing the Initial State
^^^^^^^^^^^^^^^^^^^^^^^^^^

Enable the firewall.

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X PUT http://localhost:8080/firewall/module/enable/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": {
            "result": "success",
            "details": "firewall running."
          }
        }
      ]

    root@ryu-vm:~# curl http://localhost:8080/firewall/module/status
      [
        {
          "status": "enable",
          "switch_id": "0000000000000001"
        }
      ]


Adding Rules
^^^^^^^^^^^^

Add a rule to vlan_id = 2 that allows pings (ICMP packets) to be sent and received to 10.0.0.0/8. Since there is a need to set rules in both directions, add two rules.

===========  ========  ============  ============  =========  ===========  ==========
(Priority)   VLAN ID   Source        Destination   Protocol   Permission   (Rule ID)
===========  ========  ============  ============  =========  ===========  ==========
1            2         10.0.0.0/8    any           ICMP       Allow        1
1            2         any           10.0.0.0/8    ICMP       Allow        2
===========  ========  ============  ============  =========  ===========  ==========

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"nw_src": "10.0.0.0/8", "nw_proto": "ICMP"}' http://localhost:8080/firewall/rules/0000000000000001/2
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Rule added. : rule_id=1"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"nw_dst": "10.0.0.0/8", "nw_proto": "ICMP"}' http://localhost:8080/firewall/rules/0000000000000001/2
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "vlan_id": 2,
              "details": "Rule added. : rule_id=2"
            }
          ]
        }
      ]


Confirming Rules
^^^^^^^^^^^^^^^^

Confirm the rules that have been set.

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl http://localhost:8080/firewall/rules/0000000000000001/all
      [
        {
          "access_control_list": [
            {
              "rules": [
                {
                  "priority": 1,
                  "dl_type": "IPv4",
                  "nw_proto": "ICMP",
                  "dl_vlan": 2,
                  "nw_src": "10.0.0.0/8",
                  "rule_id": 1,
                  "actions": "ALLOW"
                },
                {
                  "priority": 1,
                  "dl_type": "IPv4",
                  "nw_proto": "ICMP",
                  "nw_dst": "10.0.0.0/8",
                  "dl_vlan": 2,
                  "rule_id": 2,
                  "actions": "ALLOW"
                }
              ],
              "vlan_id": 2
            }
          ],
          "switch_id": "0000000000000001"
        }
      ]


Let's confirm them. When you execute ping from h1, which is vlan_id=2, to h2 which is also vlan_id=2, you can see that it can communicate per the rules that were added.

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ping 10.0.0.2
    PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
    64 bytes from 10.0.0.2: icmp_req=1 ttl=64 time=0.893 ms
    64 bytes from 10.0.0.2: icmp_req=2 ttl=64 time=0.098 ms
    64 bytes from 10.0.0.2: icmp_req=3 ttl=64 time=0.122 ms
    64 bytes from 10.0.0.2: icmp_req=4 ttl=64 time=0.047 ms
    ...


Since there is no rule between h3 and h4, which are both vlan_id=110, packets are blocked.


host: h3:

.. rst-class:: console

::

    root@ryu-vm:~# ping 10.0.0.4
    PING 10.0.0.4 (10.0.0.4) 56(84) bytes of data.
    ^C
    --- 10.0.0.4 ping statistics ---
    6 packets transmitted, 0 received, 100% packet loss, time 4999ms

Since packets are blocked, a log is output.

controller: c0 (root):

.. rst-class:: console

::

    [FW][INFO] dpid=0000000000000001: Blocked packet = ethernet(dst='00:00:00:00:00:04',ethertype=33024,src='00:00:00:00:00:03'), vlan(cfi=0,ethertype=2048,pcp=0,vid=110), ipv4(csum=9891,dst='10.0.0.4',flags=2,header_length=5,identification=0,offset=0,option=None,proto=1,src='10.0.0.3',tos=0,total_length=84,ttl=64,version=4), icmp(code=0,csum=58104,data=echo(data='\xb8\xa9\xaeR\x00\x00\x00\x00\xce\xe3\x02\x00\x00\x00\x00\x00\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./01234567',id=7760,seq=4),type=8)
    ...


Example of operation of a single tenant (IPv6)
----------------------------------------------

The following shows an example of creating a topology where hosts are assigned with IPv6 address such as the following and routes or addresses for each switch s1 are added or deleted and communication availability between each host is verified.

.. only:: latex

  .. image:: images/rest_firewall/fig5.eps
     :scale: 80%
     :align: center

.. only:: epub

  .. image:: images/rest_firewall/fig5.png
     :align: center

.. only:: not latex and not epub

  .. image:: images/rest_firewall/fig5.png
     :scale: 40%
     :align: center


Environment Building
^^^^^^^^^^^^^^^^^^^^

First, build an environment on Mininet. The commands to be entered are the same as "`Example of operation of a single tenant (IPv4)`_".

.. rst-class:: console

::

    ryu@ryu-vm:~$ sudo mn --topo single,3 --mac --switch ovsk --controller remote -x
    *** Creating network
    *** Adding controller
    Unable to contact the remote controller at 127.0.0.1:6633
    *** Adding hosts:
    h1 h2 h3
    *** Adding switches:
    s1
    *** Adding links:
    (h1, s1) (h2, s1) (h3, s1)
    *** Configuring hosts
    h1 h2 h3
    *** Running terms on localhost:10.0
    *** Starting controller
    *** Starting 1 switches
    s1
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

    root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13

Finally, start rest_firewall on xterm of the controller.

controller: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ryu-manager ryu.app.rest_firewall
    loading app ryu.app.rest_firewall
    loading app ryu.controller.ofp_handler
    instantiating app None of DPSet
    creating context dpset
    creating context wsgi
    instantiating app ryu.app.rest_firewall of RestFirewallAPI
    instantiating app ryu.controller.ofp_handler of OFPHandler
    (2210) wsgi starting up on http://0.0.0.0:8080/

After a successful connection between the router and Ryu, the following message appears.

controller: c0 (root):

.. rst-class:: console

::

    [FW][INFO] switch_id=0000000000000001: Join as firewall


Changing the Initial State
^^^^^^^^^^^^^^^^^^^^^^^^^^

Enable the firewall.

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X PUT http://localhost:8080/firewall/module/enable/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": {
            "result": "success",
            "details": "firewall running."
          }
        }
      ]

    root@ryu-vm:~# curl http://localhost:8080/firewall/module/status
      [
        {
          "status": "enable",
          "switch_id": "0000000000000001"
        }
      ]


Adding Rules
^^^^^^^^^^^^

Add rules to permit pinging between h1 and h2. You need to add rules for both ways.

=================== =================== ========= ========== ========= ======================================
Source              Destination         Protocol  Permission (Rule ID) (Note)
=================== =================== ========= ========== ========= ======================================
fe80::200:ff:fe00:1 fe80::200:ff:fe00:2 ICMPv6    Allow      1         Unicast message (Echo)
fe80::200:ff:fe00:2 fe80::200:ff:fe00:1 ICMPv6    Allow      2         Unicast message (Echo)
fe80::200:ff:fe00:1 ff02::1:ff00:2      ICMPv6    Allow      3         Multicast message (Neighbor Discovery)
fe80::200:ff:fe00:2 ff02::1:ff00:1      ICMPv6    Allow      4         Multicast message (Neighbor Discovery)
=================== =================== ========= ========== ========= ======================================

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"ipv6_src": "fe80::200:ff:fe00:1", "ipv6_dst": "fe80::200:ff:fe00:2", "nw_proto": "ICMPv6"}' http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Rule added. : rule_id=1"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"ipv6_src": "fe80::200:ff:fe00:2", "ipv6_dst": "fe80::200:ff:fe00:1", "nw_proto": "ICMPv6"}' http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Rule added. : rule_id=2"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"ipv6_src": "fe80::200:ff:fe00:1", "ipv6_dst": "ff02::1:ff00:2", "nw_proto": "ICMPv6"}' http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Rule added. : rule_id=3"
            }
          ]
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"ipv6_src": "fe80::200:ff:fe00:2", "ipv6_dst": "ff02::1:ff00:1", "nw_proto": "ICMPv6"}' http://localhost:8080/firewall/rules/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": [
            {
              "result": "success",
              "details": "Rule added. : rule_id=4"
            }
          ]
        }
      ]


Confirming Rules
^^^^^^^^^^^^^^^^

Confirm the rules that have been set.

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl http://localhost:8080/firewall/rules/0000000000000001/all
      [
        {
          "switch_id": "0000000000000001",
          "access_control_list": [
            {
              "rules": [
                {
                  "ipv6_dst": "fe80::200:ff:fe00:2",
                  "actions": "ALLOW",
                  "rule_id": 1,
                  "ipv6_src": "fe80::200:ff:fe00:1",
                  "nw_proto": "ICMPv6",
                  "dl_type": "IPv6",
                  "priority": 1
                },
                {
                  "ipv6_dst": "fe80::200:ff:fe00:1",
                  "actions": "ALLOW",
                  "rule_id": 2,
                  "ipv6_src": "fe80::200:ff:fe00:2",
                  "nw_proto": "ICMPv6",
                  "dl_type": "IPv6",
                  "priority": 1
                },
                {
                  "ipv6_dst": "ff02::1:ff00:2",
                  "actions": "ALLOW",
                  "rule_id": 3,
                  "ipv6_src": "fe80::200:ff:fe00:1",
                  "nw_proto": "ICMPv6",
                  "dl_type": "IPv6",
                  "priority": 1
                },
                {
                  "ipv6_dst": "ff02::1:ff00:1",
                  "actions": "ALLOW",
                  "rule_id": 4,
                  "ipv6_src": "fe80::200:ff:fe00:2",
                  "nw_proto": "ICMPv6",
                  "dl_type": "IPv6",
                  "priority": 1
                }
              ]
            }
          ]
        }
      ]


Let's confirm them. When you execute ping from h1 to h2, you can see that it can communicate per the rules that were added.

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ping6 -I h1-eth0 fe80::200:ff:fe00:2
    PING fe80::200:ff:fe00:2(fe80::200:ff:fe00:2) from fe80::200:ff:fe00:1 h1-eth0: 56 data bytes
    64 bytes from fe80::200:ff:fe00:2: icmp_seq=1 ttl=64 time=0.954 ms
    64 bytes from fe80::200:ff:fe00:2: icmp_seq=2 ttl=64 time=0.047 ms
    64 bytes from fe80::200:ff:fe00:2: icmp_seq=3 ttl=64 time=0.055 ms
    64 bytes from fe80::200:ff:fe00:2: icmp_seq=4 ttl=64 time=0.027 ms
    ...


Since there is no rule between h1 and h3, packets are blocked.


host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ping6 -I h1-eth0 fe80::200:ff:fe00:3
    PING fe80::200:ff:fe00:3(fe80::200:ff:fe00:3) from fe80::200:ff:fe00:1 h1-eth0: 56 data bytes
    From fe80::200:ff:fe00:1 icmp_seq=1 Destination unreachable: Address unreachable
    From fe80::200:ff:fe00:1 icmp_seq=2 Destination unreachable: Address unreachable
    From fe80::200:ff:fe00:1 icmp_seq=3 Destination unreachable: Address unreachable
    ^C
    --- fe80::200:ff:fe00:3 ping statistics ---
    4 packets transmitted, 0 received, +3 errors, 100% packet loss, time 2999ms

Since packets are blocked, a log is output.

controller: c0 (root):

.. rst-class:: console

::

    [FW][INFO] dpid=0000000000000001: Blocked packet = ethernet(dst='33:33:ff:00:00:03',ethertype=34525,src='00:00:00:00:00:01'), ipv6(dst='ff02::1:ff00:3',ext_hdrs=[],flow_label=0,hop_limit=255,nxt=58,payload_length=32,src='fe80::200:ff:fe00:1',traffic_class=0,version=6), icmpv6(code=0,csum=31381,data=nd_neighbor(dst='fe80::200:ff:fe00:3',option=nd_option_sla(data=None,hw_src='00:00:00:00:00:01',length=1),res=0),type_=135)
    ...


Example of the Operation of a Multi-tenant (IPv6)
-------------------------------------------------

The following shows an example of creating a topology where tenants are divided by VLAN and assigned with IPv6 address such as the following, routes or addresses for each switch s1 are added or deleted and communication availability between each host is verified.

.. only:: latex

  .. image:: images/rest_firewall/fig6.eps
     :scale: 80%
     :align: center

.. only:: epub

  .. image:: images/rest_firewall/fig6.png
     :align: center

.. only:: not latex and not epub

  .. image:: images/rest_firewall/fig6.png
     :scale: 40%
     :align: center


Building an Environment
^^^^^^^^^^^^^^^^^^^^^^^

As with "`Example of the Operation of a Multi-tenant (IPv4)`_", build an environment on Mininet and start another xterm for controller.

.. rst-class:: console

::

    ryu@ryu-vm:~$ sudo mn --topo single,4 --mac --switch ovsk --controller remote -x
    *** Creating network
    *** Adding controller
    Unable to contact the remote controller at 127.0.0.1:6633
    *** Adding hosts:
    h1 h2 h3 h4
    *** Adding switches:
    s1
    *** Adding links:
    (h1, s1) (h2, s1) (h3, s1) (h4, s1)
    *** Configuring hosts
    h1 h2 h3 h4
    *** Running terms on localhost:10.0
    *** Starting controller
    *** Starting 1 switches
    s1
    *** Starting CLI:
    mininet> xterm c0
    mininet>

Next, set the VLAN ID to the interface of each host.

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del fe80::200:ff:fe00:1/64 dev h1-eth0
    root@ryu-vm:~# ip link add link h1-eth0 name h1-eth0.2 type vlan id 2
    root@ryu-vm:~# ip addr add fe80::200:ff:fe00:1/64 dev h1-eth0.2
    root@ryu-vm:~# ip link set dev h1-eth0.2 up

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del fe80::200:ff:fe00:2/64 dev h2-eth0
    root@ryu-vm:~# ip link add link h2-eth0 name h2-eth0.2 type vlan id 2
    root@ryu-vm:~# ip addr add fe80::200:ff:fe00:2/64 dev h2-eth0.2
    root@ryu-vm:~# ip link set dev h2-eth0.2 up

host: h3:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del fe80::200:ff:fe00:3/64 dev h3-eth0
    root@ryu-vm:~# ip link add link h3-eth0 name h3-eth0.110 type vlan id 110
    root@ryu-vm:~# ip addr add fe80::200:ff:fe00:3/64 dev h3-eth0.110
    root@ryu-vm:~# ip link set dev h3-eth0.110 up

host: h4:

.. rst-class:: console

::

    root@ryu-vm:~# ip addr del fe80::200:ff:fe00:4/64 dev h4-eth0
    root@ryu-vm:~# ip link add link h4-eth0 name h4-eth0.110 type vlan id 110
    root@ryu-vm:~# ip addr add fe80::200:ff:fe00:4/64 dev h4-eth0.110
    root@ryu-vm:~# ip link set dev h4-eth0.110 up

Then, set the version of OpenFlow to be used in each router to 1.3.

switch: s1 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13

Finally, start rest_firewall on an xterm of the controller.

controller: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# ryu-manager ryu.app.rest_firewall
    loading app ryu.app.rest_firewall
    loading app ryu.controller.ofp_handler
    instantiating app None of DPSet
    creating context dpset
    creating context wsgi
    instantiating app ryu.app.rest_firewall of RestFirewallAPI
    instantiating app ryu.controller.ofp_handler of OFPHandler
    (13419) wsgi starting up on http://0.0.0.0:8080/

After a successful connection between the router and Ryu, the following message appears.

controller: c0 (root):

.. rst-class:: console

::

    [FW][INFO] switch_id=0000000000000001: Join as firewall


Changing the Initial State
^^^^^^^^^^^^^^^^^^^^^^^^^^

Enable the firewall.

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X PUT http://localhost:8080/firewall/module/enable/0000000000000001
      [
        {
          "switch_id": "0000000000000001",
          "command_result": {
            "result": "success",
            "details": "firewall running."
          }
        }
      ]

    root@ryu-vm:~# curl http://localhost:8080/firewall/module/status
      [
        {
          "status": "enable",
          "switch_id": "0000000000000001"
        }
      ]


Adding Rules
^^^^^^^^^^^^

Add a rule to vlan_id = 2 that allows pings (ICMPv6 packets) to be sent and received to fe80::/64. Since there is a need to set rules in both directions, add two rules.

===========  ========  ===================  ============  =========  ===========  ==========
(Priority)   VLAN ID   Source               Destination   Protocol   Permission   (Rule ID)
===========  ========  ===================  ============  =========  ===========  ==========
1            2         fe80::200:ff:fe00:1  any           ICMPv6     Allow        1
1            2         fe80::200:ff:fe00:2  any           ICMPv6     Allow        2
===========  ========  ===================  ============  =========  ===========  ==========

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl -X POST -d '{"ipv6_src": "fe80::200:ff:fe00:1", "nw_proto": "ICMPv6"}' http://localhost:8080/firewall/rules/0000000000000001/2
      [
        {
          "command_result": [
            {
              "details": "Rule added. : rule_id=1",
              "vlan_id": 2,
              "result": "success"
            }
          ],
          "switch_id": "0000000000000001"
        }
      ]

    root@ryu-vm:~# curl -X POST -d '{"ipv6_src": "fe80::200:ff:fe00:2", "nw_proto": "ICMPv6"}' http://localhost:8080/firewall/rules/0000000000000001/2
      [
        {
          "command_result": [
            {
              "details": "Rule added. : rule_id=2",
              "vlan_id": 2,
              "result": "success"
            }
          ],
          "switch_id": "0000000000000001"
        }
      ]


Confirming Rules
^^^^^^^^^^^^^^^^

Confirm the rules that have been set.

Node: c0 (root):

.. rst-class:: console

::

    root@ryu-vm:~# curl http://localhost:8080/firewall/rules/0000000000000001/all
      [
        {
          "switch_id": "0000000000000001",
          "access_control_list": [
            {
              "vlan_id": "2",
              "rules": [
                {
                  "actions": "ALLOW",
                  "rule_id": 1,
                  "dl_vlan": "2",
                  "ipv6_src": "fe80::200:ff:fe00:1",
                  "nw_proto": "ICMPv6",
                  "dl_type": "IPv6",
                  "priority": 1
                },
                {
                  "actions": "ALLOW",
                  "rule_id": 2,
                  "dl_vlan": "2",
                  "ipv6_src": "fe80::200:ff:fe00:2",
                  "nw_proto": "ICMPv6",
                  "dl_type": "IPv6",
                  "priority": 1
                }
              ]
            }
          ]
        }
      ]

Let's confirm them. When you execute ping from h1, which is vlan_id=2, to h2 which is also vlan_id=2, you can see that it can communicate per the rules that were added.

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ping6 -I h1-eth0.2 fe80::200:ff:fe00:2
    PING fe80::200:ff:fe00:2(fe80::200:ff:fe00:2) from fe80::200:ff:fe00:1 h1-eth0.2: 56 data bytes
    64 bytes from fe80::200:ff:fe00:2: icmp_seq=1 ttl=64 time=0.609 ms
    64 bytes from fe80::200:ff:fe00:2: icmp_seq=2 ttl=64 time=0.046 ms
    64 bytes from fe80::200:ff:fe00:2: icmp_seq=3 ttl=64 time=0.046 ms
    64 bytes from fe80::200:ff:fe00:2: icmp_seq=4 ttl=64 time=0.057 ms
    ...


Since there is no rule between h3 and h4, which are both vlan_id=110, packets are blocked.


host: h3:

.. rst-class:: console

::

    root@ryu-vm:~# ping6 -I h3-eth0.110 fe80::200:ff:fe00:4
    PING fe80::200:ff:fe00:4(fe80::200:ff:fe00:4) from fe80::200:ff:fe00:3 h3-eth0.110: 56 data bytes
    From fe80::200:ff:fe00:3 icmp_seq=1 Destination unreachable: Address unreachable
    From fe80::200:ff:fe00:3 icmp_seq=2 Destination unreachable: Address unreachable
    From fe80::200:ff:fe00:3 icmp_seq=3 Destination unreachable: Address unreachable
    ^C
    --- fe80::200:ff:fe00:4 ping statistics ---
    4 packets transmitted, 0 received, +3 errors, 100% packet loss, time 3014ms

Since packets are blocked, a log is output.

controller: c0 (root):

.. rst-class:: console

::

    [FW][INFO] dpid=0000000000000001: Blocked packet = ethernet(dst='33:33:ff:00:00:04',ethertype=33024,src='00:00:00:00:00:03'), vlan(cfi=0,ethertype=34525,pcp=0,vid=110), ipv6(dst='ff02::1:ff00:4',ext_hdrs=[],flow_label=0,hop_limit=255,nxt=58,payload_length=32,src='fe80::200:ff:fe00:3',traffic_class=0,version=6), icmpv6(code=0,csum=31375,data=nd_neighbor(dst='fe80::200:ff:fe00:4',option=nd_option_sla(data=None,hw_src='00:00:00:00:00:03',length=1),res=0),type_=135)
    ...


In this section, you learned how to use the firewall with specific examples.


REST API List
-------------

List of REST API of rest_firewall, which is introduced in this section.


Acquiring Enable/Disable State of All Switches
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

============  ========================
**Method**    GET
**URL**       /firewall/module/status
============  ========================


Changing Enable/Disable State of All Switches
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

============  ================================================
**Method**    PUT
**URL**       /firewall/module/{**op**}/{**switch**}

              --**op**: [ "enable" \| "disable" ]

              --**switch**: [ "all" \| *Switch ID* ]
**Remarks**   Initial state of each switch is "disable"
============  ================================================


Acquiring All Rules
^^^^^^^^^^^^^^^^^^^

============  ==========================================
**Method**    GET
**URL**       /firewall/rules/{**switch**}[/{**vlan**}]

              --**switch**: [ "all" \| *Switch ID* ]

              --**vlan**: [ "all" \| *VLAN ID* ]
**Remarks**   Specification of VLAN ID is optional.
============  ==========================================


Adding Rules
^^^^^^^^^^^^

============  =========================================================
**Method**    POST
**URL**       /firewall/rules/{**switch**}[/{**vlan**}]

              --**switch**: [ "all" \| *Switch ID* ]

              --**vlan**: [ "all" \| *VLAN ID* ]
**Data**      **priority**:[ 0 - 65535 ]

              **in_port**:[ 0 - 65535 ]

              **dl_src**:"<xx:xx:xx:xx:xx:xx>"

              **dl_dst**:"<xx:xx:xx:xx:xx:xx>"

              **dl_type**:[ "ARP" \| "IPv4" \| "IPv6" ]

              **nw_src**:"<xxx.xxx.xxx.xxx/xx>"

              **nw_dst**:"<xxx.xxx.xxx.xxx/xx>"

              **ipv6_src**:"<xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx/xx>"

              **ipv6_dst**:"<xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx/xx>"

              **nw_proto**":[ "TCP" \| "UDP" \| "ICMP" \| "ICMPv6" ]

              **tp_src**:[ 0 - 65535 ]

              **tp_dst**:[ 0 - 65535 ]

              **actions**: [ "ALLOW" \| "DENY" ]
**Remarks**   When it is successfully registered, Rule ID is generated and is noted in the response.

              Specification of VLAN ID is optional.
============  =========================================================


Deleting Rules
^^^^^^^^^^^^^^

============  ==========================================
**Method**    DELETE
**URL**       /firewall/rules/{**switch**}[/{**vlan**}]

              --**switch**: [ "all" \| *Switch ID* ]

              --**vlan**: [ "all" \| *VLAN ID* ]
**Data**      **rule_id**:[ "all" \| 1 - ... ]
**Remarks**   Specification of VLAN ID is optional.
============  ==========================================


Acquiring Log Output State of All Switches
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

============  ====================
**Method**    GET
**URL**       /firewall/log/status
============  ====================


Changing Log Output State of All Switches
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

============  ===============================================
**Method**    PUT
**URL**       /firewall/log/{**op**}/{**switch**}

              --**op**: [ "enable" \| "disable" ]

              --**switch**: [ "all" \| *Switch ID* ]
**Remarks**   Initial state of each switch is "enable"
============  ===============================================
