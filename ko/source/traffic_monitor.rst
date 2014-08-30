.. _ch_traffic_monitor:

트래픽 모니터
=============

이 장에서는 「 :ref:`ch_switching_hub` 」에서 다루었던 스위칭 허브에 OpenFlow 스위치
통계 정보를 모니터링하는 기능을 추가하는 법에 대해 살펴봅니다.


네트워크 정기 검사
------------------

네트워크는 이미 많은 서비스 및 비즈니스 인프라가 있기 때문에 정상 상태 및 
안정적인 가동이 유지되기를 요구합니다. 그러나, 항상 뭔가 문제
가 발생합니다.

네트워크에 이상이 발생했을 경우, 신속하게 원인을 파악하고 복구시켜야 됩니다.
말할 것도 없이, 이상을 감지하고 원인을 파악하기 위해서는 
평소부터 네트워크의 상태를 잘 이해할 필요가 있습니다. 
예를 들어, 네트워크 장비 내 포트에서 트래픽 양이 매우 높은 값을
보여주는 경우, 그것이 비정상적인 상태인지 정상 상태인지, 또는 언제부터
이렇게 되었는가하는 것은, 지속적으로 해당 포트의 트래픽 양을 측정하지 않으면 
판단할 수 없습니다.

그래서, 네트워크의 건강 상태를 지속적으로 모니터링하고 계속하는 것은, 해당 
네트워크를 사용하는 서비스와 업무의 지속적인 안정적 운용을 위해서도 필수입니다.
물론, 트래픽 정보를 단순히 모니터링한다고 해서 완벽한 보장을 하지는 않습니다. 
하지만, 이 장에서는 OpenFlow를 사용해 스위치의 통계 정보를 얻는 방법에 대해 설명하고자 합니다.


트래픽 모니터 구현
------------------

다음은 「 :ref:`ch_switching_hub` 」에서 설명한 스위칭 허브에 트래픽 모니터 기능을 추가한 소스 코드입니다.

.. rst-class:: sourcecode

.. literalinclude:: sources/simple_monitor.py

SimpleSwitch13을 상속하는 SimpleMonitor 클래스에 트래픽 모니터링 기능을
구현하고 있기 때문에, 여기에는 패킷 전송에 대한 처리 부분이 없습니다.


고정 주기 처리
^^^^^^^^^^^^^^

스위칭 허브의 처리와 병행하여 주기적으로 통계 정보를 얻기 위해 OpenFlow
스위치에 요청하는 스레드를 생성합니다. 

.. rst-class:: sourcecode

::

    from operator import attrgetter
    
    from ryu.app import simple_switch_13
    from ryu.controller import ofp_event
    from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
    from ryu.controller.handler import set_ev_cls
    from ryu.lib import hub


    class SimpleMonitor(simple_switch_13.SimpleSwitch13):

        def __init__(self, *args, **kwargs):
            super(SimpleMonitor, self).__init__(*args, **kwargs)
            self.datapaths = {}
            self.monitor_thread = hub.spawn(self._monitor)
    # ...

``ryu.lib.hub`` 에는 몇 가지 eventlet wrapper와 기본 클래스 구현이 
있습니다. 여기에서는 스레드를 생성하는 ``hub.spawn ()`` 을 사용합니다.
실제로 생성되는 스레드는 eventlet green thread입니다. 

.. rst-class:: sourcecode

::

    # ...
    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)
    # ...

스레드 함수 ``_monitor ()`` 에서 등록된 스위치에 대한 통계 가져오기 
요청을 10 초 간격으로 무한 반복합니다.

연결된 스위치를 모니터링하기 때문에 스위치의 접속 및 접속 끊김에 대한 
``EventOFPStateChange`` 이벤트를 이용하고 있습니다. 이 이벤트는 Ryu 프레임
워크가 발행하는 것으로, Datapath의 상태가 바뀌었을 때에 발행됩니다.

여기에서는 Datapath 상태가 ``MAIN_DISPATCHER`` 가 될 때, 해당 스위치는 
모니터링 대상으로 등록되고, ``DEAD_DISPATCHER`` 가 될 때, 등록이 삭제됩니다. 

.. rst-class:: sourcecode

::

    # ...
    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)
    # ...

