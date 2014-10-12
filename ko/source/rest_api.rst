.. _ch_rest_api:

REST 연동
=========

이 장에서는 「 :ref:`ch_switching_hub` 」에서 설명한 스위칭 허브에
REST 연동 기능을 추가합니다.


REST API의 기본
---------------

Ryu에는 WSGI에 대응하는 Web 서버의 기능이 있습니다.
이 기능을 이용하여 다른 시스템이나 브라우저 등과 연동할 때 유용한,
REST API를 만들 수 있습니다.

.. NOTE::

    WSGI는 Python에서 Web 응용 프로그램과 Web 서버 연결을 위한
    통합 프레임워크를 의미합니다.


REST API와 함께 스위칭 허브 구현
--------------------------------
「 :ref:`ch_switching_hub` 」에서 설명한 스위칭 허브에 다음 두 REST API를 추가하여 봅시다.

1. MAC 주소 테이블 획득 API

    스위칭 허브가 갖고 있는 MAC 주소 테이블의 내용을 반환합니다.
    MAC 주소와 포트 번호의 쌍(pair)을 JSON 형식으로 반환합니다.

2. MAC 주소 테이블 등록 API

    MAC 주소와 포트 번호의 쌍(pair)을 MAC 주소 테이블에
    등록하고 스위치 플로우 항목에 추가합니다.


그러면 소스 코드를 살펴 봅시다.

.. rst-class:: sourcecode

.. literalinclude:: sources/simple_switch_rest_13.py

simple_switch_rest_13.py에서는 두 클래스를 정의하고 있습니다.

첫째,
HTTP 요청을 받는 URL과 해당 메서드를 정의하는 컨트롤러 ``SimpleSwitchController`` 입니다.

두 번째는 「 :ref:`ch_switching_hub` 」를 확장하고 MAC 주소 테이블 업데이트를
할 수 있도록 한 클래스 ``SimpleSwitchRest13`` 입니다.

``SimpleSwitchRest13`` 는 스위치에 플로우 항목을 추가하기 위해
FeaturesReply 메서드를 오버라이드하고 datapath 개체를
갖고 있습니다.

SimpleSwitchRest13 클래스 구현
------------------------------
.. rst-class:: sourcecode

::

    class SimpleSwitchRest13(simple_switch_13.SimpleSwitch13):

        _CONTEXTS = { 'wsgi': WSGIApplication }
    ...

클래스 변수 ``_CONTEXT`` 에서 Ryu의 WSGI와 호환되는 Web 서버 클래스를 지정합니다. 그러면
``wsgi`` 라는 키에서 WSGI의 Web 서버 인스턴스를 얻을 수 있습니다.

.. rst-class:: sourcecode

::

    def __init__(self, *args, **kwargs):
        super(SimpleSwitchRest13, self).__init__(*args, **kwargs)
        self.switches = {}
        wsgi = kwargs['wsgi']
        wsgi.register(SimpleSwitchController, {simple_switch_instance_name : self})
    ...

생성자는 뒤에서 설명할 컨트롤러 클래스를 등록하기 위하여,
``WSGIApplication`` 의 인스턴스를 얻고 있습니다. 등록은 ``register`` 메서드를 사용합니다.
``register`` 메서드 실행시 컨트롤러의 생성자에서 ``SimpleSwitchRest13`` 클래스의 인스턴스에
액세스할 수 있도록 ``simple_switch_api_app`` 라는 키 이름에서
dictionary 개체를 전달합니다.

.. rst-class:: sourcecode

::

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        super(SimpleSwitchRest13, self).switch_features_handler(ev)
        datapath = ev.msg.datapath
        self.switches[datapath.id] = datapath
        self.mac_to_port.setdefault(datapath.id, {})
    ...

부모 클래스의 ``switch_features_handler`` 을 오버라이딩합니다.
이 메서드는 SwitchFeatures 이벤트가 발생한 시간에
이벤트 객체 ``ev`` 에 포함된 ``datapath`` 개체를 가져온 후,
인스턴스 변수 ``switches`` 에 저장합니다.
또한, 이시기에, MAC 주소 테이블에 초기 값으로 빈 dictionary를 설정합니다.


