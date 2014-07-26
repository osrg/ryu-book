.. _ch_switching_hub:

스위칭 허브
===========

이 장에서는 간단한 스위칭 허브 구현을 소재로 Ryu하여 응용 프로그램 
구현 방법을 설명하고 있습니다. 

스위칭 허브
----------------

세상에는 다양한 기능을 가진 스위칭 허브가 있습니다만, 여기에서는
다음과 같은 간단한 기능을 가진 스위칭 허브의 구현을 보고 있습니다.

* 포트에 연결되어있는 호스트의 MAC 주소를 학습하고 MAC 주소 테이블
  을 유지하기
* 학습된 호스트에게 패킷을 수신하면 호스트 연결되는 포트로 전송
* 알 수없는 호스트에게 패킷을 수신하면, Flooding

이러한 스위치를 Ryu를 사용하여 구현해 봅시다.


OpenFlow 의한 스위칭 허브 
-------------------------

OpenFlow 스위치는 Ryu 같은 OpenFlow 컨트롤러의 지시를 받고,
다음과 같은 것을 할 수 있습니다.

* 수신 된 패킷의 주소를 다시하거나 지정된 포트에서 전송
* 받은 패킷을 컨트롤러에 전송 (Packet-In)
* 컨트롤러에서 전송 된 패킷을 특정 포트에서 전송 (Packet-Out)

이러한 기능을 조합 스위칭 허브를 실현 할 수 있습니다.

우선, Packet-In 기능을 이용한 MAC 주소 학습입니다.
컨트롤러는 Packet-In 기능을 이용하여 스위치에서 패킷을 받을 수가 있습니다.
받은 패킷을 분석하고 호스트의 MAC 주소와 연결되어있다
포트 정보를 학습 할 수 있습니다.

학습 후에는받은 패킷의 전송입니다.
패킷의 목적지 MAC 주소가 학습 된 호스트의 것을 찾습니다.
검색 결과는 다음 작업을 수행합니다.

* 학습된 호스트의 경우 ... Packet-Out 기능으로 연결할 포트에서 패킷을 전송
* 알 수 없는 호스트의 경우 ... Packet-Out 기능으로 패킷을 플러딩

이러한 동작을 단계별로 그림과 함께 설명합니다. 


1. 초기 상태

     흐름 테이블이 비어 초기 상태입니다.

     포트 1에 호스트 A, 포트 4에 호스트 B 포트 3 호스트 C가 연결되어있는 것
     합니다. 

    .. only:: latex

       .. image:: images/switching_hub/fig1.eps
          :scale: 80 %
          :align: center

    .. only:: not latex

       .. image:: images/switching_hub/fig1.png
          :align: center


2. 호스트 A → 호스트 B

     호스트 A에서 호스트 B로 패킷이 전송되면 Packet-In 메시지가 보내져
     호스트 A의 MAC 주소를 포트 1에 학습됩니다. 호스트 B의 포트는 아직 알고
     없기 때문에 패킷은 홍수 패킷은 호스트 B와 호스트 C에서 수신
     됩니다. 

    .. only:: latex

       .. image:: images/switching_hub/fig2.eps
          :scale: 80 %
          :align: center

    .. only:: not latex

       .. image:: images/switching_hub/fig2.png
          :align: center

    Packet-In::

        in-port: 1
        eth-dst: 호스트B
        eth-src: 호스트A

    Packet-Out::

        action: OUTPUT:Flooding


3. 호스트B→호스트A

     호스트 B에서 호스트 A로 패킷이 반환되면 흐름 테이블에 항목을 추가하고
     또한 패킷은 포트 1에 전송됩니다. 따라서이 패킷은 호스트 C는
     수신되지 않습니다. 

    .. only:: latex

       .. image:: images/switching_hub/fig3.eps
          :scale: 80 %
          :align: center

    .. only:: not latex

       .. image:: images/switching_hub/fig3.png
          :align: center


    Packet-In::

        in-port: 4
        eth-dst: 호스트A
        eth-src: 호스트B

    Packet-Out::

        action: OUTPUT:포트1


4. 호스트A→호스트B

     또한, 호스트 A에서 호스트 B로 패킷이 전송되면 흐름 테이블에
     항목을 추가하고 또한 패킷은 포트 4에 전송됩니다. 

    .. only:: latex

       .. image:: images/switching_hub/fig4.eps
          :scale: 80 %
          :align: center

    .. only:: not latex

       .. image:: images/switching_hub/fig4.png
          :align: center


    Packet-In::

        in-port: 1
        eth-dst: 호스트B
        eth-src: 호스트A

    Packet-Out::

        action: OUTPUT:호스트4


이제 실제로 Ryu를 사용하여 구현된 스위칭 허브 소스 코드를 살펴 보겠습니다. 


Ryu에 의한 스위칭 허브 구현 
---------------------------

스위칭 허브 소스 코드는 Ryu 소스 트리에 있습니다. 

    ryu/app/simple_switch_13.py

