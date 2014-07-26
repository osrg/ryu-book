ofproto 라이브러리
==================

이 장에서는 Ryu의 ofproto 라이브러리에 대해 소개합니다. 

개요
----

ofproto 라이브러리는 OpenFlow 프로토콜 메시지의 작성 · 분석을 행하기위한
라이브러리입니다. 

모듈 구성
---------

각 OpenFlow 버전 (버전 XY)에 대해
상수 모듈 (ofproto_vX_Y)과
파서 모듈 (ofproto_vX_Y_parser)가 포함되어 있습니다.
각 OpenFlow 버전의 구현은 기본적으로 독립되어 있습니다. 

================== ======================== ===============================
OpenFlow버전       상수 모듈                파서 모듈
================== ======================== ===============================
1.0.x              ryu.ofproto.ofproto_v1_0 ryu.ofproto.ofproto_v1_0_parser
1.2.x              ryu.ofproto.ofproto_v1_2 ryu.ofproto.ofproto_v1_2_parser
1.3.x              ryu.ofproto.ofproto_v1_3 ryu.ofproto.ofproto_v1_3_parser
1.4.x              ryu.ofproto.ofproto_v1_4 ryu.ofproto.ofproto_v1_4_parser
================== ======================== ===============================

상수 모듈
^^^^^^^^^

상수 모듈은 프로토콜 상수 정의합니다.
예를 들면 다음과 같다. 

================ ==================================
상수             설명
================ ==================================
OFP_VERSION      프로토콜 버전 번호 
OFPP_xxxx        포트 번호 
OFPCML_NO_BUFFER 버퍼없이 전체 패킷을 전송 
OFP_NO_BUFFER    잘못된 버퍼 번호 
================ ==================================

파서 모듈 
^^^^^^^^^

파서 모듈은 각 OpenFlow 메시지에 대응 한 클래스가 정의되어 있습니다.
예를 들면 다음과 같다.
이 클래스와 그 인스턴스를 앞으로 메시지 클래스
메시지 개체라고합니다. 

================ ==================================
클래스           설명
================ ==================================
OFPHello         OFPT_HELLO 메시지
OFPPacketOut     OFPT_PACKET_OUT 메시지
OFPFlowMod       OFPT_FLOW_MOD 메시지
================ ==================================

또한 파서 모듈은 OpenFlow 메시지의 페이로드 중에 사용되는
구조에 대응하는 클래스도 정의되어 있습니다.
예를 들면 다음과 같다.
이 클래스와 그 인스턴스를 향후 구조 클래스
구조체 개체라고합니다. 

======================= ==================================
클래스                  구조체
======================= ==================================
OFPMatch                ofp_match
OFPInstructionGotoTable ofp_instruction_goto_table
OFPActionOutput         ofp_action_output
======================= ==================================

기본적인 사용법
---------------

ProtocolDesc 클래스
^^^^^^^^^^^^^^^^^^^

사용하는 OpenFlow 프로토콜을 지정하기위한 클래스입니다.
메시지 클래스의 __init__의 datapath 인수는이 클래스
(또는 파생 클래스 인 Datapath 클래스)의 객체를 지정합니다. 

.. rst-class:: sourcecode

::

    from ryu.ofproto import ofproto_protocol
    from ryu.ofproto import ofproto_v1_3

    dp = ofproto_protocol.ProtocolDesc(version=ofproto_v1_3.OFP_VERSION)

네트워크 주소 
^^^^^^^^^^^^^

Ryu ofproto 라이브러리의 API는 기본적으로 문자열 표현의 네트워크 주소가
사용됩니다. 예를 들면 다음과 같다. 

.. NOTE::

    그러나 OpenFlow 1.0에 관해서는 다른 표현이 사용되고 있습니다. 
    (2014년 2월 현재)

============= ===================
주소 종류     python 문자열 예제
============= ===================
MAC 주소      '00:03:47:8c:a1:b3'
IPv4 주소     '192.0.2.1'
IPv6 주소     '2001:db8::2'
============= ===================

