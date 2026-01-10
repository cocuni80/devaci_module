# Copyright 2020 Jorge C. Riveros
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ACI module configuration for the ACI Python SDK (cobra)."""

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


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ------------------------------------------   ACI Error Class


class CobraError(Exception):
    """
    The CobraError class manage the exceptions for Cobra class
    """

    def __init__(self, reason):
        self.reason = reason
        # print(f"\x1b[31;1m{self.reason}\x1b[0m")

    def __str__(self):
        return self.reason


# ------------------------------------------   Cobra Result Class


class CobraResult:
    """
    The CobraResult class return the results for Cobra class
    """

    def __init__(self):
        self.date = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
        self._config = None
        self._success = False
        self._log = []
        self.path = None

    @property
    def config(self) -> Optional[cobra.mit.request.ConfigRequest]:
        return self._config

    @property
    def xml(self) -> bool:
        return self._config.xmldata if self._config else None

    @property
    def json(self) -> bool:
        return json.loads(self._config.data) if self._config else None

    @property
    def success(self) -> bool:
        return self._success

    @property
    def log(self) -> list:
        return self._log

    @property
    def output(self) -> dict:
        return [
            {
                "date": self.date,
                "json": self.json,
                "xml": self.xml,
                "success": self._success,
                "log": self._log,
            }
        ]

    @success.setter
    def success(self, value):
        self._success = value

    @log.setter
    def log(self, value):
        self._log.append(value)

    @config.setter
    def config(self, value):
        self._config = value

    def __str__(self):
        return "CobraResult"


# ------------------------------------------   ACI Class


class CobraClass:
    """
    Mo class from Cobra SDK
    """

    def __init__(self):
        # --------------   ACI Information
        self.__root = ""
        self.__uni = cobra.model.pol.Uni(self.__root)
        # self.__uni.setConfigZone("PROD")
        self.config = cobra.mit.request.ConfigRequest()

        # --------------   Output Information

        self._result = CobraResult()

    # -------------------------------------------------   Control

    @property
    def result(self):
        return self._result

    def render(self, jinja: JinjaResult) -> None:
        """
        Render the given Jinja template and execute corresponding CobraClass methods.

        Only executes methods with non-empty values.
        Successful executions are printed in green, failed executions in red.
        All log messages are stored as a plain list in self._result.log.
        """
        RED = "\033[31;1m"
        GREEN = "\033[32;1m"
        WHITE = "\033[37;1m"
        YELLOW = "\033[33;1m"
        MAGENTA = "\033[35;1m"
        RESET = "\033[0m"

        for key, value in jinja.output.items():
            # Skip empty values
            if value in (None, [], {}, ""):
                continue

            caller = getattr(CobraClass, key, None)

            if not callable(caller):
                msg = f"[Cobra] -> [ConfigError]: Class {key} does not exist. "
                print(f"{YELLOW}[Cobra] -> [ConfigError]::{RED} Class {key}does not exist.{RESET}")
                self._result.log = msg
                success = False
                continue
            try:
                caller(self, value)
                msg = f"[Cobra]: Class {key} was rendered successfully."
                print(f"{YELLOW}[Cobra]:{GREEN} Class {key} was rendered successfully.{RESET}")
                self._result.log = msg
                success = True
            except Exception as e:
                msg = f"[Cobra] -> [{type(e).__name__}]: Class {key} failed: {e}"
                print(f"{YELLOW}[Cobra] -> [{type(e).__name__}]:{RED} Class {key} failed, {e}{RESET}")
                self._result.log = msg
                success = False

        if not self.config.configMos:
            msg = f"[Cobra] -> [ConfigError]: No object was found in configuration."
            print(f"{YELLOW}[Cobra] -> [ConfigError]:{RED} No object was found in configuration.{RESET} ")  # red in console
            self._result.log = msg
            success = False

        self._result.config = self.config
        self._result.success = success

    # -------------------------------------------------   REST Tenant Management

    def fvTenant(self, value) -> None:
        """
        Tenants > All Tenants
        """
        Uni = cobra.model.pol.Uni(self.__root)
        for fvTenant in value:
            Tenant = cobra.model.fv.Tenant(Uni, **fvTenant)
            self.config.addMo(Tenant)

    def fvAp(self, value) -> None:
        """
        Tenants > Application Profiles
        """
        Uni = cobra.model.pol.Uni(self.__root)
        for fvAp in value:
            if not_nan_str(fvAp, ["name", "tenant"]):
                Tenant = cobra.model.fv.Tenant(Uni, name=fvAp["tenant"])
                Ap = cobra.model.fv.Ap(Tenant, **fvAp)
                self.config.addMo(Ap)

    def fvAEPg(self, value) -> None:
        """
        Tenants > Application Profiles > Application EPGs
        """
        Uni = cobra.model.pol.Uni(self.__root)
        for fvAEPg in value:
            Tenant = cobra.model.fv.Tenant(Uni, name=fvAEPg["tenant"])
            Ap = cobra.model.fv.Ap(Tenant, name=fvAEPg["fvApName"])
            AEPg = cobra.model.fv.AEPg(Ap, **fvAEPg)
            self.config.addMo(AEPg)
            if "fvRsBd" in fvAEPg:
                if not_nan_str(fvAEPg["fvRsBd"], ["tnFvBDName"]):
                    RsBd = cobra.model.fv.RsBd(AEPg, **fvAEPg["fvRsBd"])
                    self.config.addMo(RsBd)
            if "fvRsDomAtt" in fvAEPg:
                for fvRsDomAtt in fvAEPg["fvRsDomAtt"]:
                    if not_nan_str(fvRsDomAtt, ["tDn"]):
                        RsDomAtt = cobra.model.fv.RsDomAtt(AEPg, **fvRsDomAtt)
                        self.config.addMo(RsDomAtt)
            if "fvRsPathAtt" in fvAEPg:
                for fvRsPathAtt in fvAEPg["fvRsPathAtt"]:
                    if not_nan_str(fvRsPathAtt, ["tDn", "primaryEncap", "mode"]):
                        RsPathAtt = cobra.model.fv.RsPathAtt(AEPg, **fvRsPathAtt)
                        self.config.addMo(RsPathAtt)

    def staticPath(self, value) -> None:
        """
        Tenants > Application Profiles > Application EPGs > EPG Name > Static Ports
        """
        Uni = cobra.model.pol.Uni(self.__root)
        for fvAp in value:
            Tenant = cobra.model.fv.Tenant(Uni, name=fvAp["tenant"])
            self.config.addMo(Tenant)
            Ap = cobra.model.fv.Ap(Tenant, **fvAp)
            self.config.addMo(Ap)
            if "fvAEPg" in fvAp:
                for fvAEPg in fvAp["fvAEPg"]:
                    AEPg = cobra.model.fv.AEPg(Ap, **fvAEPg)
                    # self.config.addMo(AEPg)
                    if "fvRsPathAtt" in fvAEPg:
                        for fvRsPathAtt in fvAEPg["fvRsPathAtt"]:
                            RsPathAtt = cobra.model.fv.RsPathAtt(AEPg, **fvRsPathAtt)
                            self.config.addMo(RsPathAtt)

    def fvRsPathAtt(self, value) -> None:
        """
        Tenants > Application Profiles > Application EPGs > EPG Name > Static Ports
        """
        Uni = cobra.model.pol.Uni(self.__root)
        for fvRsPathAtt in value:
            if not_nan_str(fvRsPathAtt, ["tenant", "fvApName", "fvAEPgName", "tDn", "primaryEncap", "mode"]):
                Tenant = cobra.model.fv.Tenant(Uni, name=fvRsPathAtt["tenant"])
                self.config.addMo(Tenant)
                Ap = cobra.model.fv.Ap(Tenant, name=fvRsPathAtt["fvApName"])
                self.config.addMo(Ap)
                AEPg = cobra.model.fv.AEPg(Ap, name=fvRsPathAtt["fvAEPgName"])
                self.config.addMo(AEPg)
                RsPathAtt = cobra.model.fv.RsPathAtt(AEPg, **fvRsPathAtt)
                self.config.addMo(RsPathAtt)

    def tenant_application_uepg(self, value) -> None:
        """
        Tenants > Application Profiles > uSeg EPGs
        """
        for item in value:
            mo = item
            self.config.addMo(mo)

    def tenant_application_esg(self, value):
        """
        Tenants > Application Profiles > Endpoint Security Groups
        """
        pass

    def fvBD(self, value) -> None:
        """
        Tenants > Networking > Bridge Domains
        """
        Uni = cobra.model.pol.Uni(self.__root)
        for fvBD in value:
            Tenant = cobra.model.fv.Tenant(Uni, name=fvBD["tenant"])
            BD = cobra.model.fv.BD(Tenant, **fvBD)
            self.config.addMo(BD)
            if "fvRsCtx" in fvBD:
                if not_nan_str(fvBD["fvRsCtx"], ["tnFvCtxName"]):
                    RsCtx = cobra.model.fv.RsCtx(BD, **fvBD["fvRsCtx"])
                    self.config.addMo(RsCtx)
            if "igmpIfP" in fvBD:
                if not_nan_str(fvBD["igmpIfP"], ["name"]):
                    IfP = cobra.model.igmp.IfP(BD, **fvBD["igmpIfP"])
                    self.config.addMo(IfP)
            if "fvRsBdToEpRet" in fvBD:
                if not_nan_str(fvBD["fvRsBdToEpRet"], ["tnFvEpRetPolName"]):
                    RsBdToEpRet = cobra.model.fv.RsBdToEpRet(BD, **fvBD["fvRsBdToEpRet"])
                    self.config.addMo(RsBdToEpRet)
            if "fvRsIgmpsn" in fvBD:
                if not_nan_str(fvBD["fvRsIgmpsn"], ["tnIgmpSnoopPolName"]):
                    RsIgmpsn = cobra.model.fv.RsIgmpsn(BD, **fvBD["fvRsIgmpsn"])
                    self.config.addMo(RsIgmpsn)
            if "fvRsMldsn" in fvBD:
                if not_nan_str(fvBD["fvRsMldsn"], ["tnMldSnoopPolName"]):
                    RsMldsn = cobra.model.fv.RsMldsn(BD, **fvBD["fvRsMldsn"])
                    self.config.addMo(RsMldsn)
            if "fvRsBDToOut" in fvBD:
                if not_nan_str(fvBD["fvRsBDToOut"], ["tnL3extOutName"]):
                    RsBDToOut = cobra.model.fv.RsBDToOut(BD, **fvBD["fvRsBDToOut"])
                    self.config.addMo(RsBDToOut)
            if "fvSubnet" in fvBD:
                for fvSubnet in fvBD["fvSubnet"]:
                    if not_nan_str(fvSubnet, ["ip"]):
                        Subnet = cobra.model.fv.Subnet(BD, **fvSubnet)
                        self.config.addMo(Subnet)

    def fvCtx(self, value) -> None:
        """
        Tenants > Networking > VRFs
        """
        Uni = cobra.model.pol.Uni(self.__root)
        for fvCtx in value:
            Tenant = cobra.model.fv.Tenant(Uni, name=fvCtx["tenant"])
            Ctx = cobra.model.fv.Ctx(Tenant, **fvCtx)
            self.config.addMo(Ctx)
            if "vzAny" in fvCtx:
                Any = cobra.model.vz.Any(Ctx, **fvCtx["vzAny"])
                self.config.addMo(Any)
                if "vzRsAnyToProv" in fvCtx["vzAny"]:
                    for vzRsAnyToProv in fvCtx["vzAny"]["vzRsAnyToProv"]:
                        if not_nan_str(vzRsAnyToProv, ["tnVzBrCPName"]):
                            RsAnyToProv = cobra.model.vz.RsAnyToProv(Any, **vzRsAnyToProv)
                            self.config.addMo(RsAnyToProv)
                if "vzRsAnyToCons" in fvCtx["vzAny"]:
                    for vzRsAnyToCons in fvCtx["vzAny"]["vzRsAnyToCons"]:
                        if not_nan_str(vzRsAnyToCons, ["tnVzBrCPName"]):
                            RsAnyToCons = cobra.model.vz.RsAnyToCons(Any, **vzRsAnyToCons)
                            self.config.addMo(RsAnyToCons)
            if "fvRsCtxToEpRet" in fvCtx:
                if not_nan_str(fvCtx["fvRsCtxToEpRet"], ["tnFvEpRetPolName"]):
                    RsCtxToEpRet = cobra.model.fv.RsCtxToEpRet(Ctx, **fvCtx["fvRsCtxToEpRet"])
                    self.config.addMo(RsCtxToEpRet)
            if "fvRsCtxToExtRouteTagPol" in fvCtx:
                if not_nan_str(fvCtx["fvRsCtxToExtRouteTagPol"], ["tnL3extRouteTagPolName"]):
                    RsCtxToExtRouteTagPol = cobra.model.fv.RsCtxToExtRouteTagPol(Ctx, **fvCtx["fvRsCtxToExtRouteTagPol"])
                    self.config.addMo(RsCtxToExtRouteTagPol)
            if "fvRsOspfCtxPol" in fvCtx:
                if not_nan_str(fvCtx["fvRsOspfCtxPol"], ["tnOspfCtxPolName"]):
                    RsOspfCtxPol = cobra.model.fv.RsOspfCtxPol(Ctx, **fvCtx["fvRsOspfCtxPol"])
                    self.config.addMo(RsOspfCtxPol)
            if "fvRsBgpCtxPol" in fvCtx:
                if not_nan_str(fvCtx["fvRsBgpCtxPol"], ["tnBgpCtxPolName"]):
                    RsBgpCtxPol = cobra.model.fv.RsBgpCtxPol(Ctx, **fvCtx["fvRsBgpCtxPol"])
                    self.config.addMo(RsBgpCtxPol)
            if "fvRsVrfValidationPol" in fvCtx:
                if not_nan_str(fvCtx["fvRsVrfValidationPol"], ["tnL3extVrfValidationPolName"]):
                    RsVrfValidationPol = cobra.model.fv.RsVrfValidationPol(Ctx, **fvCtx["fvRsVrfValidationPol"])
                    self.config.addMo(RsVrfValidationPol)
            if "pimCtxP" in fvCtx:
                if not_nan_str(fvCtx["pimCtxP"], ["mtu"]):
                    CtxP = cobra.model.pim.CtxP(Ctx, **fvCtx["pimCtxP"])
                    self.config.addMo(CtxP)

    def tenant_network_l2out(self, value):
        """
        Tenants > Networking > L2Outs
        """
        pass

    def l3extOut(self, value) -> None:
        """
        Tenants > Networking > L3Outs
        """
        for item in value:
            mo = cobra.model.l3ext.Out(self.tenant(**item), **item)
            if "l3extRsEctx" in item:
                cobra.model.l3ext.RsEctx(mo, **item["l3extRsEctx"])
            if "l3extRsL3DomAtt" in item:
                cobra.model.l3ext.RsL3DomAtt(mo, **item["l3extRsL3DomAtt"])
            if "ospfExtP" in item:
                cobra.model.ospf.ExtP(mo, **item["ospfExtP"])
            if "l3extLNodeP" in item:
                for node in item["l3extLNodeP"]:
                    l3ext_lnodep = cobra.model.l3ext.LNodeP(mo, **node)
                    if "l3extRsNodeL3OutAtt" in node:
                        for node_l3out_att in node["l3extRsNodeL3OutAtt"]:
                            cobra.model.l3ext.RsNodeL3OutAtt(l3ext_lnodep, **node_l3out_att)
                    if "l3extLIfP" in node:
                        l3ext_lifp = cobra.model.l3ext.LIfP(l3ext_lnodep, **node["l3extLIfP"])
                        if "l3extRsPathL3OutAtt" in node["l3extLIfP"]:
                            for l3att in node["l3extLIfP"]["l3extRsPathL3OutAtt"]:
                                cobra.model.l3ext.RsPathL3OutAtt(l3ext_lifp, **l3att)
            self.config.addMo(mo)

    def tenant_network_srmpls_l3out(self, value):
        """
        Tenants > Networking > SR-MPLS VRF L3Outs
        """
        pass

    def tenant_dot1q_tunnel(self, value):
        """
        Tenants > Networking > Dot1Q Tunnels
        """
        pass

    def fvnsAddrInst(self, value):
        """
        Tenants > mgmt > IP Address Pools
        """
        Uni = cobra.model.pol.Uni(self.__root)
        for fvnsAddrInst in value:
            Tenant = cobra.model.fv.Tenant(Uni, name=fvnsAddrInst["tenant"])
            AddrInst = cobra.model.fvns.AddrInst(Tenant, **fvnsAddrInst)
            self.config.addMo(AddrInst)
            if "fvnsUcastAddrBlk" in fvnsAddrInst:
                for fvnsUcastAddrBlk in fvnsAddrInst["fvnsUcastAddrBlk"]:
                    if not_nan_str(fvnsUcastAddrBlk, ["from"]):
                        UcastAddrBlk = cobra.model.fvns.UcastAddrBlk(AddrInst, **fvnsUcastAddrBlk)
                        self.config.addMo(UcastAddrBlk)

    def mgmtGrp(self, value):
        """
        Tenants > mgmt > Managed Node Connectivity Groups
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        FuncP = cobra.model.infra.FuncP(Infra)
        for mgmtGrp in value:
            Grp = cobra.model.mgmt.Grp(FuncP, **mgmtGrp)
            self.config.addMo(Grp)
            if "mgmtOoBZone" in mgmtGrp:
                OoBZone = cobra.model.mgmt.OoBZone(Grp)
                if "mgmtRsOoB" in mgmtGrp["mgmtOoBZone"]:
                    RsOoB = cobra.model.mgmt.RsOoB(OoBZone, **mgmtGrp["mgmtOoBZone"]["mgmtRsOoB"])
                    self.config.addMo(RsOoB)
                if "mgmtRsAddrInst" in mgmtGrp["mgmtOoBZone"]:
                    RsAddrInst = cobra.model.mgmt.RsAddrInst(OoBZone, **mgmtGrp["mgmtOoBZone"]["mgmtRsAddrInst"])
                    self.config.addMo(RsAddrInst)
            if "mgmtInBZone" in mgmtGrp:
                InBZone = cobra.model.mgmt.InBZone(Grp)
                if "mgmtRsInB" in mgmtGrp["mgmtInBZone"]:
                    RsInB = cobra.model.mgmt.RsInB(InBZone, **mgmtGrp["mgmtInBZone"]["mgmtRsInB"])
                    self.config.addMo(RsInB)
                if "mgmtRsAddrInst" in mgmtGrp["mgmtInBZone"]:
                    RsAddrInst = cobra.model.mgmt.RsAddrInst(InBZone, **mgmtGrp["mgmtInBZone"]["mgmtRsAddrInst"])
                    self.config.addMo(RsAddrInst)

    def mgmtNodeGrp(self, value):
        """
        Tenants > mgmt > Node Management Addresses
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        for mgmtNodeGrp in value:
            NodeGrp = cobra.model.mgmt.NodeGrp(Infra, **mgmtNodeGrp)
            self.config.addMo(NodeGrp)
            if "mgmtRsGrp" in mgmtNodeGrp:
                for mgmtRsGrp in mgmtNodeGrp["mgmtRsGrp"]:
                    RsGrp = cobra.model.mgmt.RsGrp(NodeGrp, **mgmtRsGrp)
                    self.config.addMo(RsGrp)
            if "infraNodeBlk" in mgmtNodeGrp:
                for infraNodeBlk in mgmtNodeGrp["infraNodeBlk"]:
                    if not_nan_str(infraNodeBlk, ["from_"]):
                        NodeBlk = cobra.model.infra.NodeBlk(NodeGrp, **infraNodeBlk)
                        self.config.addMo(NodeBlk)

    def tenant_contract_standard(self, value):
        """
        Tenants > Contracts > Standard
        """
        pass

    def tenant_contract_taboo(self, value):
        """
        Tenants > Contracts > Taboos
        """
        pass

    def tenant_contract_imported(self, value):
        """
        Tenants > Contracts > Imported
        """
        pass

    def tenant_contract_filter(self, value):
        """
        Tenants > Contracts > Filters
        """
        pass

    def tenant_contract_oob(self, value):
        """
        Tenants > Contracts > Out-Of-Band Contracts
        """
        pass

    def tenant_policy_protocol_bfd(self, value):
        """
        Tenants > Policies > Protocol > BFD
        """
        pass

    def tenant_policy_protocol_bgp(self, value):
        """
        Tenants > Policies > Protocol > BGP
        """
        pass

    def tenant_policy_protocol_qos(self, value):
        """
        Tenants > Policies > Protocol > Custom QoS
        """
        pass

    def tenant_policy_protocol_dhcp(self, value):
        """
        Tenants > Policies > Protocol > DHCP
        """
        pass

    def tenant_policy_protocol_dataplane(self, value):
        """
        Tenants > Policies > Protocol > Data Plane Policing
        """
        pass

    def tenant_policy_protocol_eigrp(self, value):
        """
        Tenants > Policies > Protocol > EIGRP
        """
        pass

    def tenant_policy_protocol_endpoint_retention(self, value):
        """
        Tenants > Policies > Protocol > End Point Retention
        """
        pass

    def tenant_policy_protocol_firsthop_security(self, value):
        """
        Tenants > Policies > Protocol > First Hop Security
        """
        pass

    def tenant_policy_protocol_hsrp(self, value):
        """
        Tenants > Policies > Protocol > HSRP
        """
        pass

    def tenant_policy_protocol_igmp(self, value):
        """
        Tenants > Policies > Protocol > IGMP
        """
        pass

    def tenant_policy_protocol_ip_sla(self, value):
        """
        Tenants > Policies > Protocol > IP SLA
        """
        pass

    def tenant_policy_protocol_pbr(self, value):
        """
        Tenants > Policies > Protocol > L4-L7 Policy-Based Redirect
        """
        pass

    def tenant_policy_protocol_ospf(self, value):
        """
        Tenants > Policies > Protocol > OSPF
        """
        pass

    def tenant_policy_protocol_pim(self, value):
        """
        Tenants > Policies > Protocol > PIM
        """
        pass

    def tenant_policy_protocol_routemap_multicast(self, value):
        """
        Tenants > Policies > Protocol > Route Maps for Multicast
        """
        pass

    def tenant_policy_protocol_routemap_control(self, value):
        """
        Tenants > Policies > Protocol > Route Maps for Route Control
        """
        pass

    def tenant_policy_protocol_route_tag(self, value):
        """
        Tenants > Policies > Protocol > Route Tag
        """
        pass

    def tenant_policy_troubleshooting_span(self, value):
        """
        Tenants > Policies > Troubleshooting SPAN
        """
        pass

    def tenant_policy_troubleshooting_traceroute(self, value):
        """
        Tenants > Policies > Troubleshooting Traceroute
        """
        pass

    def tenant_policy_monitoring(self, value):
        """
        Tenants > Policies > Monitoring
        """
        pass

    def tenant_policy_netflow(self, value):
        """
        Tenants > Policies > NetFlow
        """
        pass

    def tenant_policy_vmm(self, value):
        """
        Tenants > Policies > VMM
        """
        pass

    def tenant_service_parameter(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Service Parameters
        """
        pass

    def tenant_service_graph_template(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Service Graph Templates
        """
        pass

    def tenant_service_router_configuration(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Router Configuration
        """
        pass

    def tenant_service_function_profile(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Function Profiles
        """
        pass

    def tenant_service_devices(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Devices
        """
        pass

    def tenant_service_imported_device(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Imported Devices
        """
        pass

    def tenant_service_device_policy(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Device Selection Policies
        """
        pass

    def tenant_service_deployed_graph_instance(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Deployed Graph Instances
        """
        pass

    def tenant_service_deployed_device(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Deployed Devices
        """
        pass

    def tenant_service_device_manager(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Device Managers
        """
        pass

    def tenant_service_chassis(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Chassis
        """
        pass

    def tenant_node_management_epg(self, value):
        """
        Tenants > Node Management EPGs
        """
        pass

    def tenant_external_management_profile(self, value):
        """
        Tenants > External Management Network Instance Profiles
        """
        pass

    def tenant_node_management_address(self, value):
        """
        Tenants > Node Management Address
        """
        pass

    def tenant_node_management_static(self, value):
        """
        Tenants > Node Management Address > Static Node Management Address
        """
        pass

    def tenant_node_connection_group(self, value):
        """
        Tenants > Managed Node Connectivity Groups
        """
        pass

    def fabricSetupPol(self, value):
        """
        Fabric > Inventory > Pod Fabric Setup Policy
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Inst = cobra.model.ctrlr.Inst(Uni)
        for fabricSetupPol in value:
            SetupPol = cobra.model.fabric.SetupPol(Inst, **fabricSetupPol)
            self.config.addMo(SetupPol)
            if "fabricSetupP" in fabricSetupPol:
                for fabricSetupP in fabricSetupPol["fabricSetupP"]:
                    SetupP = cobra.model.fabric.SetupP(SetupPol, **fabricSetupP)
                    self.config.addMo(SetupP)

    def fabricRsOosPath(self, value):
        """
        Fabric > RsOosPath
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Inst = cobra.model.fabric.Inst(Uni)
        OOServicePol = cobra.model.fabric.OOServicePol(Inst)
        for fabricRsOosPath in value:
            RsOosPath = cobra.model.fabric.RsOosPath(OOServicePol, **fabricRsOosPath)
            self.config.addMo(RsOosPath)

    def fabricSetupP(self, value):
        """
        Fabric > Inventory > Pod Fabric Setup Policy
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Inst = cobra.model.ctrlr.Inst(Uni)
        SetupPol = cobra.model.fabric.SetupPol(Inst)
        self.config.addMo(SetupPol)
        for fabricSetupP in value:
            SetupP = cobra.model.fabric.SetupP(SetupPol, **fabricSetupP)
            self.config.addMo(SetupP)

    def fabricNodeIdentPol(self, value):
        """
        Fabric > Inventory > Fabric Membership
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Inst = cobra.model.ctrlr.Inst(Uni)
        for fabricNodeIdentPol in value:
            NodeIdentPol = cobra.model.fabric.NodeIdentPol(Inst, **fabricNodeIdentPol)
            self.config.addMo(NodeIdentPol)
            if "fabricNodeIdentP" in fabricNodeIdentPol:
                for fabricNodeIdentPol in fabricNodeIdentPol["fabricNodeIdentP"]:
                    NodeIdentP = cobra.model.fabric.NodeIdentP(NodeIdentPol, **fabricNodeIdentPol)
                    self.config.addMo(NodeIdentP)

    def fabricPodPGrp(self, value):
        """
        Fabric > Fabric Policies > Pods > Policy Groups
        """
        for item in value:
            fabric_inst = cobra.model.fabric.Inst(self.__uni)
            fabric_func_p = cobra.model.fabric.FuncP(fabric_inst)
            mo = cobra.model.fabric.PodPGrp(fabric_func_p, **item)
            if "fabricRtPodPGrp" in item:
                cobra.model.fabric.RtPodPGrp(mo, **item["fabricRtPodPGrp"])
            if "fabricRsSnmpPol" in item:
                cobra.model.fabric.RsSnmpPol(mo, **item["fabricRsSnmpPol"])
            if "fabricRsPodPGrpIsisDomP" in item:
                cobra.model.fabric.RsPodPGrpIsisDomP(mo, **item["fabricRsPodPGrpIsisDomP"])
            if "fabricRsPodPGrpCoopP" in item:
                cobra.model.fabric.RsPodPGrpCoopP(mo, **item["fabricRsPodPGrpCoopP"])
            if "fabricRsPodPGrpBGPRRP" in item:
                cobra.model.fabric.RsPodPGrpBGPRRP(mo, **item["fabricRsPodPGrpBGPRRP"])
            if "fabricRsTimePol" in item:
                cobra.model.fabric.RsTimePol(mo, **item["fabricRsTimePol"])
            if "fabricRsMacsecPol" in item:
                cobra.model.fabric.RsMacsecPol(mo, **item["fabricRsMacsecPol"])
            if "fabricRsCommPol" in item:
                cobra.model.fabric.RsCommPol(mo, **item["fabricRsCommPol"])
            self.config.addMo(mo)

    def fabricPodP(self, value):
        """
        Fabric > Fabric Policies > Pods > Profiles
        """
        for item in value:
            fabric_inst = cobra.model.fabric.Inst(self.__uni)
            mo = cobra.model.fabric.PodP(fabric_inst, **item)
            if "fabricPodS" in item:
                for pod_s in item["fabricPodS"]:
                    mo_pod_s = cobra.model.fabric.PodS(mo, **pod_s)
                    if "fabricRsPodPGrp" in pod_s:
                        cobra.model.fabric.RsPodPGrp(mo_pod_s, **pod_s["fabricRsPodPGrp"])
                    if "fabricPodBlk" in pod_s:
                        cobra.model.fabric.PodBlk(mo_pod_s, **pod_s["fabricPodBlk"])
            self.config.addMo(mo)

    def fabric_switch_leaf_profile(self, value):
        """
        Fabric > Fabric Policies > Switches > Leaf Switches > Profiles
        """
        pass

    def fabric_switch_leaf_policy_group(self, value):
        """
        Fabric > Fabric Policies > Switches > Leaf Switches > Policy Groups
        """
        pass

    def fabric_switch_spine_profile(self, value):
        """
        Fabric > Fabric Policies > Switches > Spine Switches > Profiles
        """
        pass

    def fabric_switch_spine_policy_group(self, value):
        """
        Fabric > Fabric Policies > Switches > Spine Switches > Policy Groups
        """
        pass

    def fabric_module_leaf_profile(self, value):
        """
        Fabric > Fabric Policies > Modules > Leaf Modules > Profiles
        """
        pass

    def fabric_module_leaf_policy_group(self, value):
        """
        Fabric > Fabric Policies > Modules > Leaf Modules > Policy Groups
        """
        pass

    def fabric_module_spine_profile(self, value):
        """
        Fabric > Fabric Policies > Modules > Spine Modules > Profiles
        """
        pass

    def fabric_module_spine_policy_group(self, value):
        """
        Fabric > Fabric Policies > Modules > Spine Modules > Policy Groups
        """
        pass

    def fabric_interface_leaf_profile(self, value):
        """
        Fabric > Fabric Policies > Interfaces > Leaf Interfaces > Profiles
        """
        pass

    def fabric_interface_leaf_policy_group(self, value):
        """
        Fabric > Fabric Policies > Interfaces > Leaf Interfaces > Policy Groups
        """
        pass

    def fabric_interface_spine_profile(self, value):
        """
        Fabric > Fabric Policies > Interfaces > Spine Interfaces > Profiles
        """
        pass

    def fabric_interface_spine_policy_group(self, value):
        """
        Fabric > Fabric Policies > Interfaces > Spine Interfaces > Policy Groups
        """
        pass

    def datetimePol(self, value):
        """
        Fabric > Fabric Policies > Policies > Pod > Date and Time
        """
        Inst = cobra.model.fabric.Inst(self.__uni)
        for datetimePol in value:
            Pol = cobra.model.datetime.Pol(Inst, **datetimePol)
            self.config.addMo(Pol)
            if "datetimeNtpAuthKey" in datetimePol:
                for datetimeNtpAuthKey in datetimePol["datetimeNtpAuthKey"]:
                    if not_nan_str(datetimeNtpAuthKey, ["id", "key", "trusted", "keyType"]):
                        NtpAuthKey = cobra.model.datetime.NtpAuthKey(Pol, **datetimeNtpAuthKey)
                        self.config.addMo(NtpAuthKey)
            if "datetimeNtpProv" in datetimePol:
                for datetimeNtpProv in datetimePol["datetimeNtpProv"]:
                    if not_nan_str(datetimeNtpProv, ["name"]):
                        NtpProv = cobra.model.datetime.NtpProv(Pol, **datetimeNtpProv)
                        self.config.addMo(NtpProv)
                        if "datetimeRsNtpProvToNtpAuthKey" in datetimeNtpProv:
                            for datetimeRsNtpProvToNtpAuthKey in datetimeNtpProv["datetimeRsNtpProvToNtpAuthKey"]:
                                if not_nan_str(datetimeRsNtpProvToNtpAuthKey, ["tnDatetimeNtpAuthKeyId"]):
                                    RsNtpProvToNtpAuthKey = cobra.model.datetime.RsNtpProvToNtpAuthKey(NtpProv, **datetimeRsNtpProvToNtpAuthKey)
                                    self.config.addMo(RsNtpProvToNtpAuthKey)
                        if "datetimeRsNtpProvToEpg" in datetimeNtpProv:
                            if not_nan_str(datetimeNtpProv["datetimeRsNtpProvToEpg"], ["tDn"]):
                                RsNtpProvToEpg = cobra.model.datetime.RsNtpProvToEpg(NtpProv, **datetimeNtpProv["datetimeRsNtpProvToEpg"])
                                self.config.addMo(RsNtpProvToEpg)

    def snmpPol(self, value):
        """
        Fabric > Fabric Policies > Policies > Pod > SNMP
        """
        Inst = cobra.model.fabric.Inst(self.__uni)
        for snmpPol in value:
            if not_nan_str(snmpPol, ["name"]):
                Pol = cobra.model.snmp.Pol(Inst, **snmpPol)
                self.config.addMo(Pol)
                if "snmpClientGrpP" in snmpPol:
                    for snmpClientGrpP in snmpPol["snmpClientGrpP"]:
                        if not_nan_str(snmpClientGrpP, ["name"]):
                            ClientGrpP = cobra.model.snmp.ClientGrpP(Pol, **snmpClientGrpP)
                            if "snmpRsEpg" in snmpClientGrpP:
                                if not_nan_str(snmpClientGrpP["snmpRsEpg"], ["tDn"]):
                                    RsEpg = cobra.model.snmp.RsEpg(ClientGrpP, **snmpClientGrpP["snmpRsEpg"])
                                    self.config.addMo(RsEpg)
                            if "snmpClientP" in snmpClientGrpP:
                                for snmpClientP in snmpClientGrpP["snmpClientP"]:
                                    if not_nan_str(snmpClientP, ["name", "addr"]):
                                        ClientP = cobra.model.snmp.ClientP(ClientGrpP, **snmpClientP)
                                        self.config.addMo(ClientP)
                if "snmpUserP" in snmpPol:
                    for snmpUserP in snmpPol["snmpUserP"]:
                        if not_nan_str(snmpUserP, ["name", "privType", "privKey", "authType", "authKey"]):
                            UserP = cobra.model.snmp.UserP(Pol, **snmpUserP)
                            self.config.addMo(UserP)
                if "snmpCommunityP" in snmpPol:
                    for snmpCommunityP in snmpPol["snmpCommunityP"]:
                        if not_nan_str(snmpCommunityP, ["name"]):
                            CommunityP = cobra.model.snmp.CommunityP(Pol, **snmpCommunityP)
                            self.config.addMo(CommunityP)
                if "snmpTrapFwdServerP" in snmpPol:
                    for snmpTrapFwdServerP in snmpPol["snmpTrapFwdServerP"]:
                        if not_nan_str(snmpTrapFwdServerP, ["addr", "port"]):
                            TrapFwdServerP = cobra.model.snmp.TrapFwdServerP(Pol, **snmpTrapFwdServerP)
                            self.config.addMo(TrapFwdServerP)

    def commPol(self, value):
        """
        Fabric > Fabric Policies > Policies > Pod > Management Access
        """
        Inst = cobra.model.fabric.Inst(self.__uni)
        for commPol in value:
            Pol = cobra.model.comm.Pol(Inst, **commPol)
            self.config.addMo(Pol)
            if "commTelnet" in commPol:
                if not_nan_str(commPol["commTelnet"], ["name", "adminSt"]):
                    Telnet = cobra.model.comm.Telnet(Pol, **commPol["commTelnet"])
                    self.config.addMo(Telnet)
            if "commSsh" in commPol:
                if not_nan_str(commPol["commSsh"], ["name", "adminSt"]):
                    Ssh = cobra.model.comm.Ssh(Pol, **commPol["commSsh"])
                    self.config.addMo(Ssh)
            if "commHttp" in commPol:
                if not_nan_str(commPol["commHttp"], ["name", "adminSt"]):
                    Http = cobra.model.comm.Http(Pol, **commPol["commHttp"])
                    self.config.addMo(Http)
            if "commHttps" in commPol:
                if not_nan_str(commPol["commHttps"], ["name", "adminSt"]):
                    Https = cobra.model.comm.Https(Pol, **commPol["commHttps"])
                    self.config.addMo(Https)
            if "commShellinabox" in commPol:
                if not_nan_str(commPol["commShellinabox"], ["name", "adminSt"]):
                    Shellinabox = cobra.model.comm.Shellinabox(Pol, **commPol["commShellinabox"])
                    self.config.addMo(Shellinabox)

    def fabric_policy_switch_callhome(self, value):
        """
        Fabric > Fabric Policies > Policies > Switch > Callhome Inventory
        """
        pass

    def infraNodeP(self, value):
        """
        Fabric > Access Policies > Switches > Leaf Switches > Profiles
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        for infraNodeP in value:
            NodeP = cobra.model.infra.NodeP(Infra, **infraNodeP)
            self.config.addMo(NodeP)
            if "infraLeafS" in infraNodeP:
                for infraLeafS in infraNodeP["infraLeafS"]:
                    if not_nan_str(infraLeafS, ["name"]):
                        LeafS = cobra.model.infra.LeafS(NodeP, **infraLeafS)
                        self.config.addMo(LeafS)
                        if "infraNodeBlk" in infraLeafS:
                            if not_nan_str(infraLeafS["infraNodeBlk"], ["from_"]):
                                NodeBlk = cobra.model.infra.NodeBlk(LeafS, **infraLeafS["infraNodeBlk"])
                                self.config.addMo(NodeBlk)
                        if "infraRsAccNodePGrp" in infraLeafS:
                            if not_nan_str(infraLeafS["infraRsAccNodePGrp"], ["tDn"]):
                                RsAccNodePGrp = cobra.model.infra.RsAccNodePGrp(LeafS, **infraLeafS["infraRsAccNodePGrp"])
                                self.config.addMo(RsAccNodePGrp)
            if "infraRsAccPortP" in infraNodeP:
                for infraRsAccPortP in infraNodeP["infraRsAccPortP"]:
                    if not_nan_str(infraRsAccPortP, ["tDn"]):
                        RsAccPortP = cobra.model.infra.RsAccPortP(NodeP, **infraRsAccPortP)
                        self.config.addMo(RsAccPortP)

    def infraAccNodePGrp(self, value):
        """
        Fabric > Access Policies > Switches > Leaf Switches > Policy Groups
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        FuncP = cobra.model.infra.FuncP(Infra)
        for infraAccNodePGrp in value:
            AccNodePGrp = cobra.model.infra.AccNodePGrp(FuncP, **infraAccNodePGrp)
            self.config.addMo(AccNodePGrp)
            if "infraRsTopoctrlFwdScaleProfPol" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsTopoctrlFwdScaleProfPol"], ["tnTopoctrlFwdScaleProfilePolName"]):
                    RsTopoctrlFwdScaleProfPol = cobra.model.infra.RsTopoctrlFwdScaleProfPol(AccNodePGrp, **infraAccNodePGrp["infraRsTopoctrlFwdScaleProfPol"])
                    self.config.addMo(RsTopoctrlFwdScaleProfPol)
            if "infraRsLeafTopoctrlUsbConfigProfilePol" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsLeafTopoctrlUsbConfigProfilePol"], ["tnTopoctrlUsbConfigProfilePolName"]):
                    RsLeafTopoctrlUsbConfigProfilePol = cobra.model.infra.RsLeafTopoctrlUsbConfigProfilePol(AccNodePGrp, **infraAccNodePGrp["infraRsLeafTopoctrlUsbConfigProfilePol"])
                    self.config.addMo(RsLeafTopoctrlUsbConfigProfilePol)
            if "infraRsLeafPGrpToLldpIfPol" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsLeafPGrpToLldpIfPol"], ["tnLldpIfPolName"]):
                    RsLeafPGrpToLldpIfPol = cobra.model.infra.RsLeafPGrpToLldpIfPol(AccNodePGrp, **infraAccNodePGrp["infraRsLeafPGrpToLldpIfPol"])
                    self.config.addMo(RsLeafPGrpToLldpIfPol)
            if "infraRsBfdIpv6InstPol" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsBfdIpv6InstPol"], ["tnBfdIpv6InstPolName"]):
                    RsBfdIpv6InstPol = cobra.model.infra.RsBfdIpv6InstPol(AccNodePGrp, **infraAccNodePGrp["infraRsBfdIpv6InstPol"])
                    self.config.addMo(RsBfdIpv6InstPol)
            if "infraRsSynceInstPol" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsSynceInstPol"], ["tnSynceInstPolName"]):
                    RsSynceInstPol = cobra.model.infra.RsSynceInstPol(AccNodePGrp, **infraAccNodePGrp["infraRsSynceInstPol"])
                    self.config.addMo(RsSynceInstPol)
            if "infraRsPoeInstPol" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsPoeInstPol"], ["tnPoeInstPolName"]):
                    RsPoeInstPol = cobra.model.infra.RsPoeInstPol(AccNodePGrp, **infraAccNodePGrp["infraRsPoeInstPol"])
                    self.config.addMo(RsPoeInstPol)
            if "infraRsBfdMhIpv4InstPol" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsBfdMhIpv4InstPol"], ["tnBfdMhIpv4InstPolName"]):
                    RsBfdMhIpv4InstPol = cobra.model.infra.RsBfdMhIpv4InstPol(AccNodePGrp, **infraAccNodePGrp["infraRsBfdMhIpv4InstPol"])
                    self.config.addMo(RsBfdMhIpv4InstPol)
            if "infraRsBfdMhIpv6InstPol" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsBfdMhIpv6InstPol"], ["tnBfdMhIpv6InstPolName"]):
                    RsBfdMhIpv6InstPol = cobra.model.infra.RsBfdMhIpv6InstPol(AccNodePGrp, **infraAccNodePGrp["infraRsBfdMhIpv6InstPol"])
                    self.config.addMo(RsBfdMhIpv6InstPol)
            if "infraRsEquipmentFlashConfigPol" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsEquipmentFlashConfigPol"], ["tnEquipmentFlashConfigPolName"]):
                    RsEquipmentFlashConfigPol = cobra.model.infra.RsEquipmentFlashConfigPol(AccNodePGrp, **infraAccNodePGrp["infraRsEquipmentFlashConfigPol"])
                    self.config.addMo(RsEquipmentFlashConfigPol)
            if "infraRsMonNodeInfraPol" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsMonNodeInfraPol"], ["tnMonInfraPolName"]):
                    RsMonNodeInfraPol = cobra.model.infra.RsMonNodeInfraPol(AccNodePGrp, **infraAccNodePGrp["infraRsMonNodeInfraPol"])
                    self.config.addMo(RsMonNodeInfraPol)
            if "infraRsFcInstPol" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsFcInstPol"], ["tnFcInstPolName"]):
                    RsFcInstPol = cobra.model.infra.RsFcInstPol(AccNodePGrp, **infraAccNodePGrp["infraRsFcInstPol"])
                    self.config.addMo(RsFcInstPol)
            if "infraRsTopoctrlFastLinkFailoverInstPol" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsTopoctrlFastLinkFailoverInstPol"], ["tnTopoctrlFastLinkFailoverInstPolName"]):
                    RsTopoctrlFastLinkFailoverInstPol = cobra.model.infra.RsTopoctrlFastLinkFailoverInstPol(AccNodePGrp, **infraAccNodePGrp["infraRsTopoctrlFastLinkFailoverInstPol"])
                    self.config.addMo(RsTopoctrlFastLinkFailoverInstPol)
            if "infraRsMstInstPol" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsMstInstPol"], ["tnStpInstPolName"]):
                    RsMstInstPol = cobra.model.infra.RsMstInstPol(AccNodePGrp, **infraAccNodePGrp["infraRsMstInstPol"])
                    self.config.addMo(RsMstInstPol)
            if "infraRsFcFabricPol" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsFcFabricPol"], ["tnFcFabricPolName"]):
                    RsFcFabricPol = cobra.model.infra.RsFcFabricPol(AccNodePGrp, **infraAccNodePGrp["infraRsFcFabricPol"])
                    self.config.addMo(RsFcFabricPol)
            if "infraRsLeafCoppProfile" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsLeafCoppProfile"], ["tnCoppLeafProfileName"]):
                    RsLeafCoppProfile = cobra.model.infra.RsLeafCoppProfile(AccNodePGrp, **infraAccNodePGrp["infraRsLeafCoppProfile"])
                    self.config.addMo(RsLeafCoppProfile)
            if "infraRsIaclLeafProfile" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsIaclLeafProfile"], ["tnIaclLeafProfileName"]):
                    RsIaclLeafProfile = cobra.model.infra.RsIaclLeafProfile(AccNodePGrp, **infraAccNodePGrp["infraRsIaclLeafProfile"])
                    self.config.addMo(RsIaclLeafProfile)
            if "infraRsBfdIpv4InstPol" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsBfdIpv4InstPol"], ["tnBfdIpv4InstPolName"]):
                    RsBfdIpv4InstPol = cobra.model.infra.RsBfdIpv4InstPol(AccNodePGrp, **infraAccNodePGrp["infraRsBfdIpv4InstPol"])
                    self.config.addMo(RsBfdIpv4InstPol)
            if "infraRsL2NodeAuthPol" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsL2NodeAuthPol"], ["tnL2NodeAuthPolName"]):
                    RsL2NodeAuthPol = cobra.model.infra.RsL2NodeAuthPol(AccNodePGrp, **infraAccNodePGrp["infraRsL2NodeAuthPol"])
                    self.config.addMo(RsL2NodeAuthPol)
            if "infraRsLeafPGrpToCdpIfPol" in infraAccNodePGrp:
                if not_nan_str(infraAccNodePGrp["infraRsLeafPGrpToCdpIfPol"], ["tnCdpIfPolName"]):
                    RsLeafPGrpToCdpIfPol = cobra.model.infra.RsLeafPGrpToCdpIfPol(AccNodePGrp, **infraAccNodePGrp["infraRsLeafPGrpToCdpIfPol"])
                    self.config.addMo(RsLeafPGrpToCdpIfPol)

    def infraSpineP(self, value):
        """
        Fabric > Access Policies > Switches > Spine Switches > Profiles
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        for infraSpineP in value:
            SpineP = cobra.model.infra.SpineP(Infra, **infraSpineP)
            self.config.addMo(SpineP)
            if "infraSpineS" in infraSpineP:
                for infraSpineS in infraSpineP["infraSpineS"]:
                    SpineS = cobra.model.infra.SpineS(SpineP, **infraSpineS)
                    self.config.addMo(SpineS)
                    if "infraRsSpineAccNodePGrp" in infraSpineS:
                        RsSpineAccNodePGrp = cobra.model.infra.RsSpineAccNodePGrp(SpineS, **infraSpineS["infraRsSpineAccNodePGrp"])
                        self.config.addMo(RsSpineAccNodePGrp)
                    if "infraNodeBlk" in infraSpineS:
                        NodeBlk = cobra.model.infra.NodeBlk(SpineS, **infraSpineS["infraNodeBlk"])
                        self.config.addMo(NodeBlk)
            if "infraRsSpAccPortP" in infraSpineP:
                RsSpAccPortP = cobra.model.infra.RsSpAccPortP(SpineP, **infraSpineP["infraRsSpAccPortP"])
                self.config.addMo(RsSpAccPortP)

    def infraSpineAccNodePGrp(self, value):
        """
        Fabric > Access Policies > Switches > Spine Switches > Policy Groups
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        FuncP = cobra.model.infra.FuncP(Infra)
        for infraSpineAccNodePGrp in value:
            SpineAccNodePGrp = cobra.model.infra.SpineAccNodePGrp(FuncP, **infraSpineAccNodePGrp)
            self.config.addMo(SpineAccNodePGrp)
            if "infraRsSpineCoppProfile" in infraSpineAccNodePGrp:
                RsSpineCoppProfile = cobra.model.infra.RsSpineCoppProfile(SpineAccNodePGrp, **infraSpineAccNodePGrp["infraRsSpineCoppProfile"])
                self.config.addMo(RsSpineCoppProfile)
            if "infraRsSpineBfdIpv4InstPol" in infraSpineAccNodePGrp:
                RsSpineBfdIpv4InstPol = cobra.model.infra.RsSpineBfdIpv4InstPol(SpineAccNodePGrp, **infraSpineAccNodePGrp["infraRsSpineBfdIpv4InstPol"])
                self.config.addMo(RsSpineBfdIpv4InstPol)
            if "infraRsSpineBfdIpv6InstPol" in infraSpineAccNodePGrp:
                RsSpineBfdIpv6InstPol = cobra.model.infra.RsSpineBfdIpv6InstPol(SpineAccNodePGrp, **infraSpineAccNodePGrp["infraRsSpineBfdIpv6InstPol"])
                self.config.addMo(RsSpineBfdIpv6InstPol)
            if "infraRsIaclSpineProfile" in infraSpineAccNodePGrp:
                RsIaclSpineProfile = cobra.model.infra.RsIaclSpineProfile(SpineAccNodePGrp, **infraSpineAccNodePGrp["infraRsIaclSpineProfile"])
                self.config.addMo(RsIaclSpineProfile)
            if "infraRsSpinePGrpToCdpIfPol" in infraSpineAccNodePGrp:
                RsSpinePGrpToCdpIfPol = cobra.model.infra.RsSpinePGrpToCdpIfPol(SpineAccNodePGrp, **infraSpineAccNodePGrp["infraRsSpinePGrpToCdpIfPol"])
                self.config.addMo(RsSpinePGrpToCdpIfPol)
            if "infraRsSpinePGrpToLldpIfPol" in infraSpineAccNodePGrp:
                RsSpinePGrpToLldpIfPol = cobra.model.infra.RsSpinePGrpToLldpIfPol(SpineAccNodePGrp, **infraSpineAccNodePGrp["infraRsSpinePGrpToLldpIfPol"])
                self.config.addMo(RsSpinePGrpToLldpIfPol)

    def infraSpAccPortP(self, value):
        """
        Fabric > Access Policies > Interfaces > Spine Interfaces > Profiles
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        for infraSpAccPortP in value:
            SpAccPortP = cobra.model.infra.SpAccPortP(Infra, **infraSpAccPortP)
            self.config.addMo(SpAccPortP)
            if "infraSHPortS" in infraSpAccPortP:
                for infraSHPortS in infraSpAccPortP["infraSHPortS"]:
                    SHPortS = cobra.model.infra.SHPortS(SpAccPortP, **infraSHPortS)
                    self.config.addMo(SHPortS)
                    if "infraRsSpAccGrp" in infraSHPortS:
                        RsSpAccGrp = cobra.model.infra.RsSpAccGrp(SHPortS, **infraSHPortS["infraRsSpAccGrp"])
                        self.config.addMo(RsSpAccGrp)
                    if "infraPortBlk" in infraSHPortS:
                        for infraPortBlk in infraSHPortS["infraPortBlk"]:
                            PortBlk = cobra.model.infra.PortBlk(SHPortS, **infraPortBlk)
                            self.config.addMo(PortBlk)

    def infraSpAccPortGrp(self, value):
        """
        Fabric > Access Policies > Interfaces > Spine Interfaces > Policy Groups
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        FuncP = cobra.model.infra.FuncP(Infra)
        for infraSpAccPortGrp in value:
            SpAccPortGrp = cobra.model.infra.SpAccPortGrp(FuncP, **infraSpAccPortGrp)
            self.config.addMo(SpAccPortGrp)
            if "infraRsHIfPol" in infraSpAccPortGrp:
                RsHIfPol = cobra.model.infra.RsHIfPol(SpAccPortGrp, **infraSpAccPortGrp["infraRsHIfPol"])
                self.config.addMo(RsHIfPol)
            if "infraRsCdpIfPol" in infraSpAccPortGrp:
                RsCdpIfPol = cobra.model.infra.RsCdpIfPol(SpAccPortGrp, **infraSpAccPortGrp["infraRsCdpIfPol"])
                self.config.addMo(RsCdpIfPol)
            if "infraRsMacsecIfPol" in infraSpAccPortGrp:
                RsMacsecIfPol = cobra.model.infra.RsMacsecIfPol(SpAccPortGrp, **infraSpAccPortGrp["infraRsMacsecIfPol"])
                self.config.addMo(RsMacsecIfPol)
            if "infraRsAttEntP" in infraSpAccPortGrp:
                RsAttEntP = cobra.model.infra.RsAttEntP(SpAccPortGrp, **infraSpAccPortGrp["infraRsAttEntP"])
                self.config.addMo(RsAttEntP)
            if "infraRsLinkFlapPol" in infraSpAccPortGrp:
                RsLinkFlapPol = cobra.model.infra.RsLinkFlapPol(SpAccPortGrp, **infraSpAccPortGrp["infraRsLinkFlapPol"])
                self.config.addMo(RsLinkFlapPol)
            if "infraRsCoppIfPol" in infraSpAccPortGrp:
                RsCoppIfPol = cobra.model.infra.RsCoppIfPol(SpAccPortGrp, **infraSpAccPortGrp["infraRsCoppIfPol"])
                self.config.addMo(RsCoppIfPol)

    def infraAccPortP(self, value):
        """
        Fabric > Access Policies > Interfaces > Leaf Interfaces > Profiles
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        for infraAccPortP in value:
            AccPortP = cobra.model.infra.AccPortP(Infra, **infraAccPortP)
            self.config.addMo(AccPortP)
            if "infraHPortS" in infraAccPortP:
                for infraHPortS in infraAccPortP["infraHPortS"]:
                    HPortS = cobra.model.infra.HPortS(AccPortP, **infraHPortS)
                    self.config.addMo(HPortS)
                    if "infraRsAccBaseGrp" in infraHPortS:
                        if not_nan_str(infraHPortS["infraRsAccBaseGrp"], ["tDn"]):
                            RsAccBaseGrp = cobra.model.infra.RsAccBaseGrp(HPortS, **infraHPortS["infraRsAccBaseGrp"])
                            self.config.addMo(RsAccBaseGrp)
                    if "infraPortBlk" in infraHPortS:
                        for infraPortBlk in infraHPortS["infraPortBlk"]:
                            if not_nan_str(infraPortBlk, ["fromPort"]):
                                PortBlk = cobra.model.infra.PortBlk(HPortS, **infraPortBlk)
                                self.config.addMo(PortBlk)

    def infraFexP(self, value):
        """
        Fabric > Access Policies > Interfaces > Leaf Interfaces > FEX Profiles
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        for infraFexP in value:
            FexP = cobra.model.infra.FexP(Infra, **infraFexP)
            self.config.addMo(FexP)
            if "infraHPortS" in infraFexP:
                for infraHPortS in infraFexP["infraHPortS"]:
                    HPortS = cobra.model.infra.HPortS(FexP, **infraHPortS)
                    self.config.addMo(HPortS)
                    if "infraRsAccBaseGrp" in infraHPortS:
                        RsAccBaseGrp = cobra.model.infra.RsAccBaseGrp(HPortS, **infraHPortS["infraRsAccBaseGrp"])
                        self.config.addMo(RsAccBaseGrp)
                    if "infraPortBlk" in infraHPortS:
                        for block in infraHPortS["infraPortBlk"]:
                            PortBlk = cobra.model.infra.PortBlk(HPortS, **block)
                            self.config.addMo(PortBlk)
            if "infraFexBndlGrp" in infraFexP:
                FexBndlGrp = cobra.model.infra.FexBndlGrp(FexP, **infraFexP["infraFexBndlGrp"])
                self.config.addMo(FexBndlGrp)

    def infraAccPortGrp(self, value):
        """
        Fabric > Access Policies > Interfaces > Leaf Interfaces > Policy Groups > Access
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        FuncP = cobra.model.infra.FuncP(Infra)
        for infraAccPortGrp in value:
            AccPortGrp = cobra.model.infra.AccPortGrp(FuncP, **infraAccPortGrp)
            self.config.addMo(AccPortGrp)
            if "infraRsAttEntP" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsAttEntP"], ["tDn"]):
                    RsAttEntP = cobra.model.infra.RsAttEntP(AccPortGrp, **infraAccPortGrp["infraRsAttEntP"])
                    self.config.addMo(RsAttEntP)
            if "infraRsStpIfPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsStpIfPol"], ["tnStpIfPolName"]):
                    RsStpIfPol = cobra.model.infra.RsStpIfPol(AccPortGrp, **infraAccPortGrp["infraRsStpIfPol"])
                    self.config.addMo(RsStpIfPol)
            if "infraRsQosLlfcIfPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsQosLlfcIfPol"], ["tnQosLlfcIfPolName"]):
                    RsQosLlfcIfPol = cobra.model.infra.RsQosLlfcIfPol(AccPortGrp, **infraAccPortGrp["infraRsQosLlfcIfPol"])
                    self.config.addMo(RsQosLlfcIfPol)
            if "infraRsQosIngressDppIfPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsQosIngressDppIfPol"], ["tnQosDppPolName"]):
                    RsQosIngressDppIfPol = cobra.model.infra.RsQosIngressDppIfPol(AccPortGrp, **infraAccPortGrp["infraRsQosIngressDppIfPol"])
                    self.config.addMo(RsQosIngressDppIfPol)
            if "infraRsStormctrlIfPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsStormctrlIfPol"], ["tnStormctrlIfPolName"]):
                    RsStormctrlIfPol = cobra.model.infra.RsStormctrlIfPol(AccPortGrp, **infraAccPortGrp["infraRsStormctrlIfPol"])
                    self.config.addMo(RsStormctrlIfPol)
            if "infraRsQosEgressDppIfPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsQosEgressDppIfPol"], ["tnQosDppPolName"]):
                    RsQosEgressDppIfPol = cobra.model.infra.RsQosEgressDppIfPol(AccPortGrp, **infraAccPortGrp["infraRsQosEgressDppIfPol"])
                    self.config.addMo(RsQosEgressDppIfPol)
            if "infraRsMonIfInfraPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsMonIfInfraPol"], ["tnMonInfraPolName"]):
                    RsMonIfInfraPol = cobra.model.infra.RsMonIfInfraPol(AccPortGrp, **infraAccPortGrp["infraRsMonIfInfraPol"])
                    self.config.addMo(RsMonIfInfraPol)
            if "infraRsMcpIfPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsMcpIfPol"], ["tnMcpIfPolName"]):
                    RsMcpIfPol = cobra.model.infra.RsMcpIfPol(AccPortGrp, **infraAccPortGrp["infraRsMcpIfPol"])
                    self.config.addMo(RsMcpIfPol)
            if "infraRsMacsecIfPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsMacsecIfPol"], ["tnMacsecIfPolName"]):
                    RsMacsecIfPol = cobra.model.infra.RsMacsecIfPol(AccPortGrp, **infraAccPortGrp["infraRsMacsecIfPol"])
                    self.config.addMo(RsMacsecIfPol)
            if "infraRsQosSdIfPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsQosSdIfPol"], ["tnQosSdIfPolName"]):
                    RsQosSdIfPol = cobra.model.infra.RsQosSdIfPol(AccPortGrp, **infraAccPortGrp["infraRsQosSdIfPol"])
                    self.config.addMo(RsQosSdIfPol)
            if "infraRsCdpIfPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsCdpIfPol"], ["tnCdpIfPolName"]):
                    RsCdpIfPol = cobra.model.infra.RsCdpIfPol(AccPortGrp, **infraAccPortGrp["infraRsCdpIfPol"])
                    self.config.addMo(RsCdpIfPol)
            if "infraRsL2IfPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsL2IfPol"], ["tnL2IfPolName"]):
                    RsL2IfPol = cobra.model.infra.RsL2IfPol(AccPortGrp, **infraAccPortGrp["infraRsL2IfPol"])
                    self.config.addMo(RsL2IfPol)
            if "infraRsQosDppIfPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsQosDppIfPol"], ["tnQosDppPolName"]):
                    RsQosDppIfPol = cobra.model.infra.RsQosDppIfPol(AccPortGrp, **infraAccPortGrp["infraRsQosDppIfPol"])
                    self.config.addMo(RsQosDppIfPol)
            if "infraRsCoppIfPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsCoppIfPol"], ["tnCoppIfPolName"]):
                    RsCoppIfPol = cobra.model.infra.RsCoppIfPol(AccPortGrp, **infraAccPortGrp["infraRsCoppIfPol"])
                    self.config.addMo(RsCoppIfPol)
            if "infraRsDwdmIfPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsDwdmIfPol"], ["tnDwdmIfPolName"]):
                    RsDwdmIfPol = cobra.model.infra.RsDwdmIfPol(AccPortGrp, **infraAccPortGrp["infraRsDwdmIfPol"])
                    self.config.addMo(RsDwdmIfPol)
            if "infraRsLinkFlapPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsLinkFlapPol"], ["tnFabricLinkFlapPolName"]):
                    RsLinkFlapPol = cobra.model.infra.RsLinkFlapPol(AccPortGrp, **infraAccPortGrp["infraRsLinkFlapPol"])
                    self.config.addMo(RsLinkFlapPol)
            if "infraRsLldpIfPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsLldpIfPol"], ["tnLldpIfPolName"]):
                    RsLldpIfPol = cobra.model.infra.RsLldpIfPol(AccPortGrp, **infraAccPortGrp["infraRsLldpIfPol"])
                    self.config.addMo(RsLldpIfPol)
            if "infraRsFcIfPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsFcIfPol"], ["tnFcIfPolName"]):
                    RsFcIfPol = cobra.model.infra.RsFcIfPol(AccPortGrp, **infraAccPortGrp["infraRsFcIfPol"])
                    self.config.addMo(RsFcIfPol)
            if "infraRsQosPfcIfPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsQosPfcIfPol"], ["tnQosPfcIfPolName"]):
                    RsQosPfcIfPol = cobra.model.infra.RsQosPfcIfPol(AccPortGrp, **infraAccPortGrp["infraRsQosPfcIfPol"])
                    self.config.addMo(RsQosPfcIfPol)
            if "infraRsHIfPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsHIfPol"], ["tnFabricHIfPolName"]):
                    RsHIfPol = cobra.model.infra.RsHIfPol(AccPortGrp, **infraAccPortGrp["infraRsHIfPol"])
                    self.config.addMo(RsHIfPol)
            if "infraRsL2PortSecurityPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsL2PortSecurityPol"], ["tnL2PortSecurityPolName"]):
                    RsL2PortSecurityPol = cobra.model.infra.RsL2PortSecurityPol(AccPortGrp, **infraAccPortGrp["infraRsL2PortSecurityPol"])
                    self.config.addMo(RsL2PortSecurityPol)
            if "infraRsL2PortAuthPol" in infraAccPortGrp:
                if not_nan_str(infraAccPortGrp["infraRsL2PortAuthPol"], ["tnL2PortAuthPolName"]):
                    RsL2PortAuthPol = cobra.model.infra.RsL2PortAuthPol(AccPortGrp, **infraAccPortGrp["infraRsL2PortAuthPol"])
                    self.config.addMo(RsL2PortAuthPol)

    def infraAccBndlGrp(self, value):
        """
        Fabric > Access Policies > Interfaces > Leaf Interfaces > Policy Groups > PC or VPC
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        FuncP = cobra.model.infra.FuncP(Infra)
        for infraAccBndlGrp in value:
            AccBndlGrp = cobra.model.infra.AccBndlGrp(FuncP, **infraAccBndlGrp)
            self.config.addMo(AccBndlGrp)
            if "infraRsAttEntP" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsAttEntP"], ["tDn"]):
                    RsAttEntP = cobra.model.infra.RsAttEntP(AccBndlGrp, **infraAccBndlGrp["infraRsAttEntP"])
                    self.config.addMo(RsAttEntP)
            if "infraRsStpIfPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsStpIfPol"], ["tnStpIfPolName"]):
                    RsStpIfPol = cobra.model.infra.RsStpIfPol(AccBndlGrp, **infraAccBndlGrp["infraRsStpIfPol"])
                    self.config.addMo(RsStpIfPol)
            if "infraRsQosLlfcIfPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsQosLlfcIfPol"], ["tnQosLlfcIfPolName"]):
                    RsQosLlfcIfPol = cobra.model.infra.RsQosLlfcIfPol(AccBndlGrp, **infraAccBndlGrp["infraRsQosLlfcIfPol"])
                    self.config.addMo(RsQosLlfcIfPol)
            if "infraRsQosIngressDppIfPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsQosIngressDppIfPol"], ["tnQosDppPolName"]):
                    RsQosIngressDppIfPol = cobra.model.infra.RsQosIngressDppIfPol(AccBndlGrp, **infraAccBndlGrp["infraRsQosIngressDppIfPol"])
                    self.config.addMo(RsQosIngressDppIfPol)
            if "infraRsStormctrlIfPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsStormctrlIfPol"], ["tnStormctrlIfPolName"]):
                    RsStormctrlIfPol = cobra.model.infra.RsStormctrlIfPol(AccBndlGrp, **infraAccBndlGrp["infraRsStormctrlIfPol"])
                    self.config.addMo(RsStormctrlIfPol)
            if "infraRsQosEgressDppIfPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsQosEgressDppIfPol"], ["tnQosDppPolName"]):
                    RsQosEgressDppIfPol = cobra.model.infra.RsQosEgressDppIfPol(AccBndlGrp, **infraAccBndlGrp["infraRsQosEgressDppIfPol"])
                    self.config.addMo(RsQosEgressDppIfPol)
            if "infraRsMonIfInfraPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsMonIfInfraPol"], ["tnMonInfraPolName"]):
                    RsMonIfInfraPol = cobra.model.infra.RsMonIfInfraPol(AccBndlGrp, **infraAccBndlGrp["infraRsMonIfInfraPol"])
                    self.config.addMo(RsMonIfInfraPol)
            if "infraRsMcpIfPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsMcpIfPol"], ["tnMcpIfPolName"]):
                    RsMcpIfPol = cobra.model.infra.RsMcpIfPol(AccBndlGrp, **infraAccBndlGrp["infraRsMcpIfPol"])
                    self.config.addMo(RsMcpIfPol)
            if "infraRsMacsecIfPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsMacsecIfPol"], ["tnMacsecIfPolName"]):
                    RsMacsecIfPol = cobra.model.infra.RsMacsecIfPol(AccBndlGrp, **infraAccBndlGrp["infraRsMacsecIfPol"])
                    self.config.addMo(RsMacsecIfPol)
            if "infraRsQosSdIfPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsQosSdIfPol"], ["tnQosSdIfPolName"]):
                    RsQosSdIfPol = cobra.model.infra.RsQosSdIfPol(AccBndlGrp, **infraAccBndlGrp["infraRsQosSdIfPol"])
                    self.config.addMo(RsQosSdIfPol)
            if "infraRsCdpIfPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsCdpIfPol"], ["tnCdpIfPolName"]):
                    RsCdpIfPol = cobra.model.infra.RsCdpIfPol(AccBndlGrp, **infraAccBndlGrp["infraRsCdpIfPol"])
                    self.config.addMo(RsCdpIfPol)
            if "infraRsL2IfPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsL2IfPol"], ["tnL2IfPolName"]):
                    RsL2IfPol = cobra.model.infra.RsL2IfPol(AccBndlGrp, **infraAccBndlGrp["infraRsL2IfPol"])
                    self.config.addMo(RsL2IfPol)
            if "infraRsQosDppIfPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsQosDppIfPol"], ["tnQosDppPolName"]):
                    RsQosDppIfPol = cobra.model.infra.RsQosDppIfPol(AccBndlGrp, **infraAccBndlGrp["infraRsQosDppIfPol"])
                    self.config.addMo(RsQosDppIfPol)
            if "infraRsCoppIfPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsCoppIfPol"], ["tnCoppIfPolName"]):
                    RsCoppIfPol = cobra.model.infra.RsCoppIfPol(AccBndlGrp, **infraAccBndlGrp["infraRsCoppIfPol"])
                    self.config.addMo(RsCoppIfPol)
            if "infraRsLldpIfPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsLldpIfPol"], ["tnLldpIfPolName"]):
                    RsLldpIfPol = cobra.model.infra.RsLldpIfPol(AccBndlGrp, **infraAccBndlGrp["infraRsLldpIfPol"])
                    self.config.addMo(RsLldpIfPol)
            if "infraRsFcIfPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsFcIfPol"], ["tnFcIfPolName"]):
                    RsFcIfPol = cobra.model.infra.RsFcIfPol(AccBndlGrp, **infraAccBndlGrp["infraRsFcIfPol"])
                    self.config.addMo(RsFcIfPol)
            if "infraRsQosPfcIfPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsQosPfcIfPol"], ["tnQosPfcIfPolName"]):
                    RsQosPfcIfPol = cobra.model.infra.RsQosPfcIfPol(AccBndlGrp, **infraAccBndlGrp["infraRsQosPfcIfPol"])
                    self.config.addMo(RsQosPfcIfPol)
            if "infraRsHIfPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsHIfPol"], ["tnFabricHIfPolName"]):
                    RsHIfPol = cobra.model.infra.RsHIfPol(AccBndlGrp, **infraAccBndlGrp["infraRsHIfPol"])
                    self.config.addMo(RsHIfPol)
            if "infraRsL2PortSecurityPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsL2PortSecurityPol"], ["tnL2PortSecurityPolName"]):
                    RsL2PortSecurityPol = cobra.model.infra.RsL2PortSecurityPol(AccBndlGrp, **infraAccBndlGrp["infraRsL2PortSecurityPol"])
                    self.config.addMo(RsL2PortSecurityPol)
            if "infraRsL2PortAuthPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsL2PortAuthPol"], ["tnL2PortAuthPolName"]):
                    RsL2PortAuthPol = cobra.model.infra.RsL2PortAuthPol(AccBndlGrp, **infraAccBndlGrp["infraRsL2PortAuthPol"])
                    self.config.addMo(RsL2PortAuthPol)
            if "infraRsLacpPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsLacpPol"], ["tnLacpLagPolName"]):
                    RsLacpPol = cobra.model.infra.RsLacpPol(AccBndlGrp, **infraAccBndlGrp["infraRsLacpPol"])
                    self.config.addMo(RsLacpPol)
            if "infraRsLinkFlapPol" in infraAccBndlGrp:
                if not_nan_str(infraAccBndlGrp["infraRsLinkFlapPol"], ["tnFabricLinkFlapPolName"]):
                    RsLinkFlapPol = cobra.model.infra.RsLinkFlapPol(AccBndlGrp, **infraAccBndlGrp["infraRsLinkFlapPol"])
                    self.config.addMo(RsLinkFlapPol)

    def fabricProtPol(self, value):
        """
        Fabric > Access Policies > Policies > Switch > Virtual Port Channel default
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Inst = cobra.model.fabric.Inst(Uni)
        for fabricProtPol in value:
            ProtPol = cobra.model.fabric.ProtPol(Inst, **fabricProtPol)
            self.config.addMo(ProtPol)
            if "fabricExplicitGEp" in fabricProtPol:
                for fabricExplicitGEp in fabricProtPol["fabricExplicitGEp"]:
                    ExplicitGEp = cobra.model.fabric.ExplicitGEp(ProtPol, **fabricExplicitGEp)
                    self.config.addMo(ExplicitGEp)
                    if "fabricRsVpcInstPol" in fabricExplicitGEp:
                        RsVpcInstPol = cobra.model.fabric.RsVpcInstPol(ExplicitGEp, **fabricExplicitGEp["fabricRsVpcInstPol"])
                        self.config.addMo(RsVpcInstPol)
                    if "fabricNodePEp" in fabricExplicitGEp:
                        for fabricNodePEp in fabricExplicitGEp["fabricNodePEp"]:
                            NodePEp = cobra.model.fabric.NodePEp(ExplicitGEp, **fabricNodePEp)
                            self.config.addMo(NodePEp)

    def fabricHIfPol(self, value):
        """
        Fabric > Access Policies > Policies > Interface > Link Level
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        for fabricHIfPol in value:
            HIfPol = cobra.model.fabric.HIfPol(Infra, **fabricHIfPol)
            self.config.addMo(HIfPol)

    def qosPfcIfPol(self, value):
        """
        Fabric > Access Policies > Policies > Interface > Priority Flow Control
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        for qosPfcIfPol in value:
            PfcIfPol = cobra.model.qos.PfcIfPol(Infra, **qosPfcIfPol)
            self.config.addMo(PfcIfPol)

    def cdpIfPol(self, value):
        """
        Fabric > Access Policies > Policies > Interface > CDP Interface
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        for cdpIfPol in value:
            IfPol = cobra.model.cdp.IfPol(Infra, **cdpIfPol)
            self.config.addMo(IfPol)

    def lldpIfPol(self, value):
        """
        Fabric > Access Policies > Policies > Interface > LLDP Interface
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        for lldpIfPol in value:
            IfPol = cobra.model.lldp.IfPol(Infra, **lldpIfPol)
            self.config.addMo(IfPol)

    def lacpLagPol(self, value):
        """
        Fabric > Access Policies > Policies > Interface > Port Channel
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        for lacpLagPol in value:
            LagPol = cobra.model.lacp.LagPol(Infra, **lacpLagPol)
            self.config.addMo(LagPol)

    def stpIfPol(self, value) -> None:
        """
        Fabric > Access Policies > Policies > Interface > Spanning Tree Interface
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        for stpIfPol in value:
            IfPol = cobra.model.stp.IfPol(Infra, **stpIfPol)
            self.config.addMo(IfPol)

    def stormctrlIfPol(self, value) -> None:
        """
        Fabric > Access Policies > Policies > Interface > Storm Control
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        for stormctrlIfPol in value:
            IfPol = cobra.model.stormctrl.IfPol(Infra, **stormctrlIfPol)
            self.config.addMo(IfPol)

    def mcpIfPol(self, value):
        """
        Fabric > Access Policies > Policies > Interface > MCP Interface
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        for mcpIfPol in value:
            IfPol = cobra.model.mcp.IfPol(Infra, **mcpIfPol)
            self.config.addMo(IfPol)

    def infraAttEntityP(self, value):
        """
        Fabric > Access Policies > Policies > Global > Attachable Access Entity Profiles
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        for infraAttEntityP in value:
            AttEntityP = cobra.model.infra.AttEntityP(Infra, **infraAttEntityP)
            self.config.addMo(AttEntityP)
            if "infraRsDomP" in infraAttEntityP:
                for infraRsDomP in infraAttEntityP["infraRsDomP"]:
                    RsDomP = cobra.model.infra.RsDomP(AttEntityP, **infraRsDomP)
                    self.config.addMo(RsDomP)

    def fvnsVlanInstP(self, value):
        """
        Fabric > Access Policies > Pools > VLAN
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        for fvnsVlanInstP in value:
            VlanInstP = cobra.model.fvns.VlanInstP(Infra, **fvnsVlanInstP)
            self.config.addMo(VlanInstP)
            if "fvnsEncapBlk" in fvnsVlanInstP:
                for fvnsEncapBlk in fvnsVlanInstP["fvnsEncapBlk"]:
                    EncapBlk = cobra.model.fvns.EncapBlk(VlanInstP, **fvnsEncapBlk)
                    self.config.addMo(EncapBlk)

    def physDomP(self, value):
        """
        Fabric > Access Policies > Physical and External Domains > Physical Domain
        """
        Uni = cobra.model.pol.Uni(self.__root)
        for physDomP in value:
            DomP = cobra.model.phys.DomP(Uni, **physDomP)
            self.config.addMo(DomP)
            if "infraRsVlanNs" in physDomP:
                RsVlanNs = cobra.model.infra.RsVlanNs(DomP, **physDomP["infraRsVlanNs"])
                self.config.addMo(RsVlanNs)

    def l3extDomP(self, value):
        """
        Fabric > Access Policies > Physical and External Domains > L3 Domains
        """
        Uni = cobra.model.pol.Uni(self.__root)
        for l3extDomP in value:
            DomP = cobra.model.l3ext.DomP(Uni, **l3extDomP)
            self.config.addMo(DomP)
            if "infraRsVlanNs" in l3extDomP:
                RsVlanNs = cobra.model.infra.RsVlanNs(DomP, **l3extDomP["infraRsVlanNs"])
                self.config.addMo(RsVlanNs)

    def l2extDomP(self, value):
        """
        Fabric > Access Policies > Physical and External Domains > External Bridged Domains
        """
        Uni = cobra.model.pol.Uni(self.__root)
        for l2extDomP in value:
            DomP = cobra.model.l2ext.DomP(Uni, **l2extDomP)
            self.config.addMo(DomP)
            if "infraRsVlanNs" in l2extDomP:
                RsVlanNs = cobra.model.infra.RsVlanNs(DomP, **l2extDomP["infraRsVlanNs"])
                self.config.addMo(RsVlanNs)

    def bgpInstPol(self, value) -> None:
        """
        System Settings > All Tenants
        """
        Inst = cobra.model.fabric.Inst(self.__uni)
        for bgpInstPol in value:
            InstPol = cobra.model.bgp.InstPol(Inst, **bgpInstPol)
            self.config.addMo(InstPol)
            if "bgpAsP" in bgpInstPol:
                if not_nan_str(bgpInstPol["bgpAsP"], ["asn"]):
                    AsP = cobra.model.bgp.AsP(InstPol, **bgpInstPol["bgpAsP"])
                    self.config.addMo(AsP)
            if "bgpRRP" in bgpInstPol:
                RRP = cobra.model.bgp.RRP(InstPol)
                self.config.addMo(RRP)
                for bgpRRP in bgpInstPol["bgpRRP"]:
                    if "bgpRRNodePEp" in bgpRRP:
                        RRNodePEp = cobra.model.bgp.RRNodePEp(RRP, **bgpRRP["bgpRRNodePEp"])
                        self.config.addMo(RRNodePEp)
            if "ExtRRP" in bgpInstPol:
                ExtRRP = cobra.model.bgp.ExtRRP(InstPol)
                for ExtRRP in bgpInstPol["ExtRRP"]:
                    RRNodePEp = cobra.model.bgp.RRNodePEp(ExtRRP, **ExtRRP)
                    self.config.addMo(RRNodePEp)

    def coopPol(self, value) -> None:
        """
        System Settings > COOP Group
        """
        Inst = cobra.model.fabric.Inst(self.__uni)
        for coopPol in value:
            Pol = cobra.model.coop.Pol(Inst, **coopPol)
            self.config.addMo(Pol)

    def datetimeFormat(self, value) -> None:
        """
        System Settings > Date and Time
        """
        Inst = cobra.model.fabric.Inst(self.__uni)
        for datetimeFormat in value:
            Format = cobra.model.datetime.Format(Inst, **datetimeFormat)
            self.config.addMo(Format)

    def aaaFabricSec(self, value) -> None:
        """
        System Settings > Fabric Security
        """
        UserEp = cobra.model.aaa.UserEp(self.__uni)
        for aaaFabricSec in value:
            FabricSec = cobra.model.aaa.FabricSec(UserEp, **aaaFabricSec)
            self.config.addMo(FabricSec)

    def aaaPreLoginBanner(self, value) -> None:
        """
        System Settings > System Alias and Banners
        """
        UserEp = cobra.model.aaa.UserEp(self.__uni)
        for aaaPreLoginBanner in value:
            PreLoginBanner = cobra.model.aaa.PreLoginBanner(UserEp, **aaaPreLoginBanner)
            self.config.addMo(PreLoginBanner)

    def pkiExportEncryptionKey(self, value) -> None:
        """
        System Settings > Fabric Security
        """
        for pkiExportEncryptionKey in value:
            ExportEncryptionKey = cobra.model.pki.ExportEncryptionKey(self.__uni, **pkiExportEncryptionKey)
            self.config.addMo(ExportEncryptionKey)

    def epLoopProtectP(self, value) -> None:
        """
        System Settings > Enpoint Controls > The endpoint loop protection
        """
        Infra = cobra.model.infra.Infra(self.__uni)
        for epLoopProtectP in value:
            LoopProtectP = cobra.model.ep.LoopProtectP(Infra, **epLoopProtectP)
            self.config.addMo(LoopProtectP)

    def epControlP(self, value) -> None:
        """
        System Settings > Enpoint Controls > Rogue EP Control
        """
        Infra = cobra.model.infra.Infra(self.__uni)
        for epControlP in value:
            ControlP = cobra.model.ep.ControlP(Infra, **epControlP)
            self.config.addMo(ControlP)

    def epIpAgingP(self, value) -> None:
        """
        System Settings > Enpoint Controls > IP Aging
        """
        Infra = cobra.model.infra.Infra(self.__uni)
        for epIpAgingP in value:
            IpAgingP = cobra.model.ep.IpAgingP(Infra, **epIpAgingP)
            self.config.addMo(IpAgingP)

    def infraSetPol(self, value) -> None:
        """
        System Settings > Fabric-Wide Settings
        """
        Infra = cobra.model.infra.Infra(self.__uni)
        for infraSetPol in value:
            SetPol = cobra.model.infra.SetPol(Infra, **infraSetPol)
            self.config.addMo(SetPol)

    def isisDomPol(self, value) -> None:
        """
        System Settings > ISIS Policy
        """
        Inst = cobra.model.fabric.Inst(self.__uni)
        for isisDomPol in value:
            DomPol = cobra.model.isis.DomPol(Inst, **isisDomPol)
            self.config.addMo(DomPol)

    def infraPortTrackPol(self, value) -> None:
        """
        System Settings > Port Tracking
        """
        Infra = cobra.model.infra.Infra(self.__uni)
        for infraPortTrackPol in value:
            PortTrackPol = cobra.model.infra.PortTrackPol(Infra, **infraPortTrackPol)
            self.config.addMo(PortTrackPol)

    def mcpInstPol(self, value) -> None:
        """
        Fabric > Access Policies > Global > MCP Instance Policy default
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        for mcpInstPol in value:
            InstPol = cobra.model.mcp.InstPol(Infra, **mcpInstPol)
            self.config.addMo(InstPol)

    def fabricNodeControl(self, value) -> None:
        """
        Fabric > Fabric Policies > Policies > Monitoring > Fabric Node Controls > default
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Inst = cobra.model.fabric.Inst(Uni)
        for fabricNodeControl in value:
            NodeControl = cobra.model.fabric.NodeControl(Inst, **fabricNodeControl)
            self.config.addMo(NodeControl)

    def geoSite(self, value) -> None:
        """
        Fabric > Fabric Policies > Policies > Geolocation
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Inst = cobra.model.fabric.Inst(Uni)
        for geoSite in value:
            Site = cobra.model.geo.Site(Inst, **geoSite)
            self.config.addMo(Site)
            if "geoBuilding" in geoSite:
                for geoBuilding in geoSite["geoBuilding"]:
                    Building = cobra.model.geo.Building(Site, **geoBuilding)
                    self.config.addMo(Building)
                    if "geoFloor" in geoBuilding:
                        for geoFloor in geoBuilding["geoFloor"]:
                            Floor = cobra.model.geo.Floor(Building, **geoFloor)
                            self.config.addMo(Floor)
                            if "geoRoom" in geoFloor:
                                for geoRoom in geoFloor["geoRoom"]:
                                    Room = cobra.model.geo.Room(Floor, **geoRoom)
                                    self.config.addMo(Room)
                                    if "geoRow" in geoRoom:
                                        for geoRow in geoRoom["geoRow"]:
                                            Row = cobra.model.geo.Row(Room, **geoRow)
                                            self.config.addMo(Row)
                                            if "geoRack" in geoRow:
                                                for geoRack in geoRow["geoRack"]:
                                                    if not_nan_str(geoRack, ["name"]):
                                                        Rack = cobra.model.geo.Rack(Row, **geoRack)
                                                        self.config.addMo(Rack)
                                                        if "geoRsNodeLocation" in geoRack:
                                                            for geoRsNodeLocation in geoRack["geoRsNodeLocation"]:
                                                                if not_nan_str(geoRsNodeLocation, ["tDn"]):
                                                                    RsNodeLocation = cobra.model.geo.RsNodeLocation(Rack, **geoRsNodeLocation)
                                                                    self.config.addMo(RsNodeLocation)

    def latencyPtpMode(self, value) -> None:
        """
        Fabric > Fabric Policies > Policies > Monitoring > Fabric Node Controls > default
        """
        Inst = cobra.model.fabric.Inst(self.__uni)
        for latencyPtpMode in value:
            PtpMode = cobra.model.latency.PtpMode(Inst, **latencyPtpMode)
            self.config.addMo(PtpMode)

    def infrazoneZoneP(self, value) -> None:
        """
        Fabric > Fabric Policies > Policies > Monitoring > Fabric Node Controls > default
        """
        Uni = cobra.model.pol.Uni(self.__root)
        Infra = cobra.model.infra.Infra(Uni)
        ZoneP = cobra.model.infrazone.ZoneP(Infra, **value)
        self.config.addMo(ZoneP)
        for infrazoneZone in value:
            if "Zone" in infrazoneZone:
                Zone = cobra.model.infrazone.Zone(ZoneP, **infrazoneZone["Zone"])
                self.config.addMo(Zone)


def not_nan_str(value: Mapping[str, Any], keys: Iterable[str]) -> bool:
    """
    Validate that none of the specified keys in a mapping contain invalid values.

    A value is considered invalid if it is:
    - None
    - An empty or whitespace-only string
    - The string "nan" (case-insensitive)
    - A float NaN value

    Missing keys are ignored.

    :param value: Mapping (dict-like) object to validate
    :param keys: Iterable of keys to check in the mapping
    :return: True if all existing keys have valid values, False otherwise
    """

    def is_invalid(v: Any) -> bool:
        if v is None:
            return True
        if isinstance(v, str):
            v = v.strip()
            return not v or v.lower() == "nan"
        if isinstance(v, float):
            return isnan(v)
        return False

    return not any(is_invalid(value[k]) for k in keys if k in value)