OpenFlow 버전에 따라 그 밖에도 simple_switch.py (OpenFlow 1.0), 
simple_switch_12.py (OpenFlow 1.2)이 있지만, 여기에서는 OpenFlow 1.3에 대응 한
구현을 살펴 보겠습니다. 

짧은 소스 코드이므로 전체를 여기에 게재합니다.

.. rst-class:: sourcecode

.. literalinclude:: sources/simple_switch_13.py


그러면, 각각의 구현 내용 알아 보겠습니다. 


클래스의 정의 및 초기화
^^^^^^^^^^^^^^^^^^^^^^^

Ryu 응용 프로그램으로 구현하기 위해 ryu.base.app_manager.RyuApp을
상속합니다. 또한 OpenFlow 1.3을 사용하기 때문에 ``OFP_VERSIONS``
에 OpenFlow 1.3 버전을 지정합니다. 

또한 MAC 주소 테이블 mac_to_port을 정의합니다.

OpenFlow 프로토콜은 OpenFlow 스위치와 컨트롤러가 통신을 위해
필요한 핸드 셰이크 등의 몇 가지 단계가 정해져 있습니다 만, Ryu의
프레임 워크가 처리주기 위해, Ryu 응용 프로그램은 의식 할 필요는
없습니다. 


.. rst-class:: sourcecode

::

    class SimpleSwitch13(app_manager.RyuApp):
        OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

        def __init__(self, *args, **kwargs):
            super(SimpleSwitch13, self).__init__(*args, **kwargs)
            self.mac_to_port = {}

        # ...


이벤트 처리기 
^^^^^^^^^^^^^

Ryu는 OpenFlow 메시지를 받으면 메시지에 대응하는 이벤트가 발생
합니다. Ryu 응용 프로그램은 수신하려는 메시지에 대응하는 이벤트
처리기를 구현합니다. 

이벤트 처리기는 인수에 이벤트 객체의 함수를 정의하고
``ryu.controller.handler.set_ev_cls`` 장식으로 한정합니다. 

set_ev_cls 인수받는 메시지에 대응하는 이벤트 클래스와 OpenFlow
스위치의 상태를 지정합니다. 

이벤트 클래스 이름은 ``ryu.controller.ofp_event.EventOFP`` + <OpenFlow
메시지 이름>이 있습니다. 예를 들어, Packet-In 메시지의 경우
``EventOFPPacketIn`` 입니다.
자세한 내용은 Ryu 문서`API 참조 <http://ryu.readthedocs.org/en/latest/>`_을 참조하십시오.
상태는 다음 중 하나 또는 목록을 지정합니다. 

.. tabularcolumns:: |l|L|

=========================================== ==================================
정의                                        설명
=========================================== ==================================
ryu.controller.handler.HANDSHAKE_DISPATCHER HELLO 메시지 교환
ryu.controller.handler.CONFIG_DISPATCHER    SwitchFeatures 메시지의 수신
ryu.controller.handler.MAIN_DISPATCHER      표준 상태
ryu.controller.handler.DEAD_DISPATCHER      연결 절단
=========================================== ==================================


Table-miss 흐름 항목 추가
"""""""""""""""""""""""""

OpenFlow 스위치와 핸드 셰이크 완료 후 Table-miss 흐름 항목
흐름 테이블에 추가하고 Packet-In 메시지를 수신 할 준비를합니다.

구체적으로는 Switch Features (Features Reply) 메시지를 수신하고 그래서
Table-miss 흐름 항목을 추가합니다. 

.. rst-class:: sourcecode

::

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # ...

``ev.msg`` 이벤트에 해당하는 OpenFlow 메시지 클래스의 인스턴스가
저장되어 있습니다. 이 경우 
``ryu.ofproto.ofproto_v1_3_parser.OFPSwitchFeatures`` 됩니다.

``msg.datapath`` 이 메시지를 발행 한 OpenFlow 스위치에 해당하는 
``ryu.controller.controller.Datapath`` 클래스의 인스턴스가 포함되어 있습니다. 

Datapath 클래스는 OpenFlow 스위치와의 실제 통신 처리 및 수신 메시지에 대응
이벤트의 발행 등의 중요한 작업을 실시하고 있습니다. 

Ryu 응용 프로그램에서 사용되는 주요 특성은 다음과 같습니다. 

.. tabularcolumns:: |l|L|

============== ==============================================================
속성이름       설명
============== ==============================================================
id             연결된 OpenFlow 스위치 ID (데이터 경로 ID)입니다. 
ofproto        사용하는 OpenFlow 버전에 대응 한 ofproto 모듈을 
               보여줍니다. 현재 다음 중 하나입니다. 

               ``ryu.ofproto.ofproto_v1_0``

               ``ryu.ofproto.ofproto_v1_2``

               ``ryu.ofproto.ofproto_v1_3``

               ``ryu.ofproto.ofproto_v1_4``