주기적으로 호출되는 ``_request_stats ()`` 는 스위치에
``OFPFlowStatsRequest`` 와 ``OFPPortStatsRequest`` 를 발행하고 있습니다.

``OFPFlowStatsRequest`` 는 플로우 항목에 대한 통계를 스위치에 요청합니다.
테이블 ID, 출력 포트, cookie 값, 매치 등의 상태를 통해 요청 대상 플로우 항목
을 좁힐 수 있지만, 여기에서는 모든 플로우 항목을 대상으로 하고 있습니다.

``OFPPortStatsRequest`` 는 포트 관련 통계 정보를 스위치에 요청합니다.
원하는 포트 번호를 정보 수집을 위해 지정할 수 있습니다. 여기에서는 ``OFPP_ANY`` 를 지정하여 
모든 포트의 통계 정보를 요청하고 있습니다. 


FlowStats
^^^^^^^^^
스위치로부터 응답을 받기 위해 FlowStatsReply 메시지를 수신하는 이벤트 처리기를 생성합니다. 

.. rst-class:: sourcecode

::

    # ...
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body

        self.logger.info('datapath         '
                         'in-port  eth-dst           '
                         'out-port packets  bytes')
        self.logger.info('---------------- '
                         '-------- ----------------- '
                         '-------- -------- --------')
        for stat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match['in_port'],
                                             flow.match['eth_dst'])):
            self.logger.info('%016x %8x %17s %8x %8d %8d',
                             ev.msg.datapath.id,
                             stat.match['in_port'], stat.match['eth_dst'],
                             stat.instructions[0].actions[0].port,
                             stat.packet_count, stat.byte_count)
    # ...

``OPFFlowStatsReply`` 클래스의 속성인 ``body`` 는 ``OFPFlowStats`` 목록에서
FlowStatsRequest의 대상이 된 각 플로우 항목의 통계 정보가 포함되어 있습니다.

우선 순위가 0 인 Table-miss 플로우를 제외하고 모든 플로우 항목
을 선택합니다. 수신 포트와 대상 MAC 주소로 정렬하여 각각의 플로우 항목과 
매치되는 패킷과 바이트를 출력합니다.

또한, 여기에서는 일부 숫자들만 로그에 출력되고 있지만, 지속적으로 정보
를 수집하고 분석하려면 외부 프로그램과의 연계가 필요할 것입니다. 그런
경우 ``OFPFlowStatsReply`` 의 내용을 JSON 형식으로 변환할 수 있습니다.

예를 들어 다음과 같이 쓸 수 있습니다. 

.. rst-class:: sourcecode

::

    import json

    # ...

    self.logger.info('%s', json.dumps(ev.msg.to_jsondict(), ensure_ascii=True,
                                      indent=3, sort_keys=True))

이 경우 다음과 같이 출력됩니다. 

.. rst-class:: console

::

    {
       "OFPFlowStatsReply": {
          "body": [
             {
                "OFPFlowStats": {
                   "byte_count": 0, 
                   "cookie": 0, 
                   "duration_nsec": 680000000, 
                   "duration_sec": 4, 
                   "flags": 0, 
                   "hard_timeout": 0, 
                   "idle_timeout": 0, 
                   "instructions": [
                      {
                         "OFPInstructionActions": {
                            "actions": [
                               {
                                  "OFPActionOutput": {
                                     "len": 16, 
                                     "max_len": 65535, 
                                     "port": 4294967293, 
                                     "type": 0
                                  }
                               }
                            ], 
                            "len": 24, 
                            "type": 4
                         }
                      }
                   ], 
                   "length": 80, 
                   "match": {
                      "OFPMatch": {
                         "length": 4, 
                         "oxm_fields": [], 
                         "type": 1
                      }
                   }, 
                   "packet_count": 0, 
                   "priority": 0, 
                   "table_id": 0
                }
             }, 
             {
                "OFPFlowStats": {
                   "byte_count": 42, 
                   "cookie": 0, 
                   "duration_nsec": 72000000, 
                   "duration_sec": 57, 
                   "flags": 0, 
                   "hard_timeout": 0, 
                   "idle_timeout": 0, 
                   "instructions": [
                      {
                         "OFPInstructionActions": {
                            "actions": [
                               {
                                  "OFPActionOutput": {
                                     "len": 16, 
                                     "max_len": 65509, 
                                     "port": 1, 
                                     "type": 0
                                  }
                               }
                            ], 
                            "len": 24, 
                            "type": 4
                         }
                      }
                   ], 
                   "length": 96, 
                   "match": {
                      "OFPMatch": {
                         "length": 22, 
                         "oxm_fields": [
                            {
                               "OXMTlv": {
                                  "field": "in_port", 
                                  "mask": null, 
                                  "value": 2
                               }
                            }, 
                            {
                               "OXMTlv": {
                                  "field": "eth_dst", 
                                  "mask": null, 
                                  "value": "00:00:00:00:00:01"
                               }
                            }
                         ], 
                         "type": 1
                      }
                   }, 
                   "packet_count": 1, 
                   "priority": 1, 
                   "table_id": 0
                }
             }
          ], 
          "flags": 0, 
          "type": 1
       }
    }


