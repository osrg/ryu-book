.. _ch_introduction_example:

Introduction example
====================

This section shows examples of services and products that use Ryu.

Stratosphere SDN Platform (Stratosphere)
----------------------------------------

The Stratosphere SDN Platform (hereinafter abbreviated as SSP) is a software product developed by Stratosphere. Using SSP, you can construct a virtual network with an Edge Overlay-model using tunneling protocols such as VXLAN, STT, and MPLS.

Each tunneling protocol is converted to and from VLAN. Since the identifier of each tunneled protocol is larger than the 12 bits of VLAN, many more L2 segments can be managed than directly using VLAN. Also SSP can be used in conjunction with software such as OpenStack, CloudStack and IaaS.

SSP uses OpenFlow to implement functions and is adopting Ryu as the controller in version 1.1.4. One of the reasons for this is to support OpenFlow1.1 and later. Upon supporting MPLS to SSP, introduction of a framework that supports OpenFlow1.1 is being considered since it has support at the protocol level.

.. NOTE::
    Apart from support for the OpenFlow protocol itself, for items for which implementation is optional, it is also necessary to consider sufficient support of the OpenFlow switch side being used.

The fact that Python can be used as a development language is also a factor. Python is actively used in the development of Stratosphere, and many parts of SSP are written in Python as well. The outstanding descriptive power of Python and the fact that work can be performed using a familiar language results in improved development efficiency.

Software consists of multiple Ryu applications and interacts with other components of SSP through the REST API. The ability to divide software into multiple applications at the functional level is essential to maintaining good source code.



SmartSDN Controller (NTT COMWARE)
---------------------------------

SmartSDN Controller is an SDN controller that provides centralized control functions of the network (network virtualization, optimization, etc.) to replace conventional autonomous distributed control.

.. only:: latex

    .. image:: images/introduction_example/fig1.png
        :align: center

.. only:: epub

    .. image:: images/introduction_example/fig1.png
        :align: center

.. only:: not latex and not epub

    .. image:: images/introduction_example/fig1.png
        :scale: 70 %
        :align: center


SmartSDN Controller has the following two characteristics:

1. Flexible network routing by virtual networks

    By building multiple virtual networks on the same physical network, a flexible environment is provided to the network for requests from users, enabling reduced equipment cost through effective utilization of facilities. Also, by centrally managing the switches and routers in which information is individually referred and set, the entire network can be understood, allowing flexible route changes depending on the traffic situation and network failures.

    It focuses on Quality of Experience (QoE) of the user, and by determining QoE of network communication that is flowing (such as bandwidth, delay, loss, and fluctuation) and bypassing to a better path, stable maintenance of service quality is achieved.


2. Ensure network reliability with a high degree of maintenance and operation functionality

    It has a redundant configuration in order to continue service even in the event of controller failure. Also, by creating artificial communication packets that flow between sites and sending them on the path, early detection of failure on the path is provided, which cannot be detected by standard monitoring functions specified by the OpenFlow specification, allowing various tests (communication confirmation, route confirmation, etc.) to be performed.

    Furthermore, network design and network state confirmation is visualized using a GUI, allowing operation that does not depend on the skill level of maintenance personnel, which can reduce network operating costs.

In the development of SmartSDN Controller, it was necessary to select an OpenFlow framework that meets the following conditions.

* Framework that can comprehensively support the OpenFlow specification.
* Framework that allows updates relatively quickly because it is planning to follow updates to OpenFlow.

Within the above, Ryu had the following characteristics.

* Comprehensive support for functions in each version of OpenFlow. 
* Quick compliance for updating of OpenFlow. The development community is also active and responds quickly to bugs.
* Substantial amounts of sample code and documentation.

Therefore, Ryu was deemed appropriate as a framework and has been adopted.
