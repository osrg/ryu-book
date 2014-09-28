OF-Config 라이브러리
====================

이 장에서는 Ryu에 포함된 OF-Config 클라이언트 라이브러리에 대해
소개합니다. 

OF-Config 프로토콜
------------------

OF-Config는 OpenFlow 스위치의 관리를 위한
프로토콜입니다.
NETCONF (RFC 6241) 스키마로 정의되며,
논리 스위치, 포트, 큐 등의 상태를 얻어오거나 설정이 가능합니다.

OpenFlow와 동일하게 ONF에서 제정한 것으로, 다음 사이트에서 스펙을 확인할 수 있습니다. 

https://www.opennetworking.org/sdn-resources/onf-specifications/openflow-config

이 라이브러리는 OF-Config 1.1.1을 준수하고 있습니다. 

.. NOTE::
    현재 Open vSwitch는 OF-Config를 지원하지 않지만
    같은 목적을 위해 OVSDB하는 서비스를 제공하고 있습니다.
    OF-Config는 비교적 새로운 표준으로 Open vSwitch가 OVSDB을
    구현했을 때는 아직 존재하지 않았었습니다.

    OVSDB 프로토콜은 RFC 7047으로 스펙이 공개되어 있지만,
    사실상 Open vSwitch 전용 프로토콜이 되고 있습니다.
    OF-Config는 비록 갓 등장하였지만 미래에는
    많은 OpenFlow 스위치에서 구현될 것으로 예상됩니다. 

라이브러리 구성
---------------

ryu.lib.of_config.capable_switch.OFCapableSwitch 클래스
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

NETCONF 세션을 처리하기 위한 클래스입니다.

.. rst-class:: sourcecode

::

        from ryu.lib.of_config.capable_switch import OFCapableSwitch

ryu.lib.of_config.classes 모듈
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

설정 내용을 python 객체로 취급하기위한 클래스 군을 제공하는
모듈입니다. 

.. NOTE::
    클래스 이름은 기본적으로 OF-Config 1.1.1 yang specification에
    grouping 키워드로 사용되는 이름과 동일합니다.
    예. OFPortType

.. rst-class:: sourcecode

::

        import ryu.lib.of_config.classes as ofc

예제 
----

스위치에 연결
^^^^^^^^^^^^^

SSH 트랜스 포트를 사용하여 스위치에 연결합니다.
unknown_host_cb에는 알 수 없는 SSH 호스트 키를 처리하는 콜백 함수가 있지만,
여기에서는 무조건 연결을 계속하도록 하고 있습니다. 

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

NETCONF GET을 사용하여 상태를 가져 오는 방법입니다.
모든 포트의 
/resources/port/resource-id와
/resources/port/current-rate를 표시합니다. 

.. rst-class:: sourcecode

::

        csw = sess.get()
        for p in csw.resources.port:
            print p.resource_id, p.current_rate

GET-CONFIG
^^^^^^^^^^

NETCONF GET-CONFIG를 사용하여 설정을 검색하는 예입니다. 

.. NOTE::
    실행은 현재 NETCONF의 데이터 저장소에서 실행되는 설정입니다.
    구현에 따라, 그 밖에도 startup (장치를 시작할 때 로드되는 기타 설정)
    나 candidate (후보 설정) 등의 데이터 스토어를 이용할 수 있습니다. 

모든 포트의 
/resources/port/resource-id와
/resources/port/configuration/admin-state를 표시합니다.

.. rst-class:: sourcecode

::

        csw = sess.get_config('running')
        for p in csw.resources.port:
            print p.resource_id, p.configuration.admin_state

EDIT-CONFIG
^^^^^^^^^^^

NETCONF EDIT-CONFIG를 사용하여 설정을 변경하는 예입니다. 
기본적으로 GET-CONFIG에서 얻은 설정을 편집하여 EDIT-CONFIG를 사용해 
다시 전송하는 단계입니다. 

.. NOTE::
    프로토콜상에서는 EDIT-CONFIG 설정의 부분적 편집을 할 수도
    있지만 이러한 방법이 무난합니다. 

모든 포트의 
/resources/port/configuration/admin-state를 down으로 설정합니다.

.. rst-class:: sourcecode

::

        csw = sess.get_config('running')
        for p in csw.resources.port:
            p.configuration.admin_state = 'down'
        sess.edit_config('running', csw)
