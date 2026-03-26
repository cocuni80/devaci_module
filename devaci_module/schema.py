import json
import urllib3
import cobra.mit.session
import cobra.mit.access
import cobra.mit.request
import cobra.model.aaa
import cobra.model.ep
import cobra.model.geo
import cobra.model.coop
import cobra.model.ctrlr
import cobra.model.fv
import cobra.model.l3ext
import cobra.model.l2ext
import cobra.model.ospf
import cobra.model.infra
import cobra.model.dhcp
import cobra.model.fabric
import cobra.model.datetime
import cobra.model.snmp
import cobra.model.comm
import cobra.model.cdp
import cobra.model.lldp
import cobra.model.lacp
import cobra.model.stp
import cobra.model.stormctrl
import cobra.model.mcp
import cobra.model.pol
import cobra.model.fvns
import cobra.model.phys
import cobra.model.qos
import cobra.model.bgp
import cobra.model.pki
import cobra.model.isis
import cobra.model.latency
import cobra.model.infrazone
import cobra.model.mgmt
import cobra.model.vz
import cobra.model.pim
import cobra.model.igmp

from typing import Optional
from datetime import datetime
from typing import Mapping, Iterable, Any
from math import isnan
from .jinja import JinjaResult

ACI_SCHEMA = {
    "fvAEPg": {
        "class": cobra.model.fv.AEPg,
        "parent": ["fvAp"],
        "requires": ["tenant", "fvApName"],
        "children": {
            "fvRsBd": {
                "class": cobra.model.fv.RsBd,
                "validators": ["tnFvBDName"],
                "multi": False,
            },
            "fvRsDomAtt": {
                "class": cobra.model.fv.RsDomAtt,
                "validators": ["tDn"],
                "multi": True,
            },
            "fvRsPathAtt": {
                "class": cobra.model.fv.RsPathAtt,
                "validators": ["tDn", "primaryEncap", "mode"],
                "multi": True,
            },
        },
    }
}