메시지 개체의 생성
^^^^^^^^^^^^^^^^^^

각 메시지 클래스, 구조체 클래스의 인스턴스를 적절한 인수로 생성합니다.

인수의 이름은 기본적으로 OpenFlow 프로토콜에서 정해진 필드 이름
동일합니다. 그러나 python의 예약어와 충돌하는 경우 마지막에 「_」를 넣습니다.
다음 예제에서는 「``type_``」이 이에 해당됩니다.

.. rst-class:: sourcecode

::

    from ryu.ofproto import ofproto_protocol
    from ryu.ofproto import ofproto_v1_3

    dp = ofproto_protocol.ProtocolDesc(version=ofproto_v1_3.OFP_VERSION)
    ofp = dp.ofproto
    ofpp = dp.ofproto_parser
    actions = [parser.OFPActionOutput(port=ofp.OFPP_CONTROLLER,
                                      max_len=ofp.OFPCML_NO_BUFFER)]
    inst = [parser.OFPInstructionActions(type_=ofp.OFPIT_APPLY_ACTIONS,
                                         actions=actions)]
    fm = ofpp.OFPFlowMod(datapath=dp,
                         priority=0,
                         match=ofpp.OFPMatch(in_port=1,
                                             eth_src='00:50:56:c0:00:08'),
                         instructions=inst)

.. NOTE::

    상수 모듈 파서 모듈은 직접 import하여 사용해도 좋지만,
    사용하는 OpenFlow 버전을 변경할 때 최소한의 수정으로 끝나도록,
    가능한 ProtocolDesc 개체의 ofproto, ofproto_parser 특성을
    사용하는 것을 권장합니다. 

메시지 개체의 분석 
^^^^^^^^^^^^^^^^^^

메시지 개체의 내용을 확인할 수 있습니다.

예를 들어 OFPPacketIn 개체 pid의 match 필드가 pin.match로
액세스 할 수 있습니다.

OFPMatch 개체의 각 TLV 다음과 같이 이름으로 액세스 할 수 있습니다. 

.. rst-class:: sourcecode

::

    print pin.match['in_port']

JSON
^^^^

메시지 개체를 json.dumps 호환 사전으로 변환하는 기능과
json.loads 호환 사전에서 메시지 개체를 복원하는 기능이 있습니다. 

.. NOTE::

    그러나 OpenFlow 1.0 관해서는 구현이 불완전합니다. 
    (2014년 2월 현재)

.. rst-class:: sourcecode

::

    import json

    print json.dumps(msg.to_jsondict())

메시지의 해석 (Parse) 
^^^^^^^^^^^^^^^^^^^^^

메시지의 바이트 열에서 해당 메시지 객체를 생성합니다.
스위치에서받은 메시지 내용은 프레임 워크가 자동으로
이 처리를 행하기 위해, Ryu 응용 프로그램이 의식 할 필요는 없습니다.

구체적으로는 다음과 같습니다.

1. ryu.ofproto.ofproto_parser.header 함수를 사용하여 버전 독립적 부분을 분석
2 1. 결과를 ryu.ofproto.ofproto_parser.msg 함수에 전달하여 나머지 부분을 분석 

메시지의 생성 (연재) 
^^^^^^^^^^^^^^^^^^^^

메시지 개체에서 해당 메시지의 바이트를 생성합니다.
스위치에 보내는 메시지 내용은 프레임 워크가 자동으로
이 처리를 행하기 위해, Ryu 응용 프로그램이 의식 할 필요는 없습니다.

구체적으로는 다음과 같습니다.

1. 메시지 개체의 serialize 메소드를 호출
2. 메시지 개체의 buf 특성을 읽을

'len'같은 일부 필드는 명시 적으로 값을 지정하지 않아도
serialize시 자동으로 계산됩니다.