PortStats
^^^^^^^^^

스위치로부터 응답을 받기 위해 PortStatsReply 메시지를 수신하는 이벤트 처리기를 생성합니다. 

.. rst-class:: sourcecode

::

    # ...
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body

        self.logger.info('datapath         port     '
                         'rx-pkts  rx-bytes rx-error '
                         'tx-pkts  tx-bytes tx-error')
        self.logger.info('---------------- -------- '
                         '-------- -------- -------- '
                         '-------- -------- --------')
        for stat in sorted(body, key=attrgetter('port_no')):
            self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d', 
                             ev.msg.datapath.id, stat.port_no,
                             stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                             stat.tx_packets, stat.tx_bytes, stat.tx_errors)

``OPFPortStatsReply`` 클래스의 속성 ``body`` 은 ``OFPPortStats`` 의 목록에 
있습니다. 

``OFPPortStats`` 에는 포트 번호, 송수신 각각의 패킷 수, 바이트 수, 드롭 
개수, 오류 개수, 프레임 오류 개수, 오버런 개수, CRC 오류 개수, 충돌 개수 등
통계 정보가 저장됩니다.

여기에서는 포트 번호별로 정렬하고 수신 패킷 개수, 수신된 바이트 수신 오류 개수,
전송 패킷 수, 송신 바이트 수, 전송 오류 개수를 출력합니다. 


트래픽 모니터 실행
------------------

그럼 실제로 이 트래픽 모니터를 실행 해 봅시다.

먼저 「 :ref:`ch_switching_hub` 」와 같이 Mininet을 실행합니다. 여기서
스위치 OpenFlow 버전에 OpenFlow13을 설정하는 것을 잊지 마십시오.

다음, 이제, 트래픽 모니터를 실행합니다. 

controller: c0:

.. rst-class:: console

::

    ryu@ryu-vm:~# ryu-manager --verbose ./simple_monitor.py
    loading app ./simple_monitor.py
    loading app ryu.controller.ofp_handler
    instantiating app ./simple_monitor.py
    instantiating app ryu.controller.ofp_handler
    BRICK SimpleMonitor
      CONSUMES EventOFPStateChange
      CONSUMES EventOFPFlowStatsReply
      CONSUMES EventOFPPortStatsReply
      CONSUMES EventOFPPacketIn
      CONSUMES EventOFPSwitchFeatures
    BRICK ofp_event
      PROVIDES EventOFPStateChange TO {'SimpleMonitor': set(['main', 'dead'])}
      PROVIDES EventOFPFlowStatsReply TO {'SimpleMonitor': set(['main'])}
      PROVIDES EventOFPPortStatsReply TO {'SimpleMonitor': set(['main'])}
      PROVIDES EventOFPPacketIn TO {'SimpleMonitor': set(['main'])}
      PROVIDES EventOFPSwitchFeatures TO {'SimpleMonitor': set(['config'])}
      CONSUMES EventOFPErrorMsg
      CONSUMES EventOFPPortDescStatsReply
      CONSUMES EventOFPHello
      CONSUMES EventOFPEchoRequest
      CONSUMES EventOFPSwitchFeatures
    connected socket:<eventlet.greenio.GreenSocket object at 0x343fb10> address:('127.0.0.1', 55598)
    hello ev <ryu.controller.ofp_event.EventOFPHello object at 0x343fed0>
    move onto config mode
    EVENT ofp_event->SimpleMonitor EventOFPSwitchFeatures
    switch features ev version: 0x4 msg_type 0x6 xid 0x7dd2dc58 OFPSwitchFeatures(auxiliary_id=0,capabilities=71,datapath_id=1,n_buffers=256,n_tables=254)
    move onto main mode
    EVENT ofp_event->SimpleMonitor EventOFPStateChange
    register datapath: 0000000000000001
    send stats request: 0000000000000001
    EVENT ofp_event->SimpleMonitor EventOFPFlowStatsReply
    datapath         in-port  eth-dst           out-port packets  bytes
    ---------------- -------- ----------------- -------- -------- --------
    EVENT ofp_event->SimpleMonitor EventOFPPortStatsReply
    datapath         port     rx-pkts  rx-bytes rx-error tx-pkts  tx-bytes tx-error
    ---------------- -------- -------- -------- -------- -------- -------- --------
    0000000000000001        1        0        0        0        0        0        0
    0000000000000001        2        0        0        0        0        0        0
    0000000000000001        3        0        0        0        0        0        0
    0000000000000001 fffffffe        0        0        0        0        0        0