.. rst-class:: sourcecode

::

    def set_mac_to_port(self, dpid, entry):
        mac_table = self.mac_to_port.setdefault(dpid, {})
        datapath = self.switches.get(dpid)

        entry_port = entry['port']
        entry_mac = entry['mac']

        if datapath is not None:
            parser = datapath.ofproto_parser
            if entry_port not in mac_table.values():

                for mac, port in mac_table.items():

                    # from known device to new device
                    actions = [parser.OFPActionOutput(entry_port)]
                    match = parser.OFPMatch(in_port=port, eth_dst=entry_mac)
                    self.add_flow(datapath, 1, match, actions)

                    # from new device to known device
                    actions = [parser.OFPActionOutput(port)]
                    match = parser.OFPMatch(in_port=entry_port, eth_dst=mac)
                    self.add_flow(datapath, 1, match, actions)

                mac_table.update({entry_mac : entry_port})
        return mac_table
    ...

지정된 스위치에 MAC 주소와 포트를 등록하는 메서드입니다.
REST API가 PUT 방식으로 호출될 때 실행됩니다.

인수 ``entry`` 에는 등록을 하려는 MAC 주소와 연결 포트 쌍(pair)이 포함되어 있습니다.

MAC 주소 테이블 ``self.mac_to_port`` 의 정보를 참조하여
스위치에 등록하는 플로우 항목을 찾아갑니다.

예를 들어, MAC 주소 테이블에 다음의 MAC 주소와 연결 포트 쌍(pair)이 등록되어 있고,

* 00:00:00:00:00:01, 1

인수 ``entry`` 에 전달 된 MAC 주소와 포트 쌍(pair)이

* 00:00:00:00:00:02, 2

일 때, 해당 스위치에 등록해야 하는 플로우 항목은 다음과 같습니다.

* 매칭 조건 : in_port = 1, dst_mac = 00:00:00:00:00:02 조치 : output = 2
* 매칭 조건 : in_port = 2, dst_mac = 00:00:00:00:00:01 조치 : output = 1

플로우 항목의 등록은 부모 클래스의 ``add_flow`` 메서드를 사용하고 있습니다. 마지막으로,
인수 ``entry`` 에서 전달된 정보를 MAC 주소 테이블에 저장합니다.


SimpleSwitchController 클래스 구현
----------------------------------
다음은 REST API에 대한 HTTP 요청을 수락하는 컨트롤러 클래스입니다.
클래스 이름은 ``SimpleSwitchController`` 입니다.

.. rst-class:: sourcecode

::

    class SimpleSwitchController(ControllerBase):
        def __init__(self, req, link, data, **config):
            super(SimpleSwitchController, self).__init__(req, link, data, **config)
            self.simpl_switch_spp = data[simple_switch_instance_name]
    ...

생성자에서 ``SimpleSwitchRest13`` 클래스의 인스턴스를 가져옵니다.

.. rst-class:: sourcecode