ofproto_parser ofproto와 마찬가지로 ofproto_parser 모듈을 보여줍니다. 
               현재 다음 중 하나입니다. 

               ``ryu.ofproto.ofproto_v1_0_parser``

               ``ryu.ofproto.ofproto_v1_2_parser``

               ``ryu.ofproto.ofproto_v1_3_parser``

               ``ryu.ofproto.ofproto_v1_4_parser``
============== ==============================================================

Ryu 응용 프로그램에서 사용할 Datapath 클래스의 주요 메서드는 다음과 같습니다. 

send_msg(msg)

    OpenFlow 메시지를 보냅니다.
    msg는 보낼 OpenFlow 메시지에 대응하는
    ``ryu.ofproto.ofproto_parser.MsgBase`` 의 서브 클래스입니다. 


스위칭 허브는받은 Switch Features 메시지 자체는 특히
사용하지 않습니다. Table-miss 흐름 항목을 추가하는 타이밍을위한
이벤트로 다루고 있습니다. 

.. rst-class:: sourcecode

::

    def switch_features_handler(self, ev):
        # ...

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

Table-miss 흐름 항목은 우선 순위가 최저 (0)에서 모든 패킷에 매치
항목입니다. 이 항목의 지침에 컨트롤러 포트
의 출력 작업을 지정하여 들어오는 패킷이 모든 정상 흐름
항목과 일치하지 않으면, Packet-In을 게시 할 수 있습니다. 

.. NOTE::

    2014 년 1 월 현재 Open vSwitch는 OpenFlow 1.3의 지원이 불완전이며,
    OpenFlow 1.3 이전과 마찬가지로 기본적으로 Packet-In이 발행됩니다. 또한
    Table-miss 흐름 항목도 현재는 미 대응에서 정상 흐름 항목
    로 취급됩니다. 

모든 패킷에 매치시키기 위해 빈 Match을 생성합니다. Match은
``OFPMatch`` 클래스로 표현됩니다. 

그런 다음 컨트롤러 포트에 전송하는 OUTPUT 액션 클래스 (
``OFPActionOutput``)의 인스턴스를 생성합니다.
대상 컨트롤러 전체 패킷을 컨트롤러에 보내 max_len에는
``OFPCML_NO_BUFFER`` 을 지정합니다. 

.. NOTE::

    컨트롤러는 패킷의 시작 부분 (Ethernet 헤더 분)만을 전송
    하고 나머지는 스위치 버퍼시킨 것이 효율성 측면에서 바람직
    하지만 Open vSwitch 버그 (2014 년 1 월 현재)을 해결하기 위해 여기에
    전체 패킷을 전송합니다. 

마지막으로, 우선 순위 0 (가장 낮음)을 지정하여 ``add_flow ()`` 메소드를 실행 Flow Mod
메시지를 보냅니다. add_flow () 메서드의 내용에 대해서는 뒤에서 설명하고자 합니다.




Packet-in 메시지
""""""""""""""""

알 수없는 목적지 들어오는 패킷을 받아들이므로 Packet-In 이벤트 처리기를 만듭니다.

.. rst-class:: sourcecode

::

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # ...


OFPPacketIn 클래스의 자주 사용되는 속성은 다음과 같은 것이 있습니다.

.. tabularcolumns:: |l|L|

========= ===================================================================
속성이름  설명
========= ===================================================================
match     ``ryu.ofproto.ofproto_v1_3_parser.OFPMatch`` 클래스의 인스턴스 
          에서 들어오는 패킷의 메타 정보가 설정되어 있습니다. 
data      수신 패킷 자체를 나타내는 이진 데이터입니다.
total_len 수신 패킷의 데이터 길이입니다. 
buffer_id 수신 패킷이 OpenFlow 스위치에서 버퍼되는 경우 
          ID가 표시됩니다. 버퍼되지 않는 경우 
          ``ryu.ofproto.ofproto_v1_3.OFP_NO_BUFFER`` 가 설정됩니다.
========= ===================================================================


MAC 주소 테이블 업데이트
""""""""""""""""""""""""

.. rst-class:: sourcecode

::

    def _packet_in_handler(self, ev):
        # ...

        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        # ...

OFPPacketIn 클래스의 match에서 수신 포트 (``in_port``)를 가져옵니다.
대상 MAC 주소와 소스 MAC 주소는 Ryu 패킷 라이브러리를 사용하여
수신 패킷의 Ethernet 헤더에서 검색합니다.

가져온 소스 MAC 주소와 수신 포트 번호에서 MAC 주소 테이블을 업데이트합니다.

여러 OpenFlow 스위치와의 연결에 대응하기 위해 MAC 주소 테이블은 OpenFlow
스위치마다 관리하도록되어 있습니다. OpenFlow 스위치를 식별하는 데이터 경로 ID
를 이용하고 있습니다. 


대상 포트 판정
""""""""""""""

대상 MAC 주소를 MAC 주소 테이블에 존재하는 경우 해당 포트 번호를
발견되지 않았던 경우는 플러딩 (``OFPP_FLOOD``)를 출력 포트에 지정된
OUTPUT 액션 클래스의 인스턴스를 생성합니다. 

.. rst-class:: sourcecode

::

    def _packet_in_handler(self, ev):
        # ...

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        # ...


목적지 MAC 주소가 있으면, OpenFlow 스위치의 흐름 테이블에
항목을 추가합니다.

Table-miss 흐름 항목의 추가와 마찬가지로 경기와 액션을 지정하고
add_flow ()를 실행하고 흐름 항목을 추가합니다.

Table-miss 흐름 항목과는 달리 이번에는 경기 조건을 설정합니다.
이번 스위칭 허브의 구현은 수신 포트 (in_port)와 대상 MAC 주소
(eth_dst)을 지정합니다. 예를 들어, "포트 1에서받은 호스트 B에게"패킷
가 대상이됩니다.

이번 흐름 항목은 우선 순위에 1을 지정합니다. 값이 큰
수록 우선 순위가 높아 지므로 여기에 추가하는 흐름 항목은 Table-miss 흐름
항목보다 먼저 평가되게됩니다.

위의 작업을 포함하여 정리하면 다음과 유사한 항목을 플로우 테이블
에 추가합니다. 

    포트 1에서 받은 호스트 B에게 (대상 MAC 주소가 B) 패킷을 
    포트 4에 전송하기

.. HINT::

    OpenFlow는 NORMAL 포트는 논리적 인 출력 포트가 옵션으로 규정
    되고 출력 포트에 NORMAL을 지정하면 스위치의 L2/L3 기능을 사용
    라고 패킷을 처리 할 수 있습니다. 즉, 모든 패킷을 NORMAL
    포트에 출력하도록 지시하는 것만으로, 스위칭 허브 역할을하는
    같이 할 수 있지만, 여기에서는 각각의 처리를 OpenFlow를 사용하여 수행하는 것으로합니다.


흐름 항목의 추가 처리
"""""""""""""""""""""

