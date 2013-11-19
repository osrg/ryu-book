import json
from ryu.app import simple_switch_13
from webob import Response
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.lib import dpid as dpid_lib

simple_switch_instance_name = 'simple_switch_api_app'
url = '/v1/simpleswitch/mactable/{dpid}'

class SimpleSwitchRest13(simple_switch_13.SimpleSwitch13):

    _CONTEXTS = { 'wsgi': WSGIApplication }

    def __init__(self, *args, **kwargs):
        super(SimpleSwitchRest13, self).__init__(*args, **kwargs)
        self.switches = {}
        wsgi = kwargs['wsgi']
        wsgi.register(SimpleSwitchController, {simple_switch_instance_name : self})

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        super(SimpleSwitchRest13, self).switch_features_handler(ev)
        datapath = ev.msg.datapath
        self.switches[datapath.id] = datapath

    def set_mac_to_port(self, dpid, mac_port_dict):
        datapath = self.switches.get(dpid, None)

        if datapath is not None:
            parser = datapath.ofproto_parser
            ports = mac_port_dict.values()
            for in_port in ports:
                for mac, port in mac_port_dict.items():
                    if port != in_port:
                        dst_mac = mac
                        out_port = port
                        actions = [parser.OFPActionOutput(out_port)]
                        match = parser.OFPMatch(in_port=in_port, eth_dst=dst_mac)
                        self.add_flow(datapath, 1, match, actions)

        mac_table = self.mac_to_port.get(dpid, {})
        mac_table.update(mac_port_dict)
        self.mac_to_port[dpid] = mac_table
        return {'status' : 'ok'}


class SimpleSwitchController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(SimpleSwitchController, self).__init__(req, link, data, **config)
        self.simpl_switch_spp = data[simple_switch_instance_name]

    @route('simpleswitch', url, methods=['GET'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def list_mac_table(self, req, **kwargs):
        simple_switch = self.simpl_switch_spp
        mac_table = {}

        if 'dpid' in kwargs:
            dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
            mac_table = simple_switch.mac_to_port.get(dpid, {})

        body = json.dumps(mac_table)
        return Response(content_type='application/json', body=body)

    @route('simpleswitch', url, methods=['PUT'], requirements={'dpid': dpid_lib.DPID_PATTERN})
    def put_mac_table(self, req, **kwargs):
        simple_switch = self.simpl_switch_spp
        result = {}
        if 'dpid' in kwargs:
            dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
            mac_table = eval(req.body)
            result = simple_switch.set_mac_to_port(dpid, mac_table)

        body = json.dumps(result)
        return Response(content_type='application/json', body=body)