「 :ref:`ch_switching_hub` 」에서는 ryu-manager 명령
에 SimpleSwitch13 모듈 이름 (ryu.app.simple_switch_13)을 지정했지만,
여기에서는 SimpleMonitor의 파일 이름 (./simple_monitor.py)을 지정합니다.

여기서는, 플로우 항목이 없고, (Table-miss 플로우 항목은 표시되지 않습니다)
각 포트의 개수도 모두 0입니다.

호스트 1에서 호스트 2로 ping을 실행하자. 

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# ping -c1 10.0.0.2
    PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
    64 bytes from 10.0.0.2: icmp_req=1 ttl=64 time=94.4 ms

    --- 10.0.0.2 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 94.489/94.489/94.489/0.000 ms
    root@ryu-vm:~# 

패킷 전송 및 플로우 항목이 등록되고 통계 정보가 
변경됩니다. 

controller: c0:

.. rst-class:: console

::

    datapath         in-port  eth-dst           out-port packets  bytes
    ---------------- -------- ----------------- -------- -------- --------
    0000000000000001        1 00:00:00:00:00:02        2        1       42
    0000000000000001        2 00:00:00:00:00:01        1        2      140
    datapath         port     rx-pkts  rx-bytes rx-error tx-pkts  tx-bytes tx-error
    ---------------- -------- -------- -------- -------- -------- -------- --------
    0000000000000001        1        3      182        0        3      182        0
    0000000000000001        2        3      182        0        3      182        0
    0000000000000001        3        0        0        0        1       42        0
    0000000000000001 fffffffe        0        0        0        1       42        0

플로우 항목의 통계 정보에 따르면, 수신 포트 1의 플로우에 매치된 트래픽
은 1 패킷, 42 바이트라고 기록되어 있습니다. 수신 포트 2에서는 2 패킷, 140
바이트로 기록되어 있습니다.

포트 통계 정보에 따르면, 포트 1의 수신 패킷 수 (rx-pkts)는 3, 수신 바이트 수
(rx-bytes)는 182 바이트, 포트 2는 3 패킷, 182 바이트라고 되어 있습니다.

플로우 항목의 통계 정보와 해당 포트의 통계 화면이 일치하지는 않습니다. 이유는 
플로우 항목의 통계 정보가 해당 항목에 매치되고 전송된 패킷 정보이기 때문입니다. 
즉, Table-miss에 의해 Packet-In을 발행되어 Packet-Out으로 전송된 
패킷은 해당 통계의 대상에 포함되지 않기 때문입니다.

이 경우, 호스트 1이 먼저 브로드 캐스트한 ARP 요청, 호스트 2가 호스트 1에 
반환하는 ARP 응답, 그리고 호스트 1에서 호스트 2로 발행하는 echo 요청인 
3개의 패킷이 있고, (모두) Packet-Out 의해 전송됩니다.
이러한 이유로, 포트 통계치는 플로우 항목의 통계치보다 많습니다.


정리
----

이 장에서는 통계 정보 수집 기능을 주제로 하여, 다음 항목들을
설명하였습니다.

* Ryu 응용 프로그램에서의 스레드 생성 방법
* Datapath의 상태 변화 확인
* FlowStats 및 PortStats 수집 방법