Packet-In 처리기의 처리가 아직 끝나지 않지만 여기서 일단 흐름 항목
추가 메서드 쪽을 살펴 보겠습니다. 

.. rst-class:: sourcecode

::

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        # ...

흐름 항목에는 대상 패킷의 조건을 나타내는 매치와 패킷
대한 작업을 나타내는 지침 항목의 우선 순위 유효 시간 등을
설정합니다.

스위칭 허브의 구현은 지침에 Apply Actions를 사용하여
지정된 조치를 즉시 적용하도록 설정합니다.

마지막으로, Flow Mod 메시지를 발행하고 흐름 테이블에 항목을 추가합니다. 

.. rst-class:: sourcecode

::

    def add_flow(self, datapath, port, dst, actions):
        # ...

        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

Flow Mod 메시지에 대응하는 클래스는 ``OFPFlowMod`` 클래스입니다. OFPFlowMod
클래스의 인스턴스를 생성하여 Datapath.send_msg () 메서드 OpenFlow
스위치에 메시지를 보냅니다.

OFPFlowMod 클래스의 생성자에는 많은 인수가 있습니다 만, 많은 것은
대부분의 경우 기본값을 그대로하면됩니다. 괄호 안은 기본값입니다. 

datapath

    흐름 테이블을 조작하는 대상 OpenFlow 스위치에 해당하는 Datapath
    클래스의 인스턴스입니다. 일반적으로 Packet-In 메시지 등의 처리기
    에 전달되는 이벤트에서 가져온 것입니다. 

cookie (0)

    컨트롤러가 지정하는 임의의 값으로 항목의 업데이트 또는 삭제할 때
    필터 조건으로 사용할 수 있습니다. 패킷의 처리는 사용되지 않습니다. 

cookie_mask (0)

    항목의 업데이트 또는 삭제의 경우 0이 아닌 값을 지정하면 항목
    cookie 값에 의한 조작 대상 항목의 필터로 사용됩니다. 

table_id (0)

    조작 대상의 흐름 테이블의 테이블 ID를 지정합니다. 

command (ofproto_v1_3.OFPFC_ADD)

    어떤 작업을 할 것인지를 지정합니다. 

    ==================== ========================================
    값                   설명
    ==================== ========================================
    OFPFC_ADD            새로운 흐름 항목을 추가합니다 
    OFPFC_MODIFY         흐름 항목을 업데이트합니다 
    OFPFC_MODIFY_STRICT  엄격하게 일치하는 흐름 항목을 업데이트합니다 
    OFPFC_DELETE         흐름 항목을 삭제합니다 
    OFPFC_DELETE_STRICT  엄격하게 일치하는 흐름 항목을 삭제합니다 
    ==================== ========================================

idle_timeout (0)

    이 항목의 유효 기간을 초 단위로 지정합니다. 항목이 참조되지 않고
    idle_timeout에서 지정된 시간을 초과하면 항목이 제거됩니다.
    항목이 참조 될 때 경과 시간은 리셋됩니다.

    항목이 삭제되면 Flow Removed 메시지가 컨트롤러에 알려
    있습니다. 