::

    @route('simpleswitch', url, methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def list_mac_table(self, req, **kwargs):

        simple_switch = self.simpl_switch_spp
        dpid = dpid_lib.str_to_dpid(kwargs['dpid'])

        if dpid not in simple_switch.mac_to_port:
            return Response(status=404)

        mac_table = simple_switch.mac_to_port.get(dpid, {})
        body = json.dumps(mac_table)
        return Response(content_type='application/json', body=body)
    ...

REST API URL과 해당 프로세스를 구현하는 부분입니다. 이 방법과 URL과의 바인딩이
Ryu에서 정의 된 ``route`` 데코레이터를 사용하고 있습니다.

데코레이터로 지정하는 내용은 다음과 같습니다.

* 첫 번째 인수

    이름

* 두 번째 인수

    URL을 지정합니다.
    URL이 http://<서버 IP>:8080/simpleswitch/mactable/<데이터 경로ID>
    가 되도록 합니다.

* 세 번째 인수

    HTTP 메서드를 지정합니다.
    GET 메서드를 지정합니다.

* 네 번째 인수

    지정 위치의 형식을 지정합니다.
    URL(/simpleswitch/mactable/{dpid})의 {dpid} 부분이
    ryu/lib/dpid.py의 ``DPID_PATTERN`` 에서 정의된 16 자리로 된 16 진수로 되어야 합니다.

두 번째 인수로 지정된 URL에서 REST API가 불려 그 때의 HTTP 방식이 GET 인 경우
``list_mac_table`` 메서드를 호출합니다.
이 메서드는, {dpid} 부분에서 지정된 데이터 경로 ID에 해당하는 MAC 주소 테이블을 검색하고
JSON으로 변환되어 호출자에게 반환합니다.

또한, Ryu에 연결되지 않은, 정보가 없는 스위치의 데이터 경로 ID를 지정하면 응답 코드 404를 반환합니다.

.. rst-class:: sourcecode

::

    @route('simpleswitch', url, methods=['PUT'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def put_mac_table(self, req, **kwargs):

        simple_switch = self.simpl_switch_spp
        dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
        new_entry = eval(req.body)

        if dpid not in simple_switch.mac_to_port:
            return Response(status=404)

        try:
            mac_table = simple_switch.set_mac_to_port(dpid, new_entry)
            body = json.dumps(mac_table)
            return Response(content_type='application/json', body=body)
        except Exception as e:
            return Response(status=500)
    ...

다음은 MAC 주소 테이블을 등록하는 REST API입니다.

URL은 MAC 주소 테이블 취득시의 API와 동일하지만 HTTP 메서드가 PUT의 경우
``put_mac_table`` 메서드를 호출합니다.
이 메서드는 내부적으로 스위칭 허브 인스턴스의 ``set_mac_to_port`` 메서드를 호출합니다.
또한 ``put_mac_table`` 메서드 내에서 예외가 발생하면 응답 코드 500을 반환합니다.
또한 ``list_mac_table`` 메서드뿐만 아니라 Ryu에 연결하지 않은 미지의 스위치의 데이터 경로 ID를 지정하면
응답 코드 404을 반환합니다.

REST API 추가된 스위칭 허브 실행
--------------------------------
REST API를 추가한 스위칭 허브를 실행해 봅시다.

먼저 「 :ref:`ch_switching_hub` 」와 같이 Mininet을 실행합니다. 여기서도
스위치 OpenFlow 버전에 OpenFlow13을 설정하는 것을 잊지 마십시오.
이어 REST API를 추가한 스위칭 허브를 시작합니다.

.. rst-class:: console

::

    ryu@ryu-vm:~/ryu/ryu/app$ cd ~/ryu/ryu/app
    ryu@ryu-vm:~/ryu/ryu/app$ sudo ovs-vsctl set Bridge s1 protocols=OpenFlow13
    ryu@ryu-vm:~/ryu/ryu/app$ ryu-manager --verbose ./simple_switch_rest_13.py
    loading app ./simple_switch_rest_13.py
    loading app ryu.controller.ofp_handler
    creating context wsgi
    instantiating app ryu.controller.ofp_handler
    instantiating app ./simple_switch_rest_13.py
    BRICK SimpleSwitchRest13
      CONSUMES EventOFPPacketIn
      CONSUMES EventOFPSwitchFeatures
    BRICK ofp_event
      PROVIDES EventOFPPacketIn TO {'SimpleSwitchRest13': set(['main'])}
      PROVIDES EventOFPSwitchFeatures TO {'SimpleSwitchRest13': set(['config'])}
      CONSUMES EventOFPErrorMsg
      CONSUMES EventOFPPortDescStatsReply
      CONSUMES EventOFPEchoRequest
      CONSUMES EventOFPSwitchFeatures
      CONSUMES EventOFPHello
    (31135) wsgi starting up on http://0.0.0.0:8080/
    connected socket:<eventlet.greenio.GreenSocket object at 0x318c6d0> address:('127.0.0.1', 48914)
    hello ev <ryu.controller.ofp_event.EventOFPHello object at 0x318cc10>
    move onto config mode
    EVENT ofp_event->SimpleSwitchRest13 EventOFPSwitchFeatures
    switch features ev version: 0x4 msg_type 0x6 xid 0x78dd7a72 OFPSwitchFeatures(auxiliary_id=0,capabilities=71,datapath_id=1,n_buffers=256,n_tables=254)
    move onto main mode

시작 부분 메시지에 "(31135) wsgi starting up on http://0.0.0.0:8080/"줄이 있는데,
이는 Web 서버가 포트 번호 8080으로 시작되었음을 나타냅니다.

다음 mininet shell에서 h1에서 h2로 ping을 실행합니다.

.. rst-class:: console

::

    mininet> h1 ping -c 1 h2
    PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
    64 bytes from 10.0.0.2: icmp_req=1 ttl=64 time=84.1 ms

    --- 10.0.0.2 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 84.171/84.171/84.171/0.000 ms


이때 Ryu의 Packet-In은 3번 발생하고 있습니다.

.. rst-class:: console

::

    EVENT ofp_event->SimpleSwitchRest13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 ff:ff:ff:ff:ff:ff 1
    EVENT ofp_event->SimpleSwitchRest13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:02 00:00:00:00:00:01 2
    EVENT ofp_event->SimpleSwitchRest13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 00:00:00:00:00:02 1

여기서, 스위칭 허브의 MAC 테이블을 검색하는 REST API를 실행해 봅시다.
이번에는 REST API를 호출하기 위해 curl 명령을 사용합니다.

.. rst-class:: console

::

    ryu@ryu-vm:~$ curl -X GET http://127.0.0.1:8080/simpleswitch/mactable/0000000000000001
    {"00:00:00:00:00:02": 2, "00:00:00:00:00:01": 1}

h1과 h2 두 호스트가 MAC 주소 테이블에서 학습된 것을 알 수 있습니다.

이번에는 h1, h2의 두 호스트를 미리 MAC 주소 테이블에 저장하고
ping을 실행해 봅니다. 먼저 스위칭 허브와 Mininet을 중지합니다.
그 다음 다시 Mininet를 시작하고 OpenFlow 버전을 OpenFlow13로 설정 후
스위칭 허브를 시작합니다.

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

이후, MAC 주소 테이블 업데이트를 위한 REST API를 각 호스트마다 호출합니다.
REST API를 호출할 때 데이터 형식은 { "mac": "MAC 주소", "port": 연결 포트 번호}가 되도록 합니다.

.. rst-class:: console

::

    ryu@ryu-vm:~$ curl -X PUT -d '{"mac" : "00:00:00:00:00:01", "port" : 1}' http://127.0.0.1:8080/simpleswitch/mactable/0000000000000001
    {"00:00:00:00:00:01": 1}
    ryu@ryu-vm:~$ curl -X PUT -d '{"mac" : "00:00:00:00:00:02", "port" : 2}' http://127.0.0.1:8080/simpleswitch/mactable/0000000000000001
    {"00:00:00:00:00:02": 2, "00:00:00:00:00:01": 1}

이 명령을 실행하면 h1, h2에 대응하는 플로우 항목이 스위치에 등록됩니다.

이어 h1에서 h2로 ping을 실행합니다.

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

이때 스위치에는 이미 플로우 항목이 존재하기 때문에 Packet-In은 h1에서 h2로 ARP 요청이 있을 
때만 발생하고, 이후의 패킷 교환에서는 발생하지 않습니다.

정리
----

이 장에서는 MAC 주소 테이블을 참조하거나 업데이트하는 기능을 중심으로
REST API를 추가하는 방법에 대해 설명했습니다. 또 하나의 실용적인 응용으로, 스위치에 원하는 플로우 항목을 추가하는 것과 
같이 REST API를 만들고 브라우저에서 사용할 수 있도록 하는 것도 좋을 것입니다.