hard_timeout (0)

    이 항목의 유효 기간을 초 단위로 지정합니다. idle_timeout과 달리,
    hard_timeout는 항목이 참조 될 수 경과 시간은 리셋되지 않습니다.
    즉, 항목의 참조의 유무에 관계없이 지정된 시간이 경과하면
    항목이 삭제됩니다.

    idle_timeout과 마찬가지로 항목이 삭제되면 Flow Removed 메시지가
    통지됩니다. 

priority (0)

    이 항목의 우선 순위를 지정합니다.
    값이 클수록 우선 순위가 높습니다. 

buffer_id (ofproto_v1_3.OFP_NO_BUFFER)

    OpenFlow 스위치에서 버퍼 된 패킷 버퍼 ID를 지정합니다.
    버퍼 ID는 Packet-In 메시지로 통지 된 것이며, 지정하면
    OFPP_TABLE을 출력 포트에 지정된 Packet-Out 메시지와 Flow Mod 메시지
    두 메시지를 보낸 것처럼 처리됩니다.
    command가 OFPFC_DELETE 또는 OFPFC_DELETE_STRICT의 경우는 무시됩니다.

    버퍼 ID를 지정하지 않으면, ``OFP_NO_BUFFER`` 을 설정합니다. 

out_port (0)

    OFPFC_DELETE 또는 OFPFC_DELETE_STRICT의 경우 대상 항목을
    출력 포트 필터링합니다. OFPFC_ADD, OFPFC_MODIFY, OFPFC_MODIFY_STRICT
    의 경우는 무시됩니다.

    출력 포트의 필터를 해제하려면 ``OFPP_ANY`` 을 지정합니다. 

out_group (0)

    out_port와 마찬가지로 출력 그룹에서 필터링합니다.

    해제하려면 ``OFPG_ANY`` 을 지정합니다. 

flags (0)

    다음 플래그의 조합을 지정할 수 있습니다. 

    .. tabularcolumns:: |l|L|

    ===================== ===================================================
    값                    설명
    ===================== ===================================================
    OFPFF_SEND_FLOW_REM   FLOW_REM이 항목이 삭제 된 때 컨트롤러에 Flow
                          Removed 메시지를 발행합니다. 
    OFPFF_CHECK_OVERLAP   OFPFC_ADD의 경우 중복 항목의 검사를 수행
                          있습니다. 중복 된 항목이있는 경우에는 Flow Mod가 손실
                          패하고 오류가 반환됩니다. 
    OFPFF_RESET_COUNTS    해당 항목의 패킷과 바이트 카운터를
                          재설정합니다. 
    OFPFF_NO_PKT_COUNTS   이 항목의 패킷 카운터를 해제합니다.
    OFPFF_NO_BYT_COUNTS   이 항목에 대한 바이트 카운터를 해제합니다.
    ===================== ===================================================

match (None)

    Match를 지정합니다.

instructions ([])

    명령어의 목록을 지정합니다.


패킷 전송
"""""""""

Packet-In 처리기로 돌아가 마지막 처리의 설명입니다. 

대상 MAC 주소를 MAC 주소 테이블에서 발견 여부에 관계없이 최종
에는 Packet-Out 메시지를 발행하여 수신 패킷을 전송합니다. 

.. rst-class:: sourcecode

::

    def _packet_in_handler(self, ev):
        # ...

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

Packet-Out 메시지에 대응하는 클래스는 ``OFPPacketOut`` 클래스입니다. 

OFPPacketOut 생성자의 인수는 다음과 같이되어 있습니다. 

datapath

    OpenFlow 스위치에 해당하는 Datapath 클래스의 인스턴스를 지정합니다. 

buffer_id

    OpenFlow 스위치에서 버퍼 된 패킷 버퍼 ID를 지정합니다. 
    버퍼를 사용하지 않으면, ``OFP_NO_BUFFER`` 을 지정합니다. 

in_port

    패킷을 수신 한 포트를 지정합니다. 수신 패킷이 아닌 경우 
    ``OFPP_CONTROLLER`` 를 지정합니다.

actions

    작업 목록을 지정합니다.

data

    패킷의 이진 데이터를 지정합니다. buffer_id에 ``OFP_NO_BUFFER``
    가 지정된 경우에 사용됩니다. OpenFlow 스위치 버퍼를 사용하는 경
    우 생략합니다. 


스위칭 허브의 구현은 buffer_id에 Packet-In 메시지 buffer_id을
지정합니다. Packet-In 메시지 buffer_id가 무효 인 경우,
Packet-In 들어오는 패킷을 data로 지정하여 패킷을 전송합니다.


이제 스위칭 허브 소스 코드의 설명은 끝입니다.
다음으로 스위칭 허브를 실행하여 실제 동작을 확인합니다. 


Ryu 응용 프로그램 실행
----------------------

스위칭 허브의 실행을 위해 OpenFlow 스위치는 Open vSwitch 실행
환경으로 mininet를 사용합니다.

Ryu의 OpenFlow Tutorial VM 이미지가 포함되어 있으므로,이 VM 이미지
를 이용하면 실험 환경을 쉽게 준비 할 수 있습니다. 

VM 이미지

    http://sourceforge.net/projects/ryu/files/vmimages/OpenFlowTutorial/

    OpenFlow_Tutorial_Ryu3.2.ova (약1.4GB)

관련 문서 (Wiki 페이지) 

    https://github.com/osrg/ryu/wiki/OpenFlow_Tutorial

문서에있는 VM 이미지는 Open vSwitch와 Ryu의 버전이 오래 되었기 때문에
주의하시기 바랍니다. 


이 VM 이미지를 사용하지 않고, 스스로 환경을 구축하는 것도 당연히 가능합니다.
VM 이미지에서 사용하는 각 소프트웨어 버전은 다음과 같으므로, 스스로 구축
하는 경우 추천합니다. 

Mininet VM 버전 2.0.0
  http://mininet.org/download/

Open vSwitch 버전 1.11.0
  http://openvswitch.org/download/

Ryu 버전 3.2
  https://github.com/osrg/ryu/

    .. rst-class:: console

    ::

        $ sudo pip install ryu


여기에서는 Ryu 용 OpenFlow Tutorial의 VM 이미지를 사용합니다. 

Mininet 실행
^^^^^^^^^^^^


mininet에서 xterm을 시작하기 위해 X를 사용할 수있는 환경이 필요합니다. 

여기에서는 OpenFlow Tutorial VM을 이용하고 있기 때문에,
ssh에서 X11 Forwarding을 사용하여 로그인합니다. 

    ::

        $ ssh -X ryu@<VM 주소>

사용자 이름은 ``ryu`` , 암호도 ``ryu`` 입니다.


로그인 후 ``mn`` 명령으로 Mininet 환경을 시작합니다.

구축 환경은 호스트 3 대, 스위치 하나의 간단한 구성입니다.

mn 명령의 매개 변수는 다음과 같습니다. 

============ ========== ===========================================
매개변수     값         설명
============ ========== ===========================================
topo         single,3   스위치 1 개, 호스트가 3 개의 토폴로지 
mac          없음       자동으로 호스트의 MAC 주소를 설정한다 
switch       ovsk       Open vSwitch를 사용
controller   remote     OpenFlow 컨트롤러는 외부의 것을 이용하기
x            없음       xterm을 시작
============ ========== ===========================================

실행 예는 다음과 같습니다.

.. rst-class:: console

::

    $ sudo mn --topo single,3 --mac --switch ovsk --controller remote -x
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

실행하면 데스크탑 PC에서 xterm을 5 개 시작합니다.
각 호스트 1 ~ 3 스위치 컨트롤러에 대응합니다.

스위치 xterm에서 명령을 실행하여 사용하는 OpenFlow 버전을
세트합니다. 윈도우 제목이 「switch : s1 (root)」이다
무슨 스위치 용 xterm입니다.

우선 Open vSwitch의 상태를보고합니다. 

switch: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl show
    fdec0957-12b6-4417-9d02-847654e9cc1f
    Bridge "s1"
        Controller "ptcp:6634"
        Controller "tcp:127.0.0.1:6633"
        fail_mode: secure
        Port "s1-eth3"
            Interface "s1-eth3"
        Port "s1-eth2"
            Interface "s1-eth2"
        Port "s1-eth1"
            Interface "s1-eth1"
        Port "s1"
            Interface "s1"
                type: internal
    ovs_version: "1.11.0"
    root@ryu-vm:~# ovs-dpctl show
    system@ovs-system:
            lookups: hit:14 missed:14 lost:0
            flows: 0
            port 0: ovs-system (internal)
            port 1: s1 (internal)
            port 2: s1-eth1
            port 3: s1-eth2
            port 4: s1-eth3
    root@ryu-vm:~#

스위치 (브리지) *s1* 수 있고, 호스트에 해당 포트가
3 개의 추가되어 있습니다.

다음 OpenFlow 버전으로 1.3을 설정합니다. 

switch: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-vsctl set Bridge s1 protocols=OpenFlow13
    root@ryu-vm:~#

빈 흐름 테이블을 확인하여보십시오. 

switch: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O OpenFlow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
    root@ryu-vm:~#

ovs-ofctl 명령에는 선택적으로 사용할 OpenFlow 버전을
지정해야합니다. 기본값은 *OpenFlow10* 입니다. 


스위칭 허브의 실행
^^^^^^^^^^^^^^^^^^

준비 하였으므로 Ryu 응용 프로그램을 실행합니다.

윈도우 제목이 「controller : c0 (root)」이다 xterm에서
다음 명령을 실행합니다. 

controller: c0:

.. rst-class:: console

::

    root@ryu-vm:~# ryu-manager --verbose ryu.app.simple_switch_13
    loading app ryu.app.simple_switch_13
    loading app ryu.controller.ofp_handler
    instantiating app ryu.app.simple_switch_13
    instantiating app ryu.controller.ofp_handler
    BRICK SimpleSwitch13
      CONSUMES EventOFPSwitchFeatures
      CONSUMES EventOFPPacketIn
    BRICK ofp_event
      PROVIDES EventOFPSwitchFeatures TO {'SimpleSwitch13': set(['config'])}
      PROVIDES EventOFPPacketIn TO {'SimpleSwitch13': set(['main'])}
      CONSUMES EventOFPErrorMsg
      CONSUMES EventOFPHello
      CONSUMES EventOFPEchoRequest
      CONSUMES EventOFPPortDescStatsReply
      CONSUMES EventOFPSwitchFeatures
    connected socket:<eventlet.greenio.GreenSocket object at 0x2e2c050> address:('127.0.0.1', 53937)
    hello ev <ryu.controller.ofp_event.EventOFPHello object at 0x2e2a550>
    move onto config mode
    EVENT ofp_event->SimpleSwitch13 EventOFPSwitchFeatures
    switch features ev version: 0x4 msg_type 0x6 xid 0xff9ad15b OFPSwitchFeatures(auxiliary_id=0,capabilities=71,datapath_id=1,n_buffers=256,n_tables=254)
    move onto main mode

OVS와의 연결에 시간이 걸리는 경우가 있습니다만, 조금 기다리면 위와 같이

.. rst-class:: console

::

    connected socket:<....
    hello ev ...
    ...
    move onto main mode

로 표시됩니다. 

이제 OVS와 연결 핸드 셰이크가 행해져 Table-miss 흐름 항목이
추가 된 Packet-In을 기다리고있는 상태가되어 있습니다.

Table-miss 흐름 항목이 추가되어 있는지 확인합니다. 

switch: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=105.975s, table=0, n_packets=0, n_bytes=0, priority=0 actions=CONTROLLER:65535
    root@ryu-vm:~#

우선 순위가 0에 매치가없고, 액션에 CONTROLLER 전송 데이터 크기 65535
(0xffff = OFPCML_NO_BUFFER)이 지정되어 있습니다. 


동작 확인
^^^^^^^^^

호스트 1에서 호스트 2로 ping을 실행합니다. 

1. ARP request

    이 시점에서 호스트 1 호스트 2의 MAC 주소를 모르기 때문에 ICMP echo
    request 앞서서 ARP request를 브로드 캐스팅하는 것입니다.
    이 브로드 캐스트 패킷은 호스트 2 및 호스트 3에서 수신됩니다. 

2. ARP reply

    호스트 2가 ARP 응답하여 호스트 1에 ARP reply를 반환합니다. 

3. ICMP echo request

    이제 호스트 1 호스트 2의 MAC 주소를 알 수 있었으므로, echo request 
    호스트 2에 보냅니다. 

4. ICMP echo reply

    호스트 2는 호스트 1의 MAC 주소를 이미 알고 있기 때문에, echo reply를 
    호스트 1에 반환합니다. 

이러한 통신이 이루어지는 것입니다.

ping 명령을 실행하기 전에 각 호스트에 어떤 패킷을 수신했는지 확인
수 있도록 tcpdump 명령을 실행해야합니다. 

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h1-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h1-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h2-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h2-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes

host: h3:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h3-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h3-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes


그럼 먼저 mn 명령을 실행 한 콘솔에서 다음 명령을 실행
호스트 1에서 호스트 2로 ping을 실행합니다. 

.. rst-class:: console

::

    mininet> h1 ping -c1 h2
    PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
    64 bytes from 10.0.0.2: icmp_req=1 ttl=64 time=97.5 ms

    --- 10.0.0.2 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 97.594/97.594/97.594/0.000 ms
    mininet>


ICMP echo reply 정상으로 돌아 왔습니다.

우선 흐름 테이블을 확인합니다.

switch: s1:

.. rst-class:: console

::

    root@ryu-vm:~# ovs-ofctl -O openflow13 dump-flows s1
    OFPST_FLOW reply (OF1.3) (xid=0x2):
     cookie=0x0, duration=417.838s, table=0, n_packets=3, n_bytes=182, priority=0 actions=CONTROLLER:65535
     cookie=0x0, duration=48.444s, table=0, n_packets=2, n_bytes=140, priority=1,in_port=2,dl_dst=00:00:00:00:00:01 actions=output:1
     cookie=0x0, duration=48.402s, table=0, n_packets=1, n_bytes=42, priority=1,in_port=1,dl_dst=00:00:00:00:00:02 actions=output:2
    root@ryu-vm:~#

Table-miss 흐름 항목 이외에 우선 순위가 1 흐름 항목이 2 개 등록되어
있습니다.

(1) 수신 포트 (in_port):2, MAC 수신 주소(dl_dst):호스트 1 →
    동작(actions):포트1로 전송
(2) 수신 포트 (in_port):1, MAC 수신 주소(dl_dst):호스트 2 →
    동작(actions):포트2로 전송

(1) 항목은 2 번 참조됩니다 (n_packets), (2) 항목은 1 번 참조됩니다.
(1)는 호스트 2에서 호스트 1에게 통신이므로 ARP reply 및 ICMP echo reply 두 가지
일치하는 것이지요.
(2)는 호스트 1에서 호스트 2에게 통신에서 ARP request는 브로드 캐스트되므로
이것은 ICMP echo request에 의한 것 일 것입니다.


그럼 simple_switch_13 로깅을보고 있습니다. 

controller: c0:

.. rst-class:: console

::

    EVENT ofp_event->SimpleSwitch13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 ff:ff:ff:ff:ff:ff 1
    EVENT ofp_event->SimpleSwitch13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:02 00:00:00:00:00:01 2
    EVENT ofp_event->SimpleSwitch13 EventOFPPacketIn
    packet in 1 00:00:00:00:00:01 00:00:00:00:00:02 1


첫 번째 Packet-In 호스트 1이 발행 한 ARP request에서 방송이므로
흐름 항목이 등록되지 않고 Packet-Out 만 발행됩니다.

두 번째는 호스트 2에서 반환 된 ARP reply에서 목적지 MAC 주소가 호스트 1이되고
그래서 위의 흐름 항목 (1)이 등록됩니다.

세 번째는 호스트 1에서 호스트 2로 전송 된 ICMP echo request에서 흐름 항목
(2)이 등록됩니다.

호스트 2에서 호스트 1에 반환 된 ICMP echo reply는 등록 된 흐름 항목 (1)
일치하기 때문에 Packet-In은 발행되지 않고 호스트 1에 전송됩니다.


마지막으로 각 호스트에서 실행 한 tcpdump의 출력을보고 있습니다. 

host: h1:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h1-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h1-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes
    20:38:04.625473 00:00:00:00:00:01 > ff:ff:ff:ff:ff:ff, ethertype ARP (0x0806), length 42: Request who-has 10.0.0.2 tell 10.0.0.1, length 28
    20:38:04.678698 00:00:00:00:00:02 > 00:00:00:00:00:01, ethertype ARP (0x0806), length 42: Reply 10.0.0.2 is-at 00:00:00:00:00:02, length 28
    20:38:04.678731 00:00:00:00:00:01 > 00:00:00:00:00:02, ethertype IPv4 (0x0800), length 98: 10.0.0.1 > 10.0.0.2: ICMP echo request, id 3940, seq 1, length 64
    20:38:04.722973 00:00:00:00:00:02 > 00:00:00:00:00:01, ethertype IPv4 (0x0800), length 98: 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 3940, seq 1, length 64


호스트 1에서 먼저 ARP request가 방송되고있어, 계속 호스트 2에서
반환 된 ARP reply를 받고 있습니다.
그런 다음 호스트 1이 발행 한 ICMP echo request 호스트 2에서 반환 된 ICMP echo reply가
수신되어 있습니다. 

host: h2:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h2-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h2-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes
    20:38:04.637987 00:00:00:00:00:01 > ff:ff:ff:ff:ff:ff, ethertype ARP (0x0806), length 42: Request who-has 10.0.0.2 tell 10.0.0.1, length 28
    20:38:04.638059 00:00:00:00:00:02 > 00:00:00:00:00:01, ethertype ARP (0x0806), length 42: Reply 10.0.0.2 is-at 00:00:00:00:00:02, length 28
    20:38:04.722601 00:00:00:00:00:01 > 00:00:00:00:00:02, ethertype IPv4 (0x0800), length 98: 10.0.0.1 > 10.0.0.2: ICMP echo request, id 3940, seq 1, length 64
    20:38:04.722747 00:00:00:00:00:02 > 00:00:00:00:00:01, ethertype IPv4 (0x0800), length 98: 10.0.0.2 > 10.0.0.1: ICMP echo reply, id 3940, seq 1, length 64


호스트 2에서 호스트 1이 발행 한 ARP request를 수신 호스트 1에 ARP reply를
반환합니다. 그런 다음 호스트 1에서 ICMP echo request를 수신 호스트 1
echo reply를 반환합니다. 

host: h3:

.. rst-class:: console

::

    root@ryu-vm:~# tcpdump -en -i h3-eth0
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on h3-eth0, link-type EN10MB (Ethernet), capture size 65535 bytes
    20:38:04.637954 00:00:00:00:00:01 > ff:ff:ff:ff:ff:ff, ethertype ARP (0x0806), length 42: Request who-has 10.0.0.2 tell 10.0.0.1, length 28


호스트 3은 먼저 호스트 1의 브로드 캐스팅 된 ARP request 만 수신
하고 있습니다. 



정리
----

이 장에서는 간단한 스위칭 허브 구현을 주제로 Ryu 응용 프로그램 구현
기본적인 절차와 OpenFlow에 따르면 OpenFlow 스위치의 간단한 제어 방법
설명했습니다.

