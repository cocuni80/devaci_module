# Copyright 2020 Jorge C. Riveros
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ACI module configuration for the ACI Python SDK (cobra)."""

import json
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
from pathlib import Path

from .jinja import JinjaResult

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ------------------------------------------   ACI Error Class


class CobraError(Exception):
    """
    The AciError class manage the exceptions for Aci class
    """

    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return self.reason


# ------------------------------------------   Cobra Result Class


class CobraResult:
    """
    The CobraResult class return the results for Cobra class
    """

    def __init__(self):
        self.date = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
        self._output = None
        self._success = False
        self._log = str()

    @property
    def output(self) -> Optional[cobra.mit.request.ConfigRequest]:
        return self._output

    @property
    def success(self) -> bool:
        return self._success

    @property
    def log(self) -> str:
        return self._log

    @property
    def json(self) -> dict:
        return [
            {
                "date": self.date,
                "output": json.loads(self._output.data) if self._output else None,
                "success": self._success,
                "log": self._log,
            }
        ]

    @success.setter
    def success(self, value):
        self._success = value

    @log.setter
    def log(self, value):
        self._log = value

    @output.setter
    def output(self, value):
        self._output = value

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
        self.__infra = cobra.model.infra.Infra(self.__uni)
        self.__fabric_inst = cobra.model.fabric.Inst(self.__uni)
        self.config = cobra.mit.request.ConfigRequest()

        # --------------   Output Information

        self._result = CobraResult()

    # -------------------------------------------------   Control

    def render(self, path: Path, jinja: JinjaResult) -> CobraResult:
        try:
            if jinja.success and jinja.output:
                for key, value in jinja.output.items():
                    try:
                        if value:
                            caller = getattr(CobraClass, key)
                            caller(self, value)
                    except AttributeError as e:
                        self._result.log = (
                            f"[AttributeError]: {path.name} error, {str(e)}"
                        )

                if self.config.configMos:
                    self._result.output = self.config
                    self._result.success = True
                    self._result.log = (
                        f"[CobraClass]: Template {path.name} was sucessfully rendered."
                    )
            else:
                if not jinja.success:
                    self._result.log = jinja.log
                else:
                    self._result.log = (
                        f"[CobraClass]: {path.name} error, no valid data."
                    )
                self._result.success = False
        except TypeError as e:
            self._result.log = f"[TypeError]: {path.name} error, {str(e)}"
        except Exception as e:
            self._result.log = f"[CobraError]: {path.name} error, {str(e)}"

    @property
    def result(self):
        return self._result

    # -------------------------------------------------   Getter Tenant Management

    def tenant(self, **item):
        try:
            if "tenant" in item:
                return cobra.model.fv.Tenant(self.__uni, name=item["tenant"])
        except Exception as e:
            self._result.log = "[tenantError]: " + str(e)

    def ap(self, **item):
        try:
            if "ap" in item:
                return cobra.model.fv.Ap(self.tenant(**item), name=item["ap"])
        except Exception as e:
            self._result.log = "[apError]: " + str(e)

    # -------------------------------------------------   REST Tenant Management

    def fvTenant(self, value) -> None:
        """
        Tenants > All Tenants
        """
        try:
            for item in value:
                mo = cobra.model.fv.Tenant(self.__uni, **item)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[fvTenantError]: " + str(e)

    def fvAp(self, value) -> None:
        """
        Tenants > Application Profiles
        """
        try:
            for fvAp in value:
                Tenant = cobra.model.fv.Tenant(self.__uni, name=fvAp["tenant"])
                Ap = cobra.model.fv.Ap(Tenant, **fvAp)
                self.config.addMo(Ap)
                if "fvAEPg" in fvAp:
                    for fvAEPg in fvAp["fvAEPg"]:
                        AEPg = cobra.model.fv.AEPg(Ap, **fvAEPg)
                        self.config.addMo(AEPg)
                        if "fvRsBd" in fvAEPg:
                            RsBd = cobra.model.fv.RsBd(AEPg, **fvAEPg["fvRsBd"])
                            self.config.addMo(RsBd)
                        if "fvRsDomAtt" in fvAEPg:
                            for fvRsDomAtt in fvAEPg["fvRsDomAtt"]:
                                RsDomAtt = cobra.model.fv.RsDomAtt(AEPg, **fvRsDomAtt)
                                self.config.addMo(RsDomAtt)
                        if "fvRsPathAtt" in fvAEPg:
                            for fvRsPathAtt in fvAEPg["fvRsPathAtt"]:
                                RsPathAtt = cobra.model.fv.RsPathAtt(
                                    AEPg, **fvRsPathAtt
                                )
                                self.config.addMo(RsPathAtt)
        except Exception as e:
            self._result.log = "[fvApError]: " + str(e)
        return self._mo

    def fvAEPg(self, value) -> None:
        """
        Tenants > Application Profiles > Application EPGs
        """
        try:
            for fvAEPg in value:
                Tenant = cobra.model.fv.Tenant(self.__uni, name=fvAEPg["tenant"])
                Ap = cobra.model.fv.Ap(Tenant, name=fvAEPg["fvApName"])
                AEPg = cobra.model.fv.AEPg(Ap, **fvAEPg)
                self.config.addMo(AEPg)
                if "fvRsBd" in fvAEPg:
                    RsBd = cobra.model.fv.RsBd(AEPg, **fvAEPg["fvRsBd"])
                    self.config.addMo(RsBd)
                if "fvRsDomAtt" in fvAEPg:
                    for fvRsDomAtt in fvAEPg["fvRsDomAtt"]:
                        RsDomAtt = cobra.model.fv.RsDomAtt(AEPg, **fvRsDomAtt)
                        self.config.addMo(RsDomAtt)
                if "fvRsPathAtt" in fvAEPg:
                    for fvRsPathAtt in fvAEPg["fvRsPathAtt"]:
                        RsPathAtt = cobra.model.fv.RsPathAtt(AEPg, **fvRsPathAtt)
                        self.config.addMo(RsPathAtt)
        except Exception as e:
            self._result.log = "[fvAEPgError]: " + str(e)

    def staticPath(self, value) -> None:
        """
        Tenants > Application Profiles > Application EPGs > EPG Name > Static Ports
        """
        try:
            for fvAp in value:
                Tenant = cobra.model.fv.Tenant(self.__uni, name=fvAp["tenant"])
                self.config.addMo(Tenant)
                Ap = cobra.model.fv.Ap(Tenant, **fvAp)
                self.config.addMo(Ap)
                if "fvAEPg" in fvAp:
                    for fvAEPg in fvAp["fvAEPg"]:
                        AEPg = cobra.model.fv.AEPg(Ap, **fvAEPg)
                        # self.config.addMo(AEPg)
                        if "fvRsPathAtt" in fvAEPg:
                            for fvRsPathAtt in fvAEPg["fvRsPathAtt"]:
                                RsPathAtt = cobra.model.fv.RsPathAtt(
                                    AEPg, **fvRsPathAtt
                                )
                                self.config.addMo(RsPathAtt)
        except Exception as e:
            self._result.log = "[fvApError]: " + str(e)
        return self._mo

    def fvRsPathAtt(self, value) -> None:
        """
        Tenants > Application Profiles > Application EPGs > EPG Name > Static Ports
        """
        try:
            for fvRsPathAtt in value:
                Tenant = cobra.model.fv.Tenant(self.__uni, name=fvRsPathAtt["tenant"])
                self.config.addMo(Tenant)
                Ap = cobra.model.fv.Ap(Tenant, name=fvRsPathAtt["fvApName"])
                self.config.addMo(Ap)
                AEPg = cobra.model.fv.AEPg(Ap, name=fvRsPathAtt["fvAEPgName"])
                self.config.addMo(AEPg)
                RsPathAtt = cobra.model.fv.RsPathAtt(AEPg, **fvRsPathAtt)
                self.config.addMo(RsPathAtt)
        except Exception as e:
            self._result.log = "[fvRsPathAttError]: " + str(e)
        return self._mo

    def tenant_application_uepg(self, value) -> None:
        """
        Tenants > Application Profiles > uSeg EPGs
        """
        try:
            for item in value:
                mo = item
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[Error]: " + str(e)

    def tenant_application_esg(self, value):
        """
        Tenants > Application Profiles > Endpoint Security Groups
        """
        return self._mo

    def fvBD(self, value) -> None:
        """
        Tenants > Networking > Bridge Domains
        """
        try:
            for fvBD in value:
                Tenant = cobra.model.fv.Tenant(self.__uni, name=fvBD["tenant"])
                BD = cobra.model.fv.BD(Tenant, **fvBD)
                self.config.addMo(BD)
                if "fvRsCtx" in fvBD:
                    RsCtx = cobra.model.fv.RsCtx(BD, **fvBD["fvRsCtx"])
                    self.config.addMo(RsCtx)
                if "igmpIfP" in fvBD:
                    IfP = cobra.model.igmp.IfP(BD, **fvBD["igmpIfP"])
                    self.config.addMo(IfP)
                if "fvRsBdToEpRet" in fvBD:
                    RsBdToEpRet = cobra.model.fv.RsBdToEpRet(
                        BD, **fvBD["fvRsBdToEpRet"]
                    )
                    self.config.addMo(RsBdToEpRet)
                if "fvRsIgmpsn" in fvBD:
                    RsIgmpsn = cobra.model.fv.RsIgmpsn(BD, **fvBD["fvRsIgmpsn"])
                    self.config.addMo(RsIgmpsn)
                if "fvRsMldsn" in fvBD:
                    RsMldsn = cobra.model.fv.RsMldsn(BD, **fvBD["fvRsMldsn"])
                    self.config.addMo(RsMldsn)
                if "fvSubnet" in fvBD:
                    for fvSubnet in fvBD["fvSubnet"]:
                        if check("ip", fvSubnet):
                            Subnet = cobra.model.fv.Subnet(BD, **fvSubnet)
                            self.config.addMo(Subnet)
                if "fvRsBDToOut" in fvBD:
                    if check("tnL3extOutName", fvBD["fvRsBDToOut"]):
                        RsBDToOut = cobra.model.fv.RsBDToOut(BD, **fvBD["fvRsBDToOut"])
                        self.config.addMo(RsBDToOut)
        except Exception as e:
            self._result.log = "[fvBDError]: " + str(e)

    def fvCtx(self, value) -> None:
        """
        Tenants > Networking > VRFs
        """
        try:
            for fvCtx in value:
                Tenant = cobra.model.fv.Tenant(self.__uni, name=fvCtx["tenant"])
                Ctx = cobra.model.fv.Ctx(Tenant, **fvCtx)
                self.config.addMo(Ctx)
                if "vzAny" in fvCtx:
                    Any = cobra.model.vz.Any(Ctx, **fvCtx["vzAny"])
                    self.config.addMo(Any)
                    if "vzRsAnyToProv" in fvCtx["vzAny"]:
                        for vzRsAnyToProv in fvCtx["vzAny"]["vzRsAnyToProv"]:
                            if check("tnVzBrCPName", vzRsAnyToProv):
                                RsAnyToProv = cobra.model.vz.RsAnyToProv(
                                    Any, **vzRsAnyToProv
                                )
                                self.config.addMo(RsAnyToProv)
                    if "vzRsAnyToCons" in fvCtx["vzAny"]:
                        for vzRsAnyToCons in fvCtx["vzAny"]["vzRsAnyToCons"]:
                            if check("tnVzBrCPName", vzRsAnyToCons):
                                RsAnyToCons = cobra.model.vz.RsAnyToCons(
                                    Any, **vzRsAnyToCons
                                )
                                self.config.addMo(RsAnyToCons)
                if "fvRsCtxToEpRet" in fvCtx:
                    if check("tnFvEpRetPolName", fvCtx["fvRsCtxToEpRet"]):
                        RsCtxToEpRet = cobra.model.fv.RsCtxToEpRet(
                            Ctx, **fvCtx["fvRsCtxToEpRet"]
                        )
                        self.config.addMo(RsCtxToEpRet)
                if "fvRsCtxToExtRouteTagPol" in fvCtx:
                    if check(
                        "tnL3extRouteTagPolName", fvCtx["fvRsCtxToExtRouteTagPol"]
                    ):
                        RsCtxToExtRouteTagPol = cobra.model.fv.RsCtxToExtRouteTagPol(
                            Ctx, **fvCtx["fvRsCtxToExtRouteTagPol"]
                        )
                        self.config.addMo(RsCtxToExtRouteTagPol)
                if "fvRsOspfCtxPol" in fvCtx:
                    if check("tnOspfCtxPolName", fvCtx["fvRsOspfCtxPol"]):
                        RsOspfCtxPol = cobra.model.fv.RsOspfCtxPol(
                            Ctx, **fvCtx["fvRsOspfCtxPol"]
                        )
                        self.config.addMo(RsOspfCtxPol)
                if "fvRsBgpCtxPol" in fvCtx:
                    if check("tnBgpCtxPolName", fvCtx["fvRsBgpCtxPol"]):
                        RsBgpCtxPol = cobra.model.fv.RsBgpCtxPol(
                            Ctx, **fvCtx["fvRsBgpCtxPol"]
                        )
                        self.config.addMo(RsBgpCtxPol)
                if "fvRsVrfValidationPol" in fvCtx:
                    if check(
                        "tnL3extVrfValidationPolName", fvCtx["fvRsVrfValidationPol"]
                    ):
                        RsVrfValidationPol = cobra.model.fv.RsVrfValidationPol(
                            Ctx, **fvCtx["fvRsVrfValidationPol"]
                        )
                        self.config.addMo(RsVrfValidationPol)
                if "pimCtxP" in fvCtx:
                    if check("mtu", fvCtx["pimCtxP"]):
                        CtxP = cobra.model.pim.CtxP(Ctx, **fvCtx["pimCtxP"])
                        self.config.addMo(CtxP)
        except Exception as e:
            self._result.log = "[fvCtxError]: " + str(e)

    def tenant_network_l2out(self, value):
        """
        Tenants > Networking > L2Outs
        """
        return self._mo

    def l3extOut(self, value) -> None:
        """
        Tenants > Networking > L3Outs
        """
        try:
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
                                cobra.model.l3ext.RsNodeL3OutAtt(
                                    l3ext_lnodep, **node_l3out_att
                                )
                        if "l3extLIfP" in node:
                            l3ext_lifp = cobra.model.l3ext.LIfP(
                                l3ext_lnodep, **node["l3extLIfP"]
                            )
                            if "l3extRsPathL3OutAtt" in node["l3extLIfP"]:
                                for l3att in node["l3extLIfP"]["l3extRsPathL3OutAtt"]:
                                    cobra.model.l3ext.RsPathL3OutAtt(
                                        l3ext_lifp, **l3att
                                    )
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[l3extOutError]: " + str(e)

    def tenant_network_srmpls_l3out(self, value):
        """
        Tenants > Networking > SR-MPLS VRF L3Outs
        """
        return self._mo

    def tenant_dot1q_tunnel(self, value):
        """
        Tenants > Networking > Dot1Q Tunnels
        """
        return self._mo

    def fvnsAddrInst(self, value):
        """
        Tenants > mgmt > IP Address Pools
        """
        try:
            for fvnsAddrInst in value:
                Tenant = cobra.model.fv.Tenant(self.__uni, name=fvnsAddrInst["tenant"])
                AddrInst = cobra.model.fvns.AddrInst(Tenant, **fvnsAddrInst)
                self.config.addMo(AddrInst)
                if "fvnsUcastAddrBlk" in fvnsAddrInst:
                    for fvnsUcastAddrBlk in fvnsAddrInst["fvnsUcastAddrBlk"]:
                        if check("from", fvnsUcastAddrBlk):
                            UcastAddrBlk = cobra.model.fvns.UcastAddrBlk(
                                AddrInst, **fvnsUcastAddrBlk
                            )
                            self.config.addMo(UcastAddrBlk)
        except Exception as e:
            self._result.log = "[fvnsAddrInstError]: " + str(e)

    def mgmtGrp(self, value):
        """
        Tenants > mgmt > Managed Node Connectivity Groups
        """
        try:
            FuncP = cobra.model.infra.FuncP(self.__infra)
            for mgmtGrp in value:
                Grp = cobra.model.mgmt.Grp(FuncP, **mgmtGrp)
                self.config.addMo(Grp)
                if "mgmtOoBZone" in mgmtGrp:
                    OoBZone = cobra.model.mgmt.OoBZone(Grp)
                    if "mgmtRsOoB" in mgmtGrp["mgmtOoBZone"]:
                        RsOoB = cobra.model.mgmt.RsOoB(
                            OoBZone, **mgmtGrp["mgmtOoBZone"]["mgmtRsOoB"]
                        )
                        self.config.addMo(RsOoB)
                    if "mgmtRsAddrInst" in mgmtGrp["mgmtOoBZone"]:
                        RsAddrInst = cobra.model.mgmt.RsAddrInst(
                            OoBZone, **mgmtGrp["mgmtOoBZone"]["mgmtRsAddrInst"]
                        )
                        self.config.addMo(RsAddrInst)
                if "mgmtInBZone" in mgmtGrp:
                    InBZone = cobra.model.mgmt.InBZone(Grp)
                    if "mgmtRsInB" in mgmtGrp["mgmtInBZone"]:
                        RsInB = cobra.model.mgmt.RsInB(
                            InBZone, **mgmtGrp["mgmtInBZone"]["mgmtRsInB"]
                        )
                        self.config.addMo(RsInB)
                    if "mgmtRsAddrInst" in mgmtGrp["mgmtInBZone"]:
                        RsAddrInst = cobra.model.mgmt.RsAddrInst(
                            InBZone, **mgmtGrp["mgmtInBZone"]["mgmtRsAddrInst"]
                        )
                        self.config.addMo(RsAddrInst)
        except Exception as e:
            self._result.log = "[mgmtGrpError]: " + str(e)

    def mgmtNodeGrp(self, value):
        """
        Tenants > mgmt > Node Management Addresses
        """
        try:
            for mgmtNodeGrp in value:
                NodeGrp = cobra.model.mgmt.NodeGrp(self.__infra, **mgmtNodeGrp)
                self.config.addMo(NodeGrp)
                if "mgmtRsGrp" in mgmtNodeGrp:
                    for mgmtRsGrp in mgmtNodeGrp["mgmtRsGrp"]:
                        RsGrp = cobra.model.mgmt.RsGrp(NodeGrp, **mgmtRsGrp)
                        self.config.addMo(RsGrp)
                if "infraNodeBlk" in mgmtNodeGrp:
                    for infraNodeBlk in mgmtNodeGrp["infraNodeBlk"]:
                        if check("from_", infraNodeBlk):
                            NodeBlk = cobra.model.infra.NodeBlk(NodeGrp, **infraNodeBlk)
                            self.config.addMo(NodeBlk)
        except Exception as e:
            self._result.log = "[mgmtNodeGrpError]: " + str(e)

    def tenant_contract_standard(self, value):
        """
        Tenants > Contracts > Standard
        """
        return self._mo

    def tenant_contract_taboo(self, value):
        """
        Tenants > Contracts > Taboos
        """
        return self._mo

    def tenant_contract_imported(self, value):
        """
        Tenants > Contracts > Imported
        """
        return self._mo

    def tenant_contract_filter(self, value):
        """
        Tenants > Contracts > Filters
        """
        return self._mo

    def tenant_contract_oob(self, value):
        """
        Tenants > Contracts > Out-Of-Band Contracts
        """
        return self._mo

    def tenant_policy_protocol_bfd(self, value):
        """
        Tenants > Policies > Protocol > BFD
        """
        return self._mo

    def tenant_policy_protocol_bgp(self, value):
        """
        Tenants > Policies > Protocol > BGP
        """
        return self._mo

    def tenant_policy_protocol_qos(self, value):
        """
        Tenants > Policies > Protocol > Custom QoS
        """
        return self._mo

    def tenant_policy_protocol_dhcp(self, value):
        """
        Tenants > Policies > Protocol > DHCP
        """
        return self._mo

    def tenant_policy_protocol_dataplane(self, value):
        """
        Tenants > Policies > Protocol > Data Plane Policing
        """
        return self._mo

    def tenant_policy_protocol_eigrp(self, value):
        """
        Tenants > Policies > Protocol > EIGRP
        """
        return self._mo

    def tenant_policy_protocol_endpoint_retention(self, value):
        """
        Tenants > Policies > Protocol > End Point Retention
        """
        return self._mo

    def tenant_policy_protocol_firsthop_security(self, value):
        """
        Tenants > Policies > Protocol > First Hop Security
        """
        return self._mo

    def tenant_policy_protocol_hsrp(self, value):
        """
        Tenants > Policies > Protocol > HSRP
        """
        return self._mo

    def tenant_policy_protocol_igmp(self, value):
        """
        Tenants > Policies > Protocol > IGMP
        """
        return self._mo

    def tenant_policy_protocol_ip_sla(self, value):
        """
        Tenants > Policies > Protocol > IP SLA
        """
        return self._mo

    def tenant_policy_protocol_pbr(self, value):
        """
        Tenants > Policies > Protocol > L4-L7 Policy-Based Redirect
        """
        return self._mo

    def tenant_policy_protocol_ospf(self, value):
        """
        Tenants > Policies > Protocol > OSPF
        """
        return self._mo

    def tenant_policy_protocol_pim(self, value):
        """
        Tenants > Policies > Protocol > PIM
        """
        return self._mo

    def tenant_policy_protocol_routemap_multicast(self, value):
        """
        Tenants > Policies > Protocol > Route Maps for Multicast
        """
        return self._mo

    def tenant_policy_protocol_routemap_control(self, value):
        """
        Tenants > Policies > Protocol > Route Maps for Route Control
        """
        return self._mo

    def tenant_policy_protocol_route_tag(self, value):
        """
        Tenants > Policies > Protocol > Route Tag
        """
        return self._mo

    def tenant_policy_troubleshooting_span(self, value):
        """
        Tenants > Policies > Troubleshooting SPAN
        """
        return self._mo

    def tenant_policy_troubleshooting_traceroute(self, value):
        """
        Tenants > Policies > Troubleshooting Traceroute
        """
        return self._mo

    def tenant_policy_monitoring(self, value):
        """
        Tenants > Policies > Monitoring
        """
        return self._mo

    def tenant_policy_netflow(self, value):
        """
        Tenants > Policies > NetFlow
        """
        return self._mo

    def tenant_policy_vmm(self, value):
        """
        Tenants > Policies > VMM
        """
        return self._mo

    def tenant_service_parameter(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Service Parameters
        """
        return self._mo

    def tenant_service_graph_template(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Service Graph Templates
        """
        return self._mo

    def tenant_service_router_configuration(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Router Configuration
        """
        return self._mo

    def tenant_service_function_profile(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Function Profiles
        """
        return self._mo

    def tenant_service_devices(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Devices
        """
        return self._mo

    def tenant_service_imported_device(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Imported Devices
        """
        return self._mo

    def tenant_service_device_policy(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Device Selection Policies
        """
        return self._mo

    def tenant_service_deployed_graph_instance(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Deployed Graph Instances
        """
        return self._mo

    def tenant_service_deployed_device(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Deployed Devices
        """
        return self._mo

    def tenant_service_device_manager(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Device Managers
        """
        return self._mo

    def tenant_service_chassis(self, value):
        """
        Tenants > Policies > Services > L4-L7 > Chassis
        """
        return self._mo

    def tenant_node_management_epg(self, value):
        """
        Tenants > Node Management EPGs
        """
        return self._mo

    def tenant_external_management_profile(self, value):
        """
        Tenants > External Management Network Instance Profiles
        """
        return self._mo

    def tenant_node_management_address(self, value):
        """
        Tenants > Node Management Address
        """
        return self._mo

    def tenant_node_management_static(self, value):
        """
        Tenants > Node Management Address > Static Node Management Address
        """
        return self._mo

    def tenant_node_connection_group(self, value):
        """
        Tenants > Managed Node Connectivity Groups
        """
        return self._mo

    def fabricSetupPol(self, value):
        """
        Fabric > Inventory > Pod Fabric Setup Policy
        """
        try:
            ctrlr_inst = cobra.model.ctrlr.Inst(self.__uni)
            SetupPol = cobra.model.fabric.SetupPol(ctrlr_inst, **value)
            if "SetupP" in value:
                for item in value["SetupP"]:
                    mo = cobra.model.fabric.SetupP(SetupPol, **item)
                    self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[fabricSetupPolError]: " + str(e)

    def fabricRsOosPath(self, value):
        """
        Fabric > RsOosPath
        """
        try:
            Inst = cobra.model.fabric.Inst(self.__uni)
            OOServicePol = cobra.model.fabric.OOServicePol(Inst)
            self.config.addMo(OOServicePol)
            for fabricRsOosPath in value:
                RsOosPath = cobra.model.fabric.RsOosPath(
                    OOServicePol, **fabricRsOosPath
                )
                self.config.addMo(RsOosPath)
        except Exception as e:
            self._result.log = "[fabricRsOosPathError]: " + str(e)

    def fabricSetupP(self, value):
        """
        Fabric > Inventory > Pod Fabric Setup Policy
        """
        try:
            for item in value:
                ctrlr_inst = cobra.model.ctrlr.Inst(self.__uni)
                setup_pol = cobra.model.fabric.SetupPol(ctrlr_inst)
                mo = cobra.model.fabric.SetupP(setup_pol, **item)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[fabricSetupPError]: " + str(e)

    def fabricNodeIdentPol(self, value):
        """
        Fabric > Inventory > Fabric Membership
        """
        try:
            ctrlr_inst = cobra.model.ctrlr.Inst(self.__uni)
            node_ident_pol = cobra.model.fabric.NodeIdentPol(ctrlr_inst, **value)
            if "NodeIdentP" in value:
                for item in value["NodeIdentP"]:
                    mo = cobra.model.fabric.NodeIdentP(node_ident_pol, **item)
                    self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[NodeIdentPolPError]: " + str(e)

    def fabricPodPGrp(self, value):
        """
        Fabric > Fabric Policies > Pods > Policy Groups
        """
        try:
            for item in value:
                fabric_inst = cobra.model.fabric.Inst(self.__uni)
                fabric_func_p = cobra.model.fabric.FuncP(fabric_inst)
                mo = cobra.model.fabric.PodPGrp(fabric_func_p, **item)
                if "fabricRtPodPGrp" in item:
                    cobra.model.fabric.RtPodPGrp(mo, **item["fabricRtPodPGrp"])
                if "fabricRsSnmpPol" in item:
                    cobra.model.fabric.RsSnmpPol(mo, **item["fabricRsSnmpPol"])
                if "fabricRsPodPGrpIsisDomP" in item:
                    cobra.model.fabric.RsPodPGrpIsisDomP(
                        mo, **item["fabricRsPodPGrpIsisDomP"]
                    )
                if "fabricRsPodPGrpCoopP" in item:
                    cobra.model.fabric.RsPodPGrpCoopP(
                        mo, **item["fabricRsPodPGrpCoopP"]
                    )
                if "fabricRsPodPGrpBGPRRP" in item:
                    cobra.model.fabric.RsPodPGrpBGPRRP(
                        mo, **item["fabricRsPodPGrpBGPRRP"]
                    )
                if "fabricRsTimePol" in item:
                    cobra.model.fabric.RsTimePol(mo, **item["fabricRsTimePol"])
                if "fabricRsMacsecPol" in item:
                    cobra.model.fabric.RsMacsecPol(mo, **item["fabricRsMacsecPol"])
                if "fabricRsCommPol" in item:
                    cobra.model.fabric.RsCommPol(mo, **item["fabricRsCommPol"])
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[fabricPodPGrpError]: " + str(e)

    def fabricPodP(self, value):
        """
        Fabric > Fabric Policies > Pods > Profiles
        """
        try:
            for item in value:
                fabric_inst = cobra.model.fabric.Inst(self.__uni)
                mo = cobra.model.fabric.PodP(fabric_inst, **item)
                if "fabricPodS" in item:
                    for pod_s in item["fabricPodS"]:
                        mo_pod_s = cobra.model.fabric.PodS(mo, **pod_s)
                        if "fabricRsPodPGrp" in pod_s:
                            cobra.model.fabric.RsPodPGrp(
                                mo_pod_s, **pod_s["fabricRsPodPGrp"]
                            )
                        if "fabricPodBlk" in pod_s:
                            cobra.model.fabric.PodBlk(mo_pod_s, **pod_s["fabricPodBlk"])
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[fabricPodPError]: " + str(e)

    def fabric_switch_leaf_profile(self, value):
        """
        Fabric > Fabric Policies > Switches > Leaf Switches > Profiles
        """
        return self._mo

    def fabric_switch_leaf_policy_group(self, value):
        """
        Fabric > Fabric Policies > Switches > Leaf Switches > Policy Groups
        """
        return self._mo

    def fabric_switch_spine_profile(self, value):
        """
        Fabric > Fabric Policies > Switches > Spine Switches > Profiles
        """
        return self._mo

    def fabric_switch_spine_policy_group(self, value):
        """
        Fabric > Fabric Policies > Switches > Spine Switches > Policy Groups
        """
        return self._mo

    def fabric_module_leaf_profile(self, value):
        """
        Fabric > Fabric Policies > Modules > Leaf Modules > Profiles
        """
        return self._mo

    def fabric_module_leaf_policy_group(self, value):
        """
        Fabric > Fabric Policies > Modules > Leaf Modules > Policy Groups
        """
        return self._mo

    def fabric_module_spine_profile(self, value):
        """
        Fabric > Fabric Policies > Modules > Spine Modules > Profiles
        """
        return self._mo

    def fabric_module_spine_policy_group(self, value):
        """
        Fabric > Fabric Policies > Modules > Spine Modules > Policy Groups
        """
        return self._mo

    def fabric_interface_leaf_profile(self, value):
        """
        Fabric > Fabric Policies > Interfaces > Leaf Interfaces > Profiles
        """
        return self._mo

    def fabric_interface_leaf_policy_group(self, value):
        """
        Fabric > Fabric Policies > Interfaces > Leaf Interfaces > Policy Groups
        """
        return self._mo

    def fabric_interface_spine_profile(self, value):
        """
        Fabric > Fabric Policies > Interfaces > Spine Interfaces > Profiles
        """
        return self._mo

    def fabric_interface_spine_policy_group(self, value):
        """
        Fabric > Fabric Policies > Interfaces > Spine Interfaces > Policy Groups
        """
        return self._mo

    def datetimePol(self, value):
        """
        Fabric > Fabric Policies > Policies > Pod > Date and Time
        """
        try:
            Inst = cobra.model.fabric.Inst(self.__uni)
            for datetimePol in value:
                Pol = cobra.model.datetime.Pol(Inst, **datetimePol)
                self.config.addMo(Pol)
                if "datetimeNtpAuthKey" in datetimePol:
                    for datetimeNtpAuthKey in datetimePol["datetimeNtpAuthKey"]:
                        if not_nan(datetimeNtpAuthKey):
                            NtpAuthKey = cobra.model.datetime.NtpAuthKey(
                                Pol, **datetimeNtpAuthKey
                            )
                            self.config.addMo(NtpAuthKey)
                if "datetimeNtpProv" in datetimePol:
                    for datetimeNtpProv in datetimePol["datetimeNtpProv"]:
                        if not_nan(datetimeNtpProv):
                            NtpProv = cobra.model.datetime.NtpProv(
                                Pol, **datetimeNtpProv
                            )
                            self.config.addMo(NtpProv)
                            if "datetimeRsNtpProvToNtpAuthKey" in datetimeNtpProv:
                                for datetimeRsNtpProvToNtpAuthKey in datetimeNtpProv[
                                    "datetimeRsNtpProvToNtpAuthKey"
                                ]:
                                    if not_nan(datetimeRsNtpProvToNtpAuthKey):
                                        RsNtpProvToNtpAuthKey = (
                                            cobra.model.datetime.RsNtpProvToNtpAuthKey(
                                                NtpProv,
                                                **datetimeRsNtpProvToNtpAuthKey,
                                            )
                                        )
                                        self.config.addMo(RsNtpProvToNtpAuthKey)
                            if "datetimeRsNtpProvToEpg" in datetimeNtpProv:
                                if not_nan(datetimeNtpProv["datetimeRsNtpProvToEpg"]):
                                    RsNtpProvToEpg = (
                                        cobra.model.datetime.RsNtpProvToEpg(
                                            NtpProv,
                                            **datetimeNtpProv["datetimeRsNtpProvToEpg"],
                                        )
                                    )
                                    self.config.addMo(RsNtpProvToEpg)
        except Exception as e:
            self._result.log = "[datetimePolError]: " + str(e)

    def snmpPol(self, value):
        """
        Fabric > Fabric Policies > Policies > Pod > SNMP
        """
        try:
            Inst = cobra.model.fabric.Inst(self.__uni)
            for snmpPol in value:
                Pol = cobra.model.snmp.Pol(Inst, **snmpPol)
                self.config.addMo(Pol)
                if "snmpClientGrpP" in snmpPol:
                    for snmpClientGrpP in snmpPol["snmpClientGrpP"]:
                        if not_nan(snmpClientGrpP):
                            ClientGrpP = cobra.model.snmp.ClientGrpP(
                                Pol, **snmpClientGrpP
                            )
                            if "snmpRsEpg" in snmpClientGrpP:
                                if not_nan(snmpClientGrpP["snmpRsEpg"]):
                                    RsEpg = cobra.model.snmp.RsEpg(
                                        ClientGrpP, **snmpClientGrpP["snmpRsEpg"]
                                    )
                                    self.config.addMo(RsEpg)
                            if "snmpClientP" in snmpClientGrpP:
                                for snmpClientP in snmpClientGrpP["snmpClientP"]:
                                    if not_nan(snmpClientP):
                                        ClientP = cobra.model.snmp.ClientP(
                                            ClientGrpP, **snmpClientP
                                        )
                                        self.config.addMo(ClientP)
                if "snmpUserP" in snmpPol:
                    for snmpUserP in snmpPol["snmpUserP"]:
                        if not_nan(snmpUserP):
                            UserP = cobra.model.snmp.UserP(Pol, **snmpUserP)
                            self.config.addMo(UserP)
                if "snmpCommunityP" in snmpPol:
                    for snmpCommunityP in snmpPol["snmpCommunityP"]:
                        if not_nan(snmpCommunityP):
                            CommunityP = cobra.model.snmp.CommunityP(
                                Pol, **snmpCommunityP
                            )
                            self.config.addMo(CommunityP)
                if "snmpTrapFwdServerP" in snmpPol:
                    for snmpTrapFwdServerP in snmpPol["snmpTrapFwdServerP"]:
                        if not_nan(snmpTrapFwdServerP):
                            TrapFwdServerP = cobra.model.snmp.TrapFwdServerP(
                                Pol, **snmpTrapFwdServerP
                            )
                            self.config.addMo(TrapFwdServerP)
        except Exception as e:
            self._result.log = "[snmpPolError]: " + str(e)

    def commPol(self, value):
        """
        Fabric > Fabric Policies > Policies > Pod > Management Access
        """
        try:
            Inst = cobra.model.fabric.Inst(self.__uni)
            for commPol in value:
                Pol = cobra.model.comm.Pol(Inst, **commPol)
                if "commTelnet" in commPol:
                    if not_nan(commPol["commTelnet"]):
                        Telnet = cobra.model.comm.Telnet(Pol, **commPol["commTelnet"])
                        self.config.addMo(Telnet)
                if "commSsh" in commPol:
                    if not_nan(commPol["commSsh"]):
                        Ssh = cobra.model.comm.Ssh(Pol, **commPol["commSsh"])
                        self.config.addMo(Ssh)
                if "commHttp" in commPol:
                    if not_nan(commPol["commHttp"]):
                        Http = cobra.model.comm.Http(Pol, **commPol["commHttp"])
                        self.config.addMo(Http)
                if "commHttps" in commPol:
                    if not_nan(commPol["commHttps"]):
                        Https = cobra.model.comm.Https(Pol, **commPol["commHttps"])
                        self.config.addMo(Https)
                if "commShellinabox" in commPol:
                    if not_nan(commPol["commShellinabox"]):
                        Shellinabox = cobra.model.comm.Shellinabox(
                            Pol, **commPol["commShellinabox"]
                        )
                        self.config.addMo(Shellinabox)
        except Exception as e:
            self._result.log = "[commPolError]: " + str(e)

    def fabric_policy_switch_callhome(self, value):
        """
        Fabric > Fabric Policies > Policies > Switch > Callhome Inventory
        """
        return self._mo

    def infraNodeP(self, value):
        """
        Fabric > Access Policies > Switches > Leaf Switches > Profiles
        """
        try:
            for infraNodeP in value:
                NodeP = cobra.model.infra.NodeP(self.__infra, **infraNodeP)
                self.config.addMo(NodeP)
                if "infraLeafS" in infraNodeP:
                    for infraLeafS in infraNodeP["infraLeafS"]:
                        if check("name", infraLeafS):
                            LeafS = cobra.model.infra.LeafS(NodeP, **infraLeafS)
                            self.config.addMo(LeafS)
                            if "infraNodeBlk" in infraLeafS:
                                if check("from_", infraLeafS["infraNodeBlk"]):
                                    NodeBlk = cobra.model.infra.NodeBlk(
                                        LeafS, **infraLeafS["infraNodeBlk"]
                                    )
                                    self.config.addMo(NodeBlk)
                            if "infraRsAccNodePGrp" in infraLeafS:
                                if check("tDn", infraLeafS["infraRsAccNodePGrp"]):
                                    RsAccNodePGrp = cobra.model.infra.RsAccNodePGrp(
                                        LeafS, **infraLeafS["infraRsAccNodePGrp"]
                                    )
                                    self.config.addMo(RsAccNodePGrp)
                if "infraRsAccPortP" in infraNodeP:
                    for infraRsAccPortP in infraNodeP["infraRsAccPortP"]:
                        if check("tDn", infraRsAccPortP):
                            RsAccPortP = cobra.model.infra.RsAccPortP(
                                NodeP, **infraRsAccPortP
                            )
                            self.config.addMo(RsAccPortP)
        except Exception as e:
            self._result.log = "[infraNodePError]: " + str(e)

    def infraAccNodePGrp(self, value):
        """
        Fabric > Access Policies > Switches > Leaf Switches > Policy Groups
        """
        try:
            FuncP = cobra.model.infra.FuncP(self.__infra)
            for infraAccNodePGrp in value:
                AccNodePGrp = cobra.model.infra.AccNodePGrp(FuncP, **infraAccNodePGrp)
                self.config.addMo(AccNodePGrp)
                if "infraRsTopoctrlFwdScaleProfPol" in infraAccNodePGrp:
                    if check(
                        "tnTopoctrlFwdScaleProfilePolName",
                        infraAccNodePGrp["infraRsTopoctrlFwdScaleProfPol"],
                    ):
                        RsTopoctrlFwdScaleProfPol = (
                            cobra.model.infra.RsTopoctrlFwdScaleProfPol(
                                AccNodePGrp,
                                **infraAccNodePGrp["infraRsTopoctrlFwdScaleProfPol"],
                            )
                        )
                        self.config.addMo(RsTopoctrlFwdScaleProfPol)
                if "infraRsLeafTopoctrlUsbConfigProfilePol" in infraAccNodePGrp:
                    if check(
                        "tnTopoctrlUsbConfigProfilePolName",
                        infraAccNodePGrp["infraRsLeafTopoctrlUsbConfigProfilePol"],
                    ):
                        RsLeafTopoctrlUsbConfigProfilePol = (
                            cobra.model.infra.RsLeafTopoctrlUsbConfigProfilePol(
                                AccNodePGrp,
                                **infraAccNodePGrp[
                                    "infraRsLeafTopoctrlUsbConfigProfilePol"
                                ],
                            )
                        )
                        self.config.addMo(RsLeafTopoctrlUsbConfigProfilePol)
                if "infraRsLeafPGrpToLldpIfPol" in infraAccNodePGrp:
                    if check(
                        "tnLldpIfPolName",
                        infraAccNodePGrp["infraRsLeafPGrpToLldpIfPol"],
                    ):
                        RsLeafPGrpToLldpIfPol = cobra.model.infra.RsLeafPGrpToLldpIfPol(
                            AccNodePGrp,
                            **infraAccNodePGrp["infraRsLeafPGrpToLldpIfPol"],
                        )
                        self.config.addMo(RsLeafPGrpToLldpIfPol)
                if "infraRsBfdIpv6InstPol" in infraAccNodePGrp:
                    if check(
                        "tnBfdIpv6InstPolName",
                        infraAccNodePGrp["infraRsBfdIpv6InstPol"],
                    ):
                        RsBfdIpv6InstPol = cobra.model.infra.RsBfdIpv6InstPol(
                            AccNodePGrp,
                            **infraAccNodePGrp["infraRsBfdIpv6InstPol"],
                        )
                        self.config.addMo(RsBfdIpv6InstPol)
                if "infraRsSynceInstPol" in infraAccNodePGrp:
                    if check(
                        "tnSynceInstPolName",
                        infraAccNodePGrp["infraRsSynceInstPol"],
                    ):
                        RsSynceInstPol = cobra.model.infra.RsSynceInstPol(
                            AccNodePGrp,
                            **infraAccNodePGrp["infraRsSynceInstPol"],
                        )
                        self.config.addMo(RsSynceInstPol)
                if "infraRsPoeInstPol" in infraAccNodePGrp:
                    if check(
                        "tnPoeInstPolName",
                        infraAccNodePGrp["infraRsPoeInstPol"],
                    ):
                        RsPoeInstPol = cobra.model.infra.RsPoeInstPol(
                            AccNodePGrp,
                            **infraAccNodePGrp["infraRsPoeInstPol"],
                        )
                        self.config.addMo(RsPoeInstPol)
                if "infraRsBfdMhIpv4InstPol" in infraAccNodePGrp:
                    if check(
                        "tnBfdMhIpv4InstPolName",
                        infraAccNodePGrp["infraRsBfdMhIpv4InstPol"],
                    ):
                        RsBfdMhIpv4InstPol = cobra.model.infra.RsBfdMhIpv4InstPol(
                            AccNodePGrp,
                            **infraAccNodePGrp["infraRsBfdMhIpv4InstPol"],
                        )
                        self.config.addMo(RsBfdMhIpv4InstPol)
                if "infraRsBfdMhIpv6InstPol" in infraAccNodePGrp:
                    if check(
                        "tnBfdMhIpv6InstPolName",
                        infraAccNodePGrp["infraRsBfdMhIpv6InstPol"],
                    ):
                        RsBfdMhIpv6InstPol = cobra.model.infra.RsBfdMhIpv6InstPol(
                            AccNodePGrp,
                            **infraAccNodePGrp["infraRsBfdMhIpv6InstPol"],
                        )
                        self.config.addMo(RsBfdMhIpv6InstPol)
                if "infraRsEquipmentFlashConfigPol" in infraAccNodePGrp:
                    if check(
                        "tnEquipmentFlashConfigPolName",
                        infraAccNodePGrp["infraRsEquipmentFlashConfigPol"],
                    ):
                        RsEquipmentFlashConfigPol = (
                            cobra.model.infra.RsEquipmentFlashConfigPol(
                                AccNodePGrp,
                                **infraAccNodePGrp["infraRsEquipmentFlashConfigPol"],
                            )
                        )
                        self.config.addMo(RsEquipmentFlashConfigPol)
                if "infraRsMonNodeInfraPol" in infraAccNodePGrp:
                    if check(
                        "tnMonInfraPolName",
                        infraAccNodePGrp["infraRsMonNodeInfraPol"],
                    ):
                        RsMonNodeInfraPol = cobra.model.infra.RsMonNodeInfraPol(
                            AccNodePGrp,
                            **infraAccNodePGrp["infraRsMonNodeInfraPol"],
                        )
                        self.config.addMo(RsMonNodeInfraPol)
                if "infraRsFcInstPol" in infraAccNodePGrp:
                    if check(
                        "tnFcInstPolName",
                        infraAccNodePGrp["infraRsFcInstPol"],
                    ):
                        RsFcInstPol = cobra.model.infra.RsFcInstPol(
                            AccNodePGrp,
                            **infraAccNodePGrp["infraRsFcInstPol"],
                        )
                        self.config.addMo(RsFcInstPol)
                if "infraRsTopoctrlFastLinkFailoverInstPol" in infraAccNodePGrp:
                    if check(
                        "tnTopoctrlFastLinkFailoverInstPolName",
                        infraAccNodePGrp["infraRsTopoctrlFastLinkFailoverInstPol"],
                    ):
                        RsTopoctrlFastLinkFailoverInstPol = (
                            cobra.model.infra.RsTopoctrlFastLinkFailoverInstPol(
                                AccNodePGrp,
                                **infraAccNodePGrp[
                                    "infraRsTopoctrlFastLinkFailoverInstPol"
                                ],
                            )
                        )
                        self.config.addMo(RsTopoctrlFastLinkFailoverInstPol)
                if "infraRsMstInstPol" in infraAccNodePGrp:
                    if check(
                        "tnStpInstPolName",
                        infraAccNodePGrp["infraRsMstInstPol"],
                    ):
                        RsMstInstPol = cobra.model.infra.RsMstInstPol(
                            AccNodePGrp,
                            **infraAccNodePGrp["infraRsMstInstPol"],
                        )
                        self.config.addMo(RsMstInstPol)
                if "infraRsFcFabricPol" in infraAccNodePGrp:
                    if check(
                        "tnFcFabricPolName",
                        infraAccNodePGrp["infraRsFcFabricPol"],
                    ):
                        RsFcFabricPol = cobra.model.infra.RsFcFabricPol(
                            AccNodePGrp,
                            **infraAccNodePGrp["infraRsFcFabricPol"],
                        )
                        self.config.addMo(RsFcFabricPol)
                if "infraRsLeafCoppProfile" in infraAccNodePGrp:
                    if check(
                        "tnCoppLeafProfileName",
                        infraAccNodePGrp["infraRsLeafCoppProfile"],
                    ):
                        RsLeafCoppProfile = cobra.model.infra.RsLeafCoppProfile(
                            AccNodePGrp,
                            **infraAccNodePGrp["infraRsLeafCoppProfile"],
                        )
                        self.config.addMo(RsLeafCoppProfile)
                if "infraRsIaclLeafProfile" in infraAccNodePGrp:
                    if check(
                        "tnIaclLeafProfileName",
                        infraAccNodePGrp["infraRsIaclLeafProfile"],
                    ):
                        RsIaclLeafProfile = cobra.model.infra.RsIaclLeafProfile(
                            AccNodePGrp,
                            **infraAccNodePGrp["infraRsIaclLeafProfile"],
                        )
                        self.config.addMo(RsIaclLeafProfile)
                if "infraRsBfdIpv4InstPol" in infraAccNodePGrp:
                    if check(
                        "tnBfdIpv4InstPolName",
                        infraAccNodePGrp["infraRsBfdIpv4InstPol"],
                    ):
                        RsBfdIpv4InstPol = cobra.model.infra.RsBfdIpv4InstPol(
                            AccNodePGrp,
                            **infraAccNodePGrp["infraRsBfdIpv4InstPol"],
                        )
                        self.config.addMo(RsBfdIpv4InstPol)
                if "infraRsL2NodeAuthPol" in infraAccNodePGrp:
                    if check(
                        "tnL2NodeAuthPolName",
                        infraAccNodePGrp["infraRsL2NodeAuthPol"],
                    ):
                        RsL2NodeAuthPol = cobra.model.infra.RsL2NodeAuthPol(
                            AccNodePGrp,
                            **infraAccNodePGrp["infraRsL2NodeAuthPol"],
                        )
                        self.config.addMo(RsL2NodeAuthPol)
                if "infraRsLeafPGrpToCdpIfPol" in infraAccNodePGrp:
                    if check(
                        "tnCdpIfPolName",
                        infraAccNodePGrp["infraRsLeafPGrpToCdpIfPol"],
                    ):
                        RsLeafPGrpToCdpIfPol = cobra.model.infra.RsLeafPGrpToCdpIfPol(
                            AccNodePGrp,
                            **infraAccNodePGrp["infraRsLeafPGrpToCdpIfPol"],
                        )
                        self.config.addMo(RsLeafPGrpToCdpIfPol)
        except Exception as e:
            self._result.log = "[infraAccNodePGrpError]: " + str(e)

    def infraSpineP(self, value):
        """
        Fabric > Access Policies > Switches > Spine Switches > Profiles
        """
        try:
            for item in value:
                mo = cobra.model.infra.SpineP(self.__infra, **item)
                if "infraSpineS" in item:
                    for spine_s in item["infraSpineS"]:
                        mo_spine_s = cobra.model.infra.SpineS(mo, **spine_s)
                        if "infraRsSpineAccNodePGrp" in spine_s:
                            cobra.model.infra.RsSpineAccNodePGrp(
                                mo_spine_s, **spine_s["infraRsSpineAccNodePGrp"]
                            )
                        if "infraNodeBlk" in spine_s:
                            cobra.model.infra.NodeBlk(
                                mo_spine_s, **spine_s["infraNodeBlk"]
                            )
                if "infraRsSpAccPortP" in item:
                    cobra.model.infra.RsSpAccPortP(mo, **item["infraRsSpAccPortP"])
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[infraSpinePError]: " + str(e)

    def infraSpineAccNodePGrp(self, value):
        """
        Fabric > Access Policies > Switches > Spine Switches > Policy Groups
        """
        try:
            for item in value:
                funcp = cobra.model.infra.FuncP(self.__infra)
                mo = cobra.model.infra.SpineAccNodePGrp(funcp, **item)
                if "infraRsSpineCoppProfile" in item:
                    cobra.model.infra.RsSpineCoppProfile(
                        mo, **item["infraRsSpineCoppProfile"]
                    )
                if "infraRsSpineBfdIpv4InstPol" in item:
                    cobra.model.infra.RsSpineBfdIpv4InstPol(
                        mo, **item["infraRsSpineBfdIpv4InstPol"]
                    )
                if "infraRsSpineBfdIpv6InstPol" in item:
                    cobra.model.infra.RsSpineBfdIpv6InstPol(
                        mo, **item["infraRsSpineBfdIpv6InstPol"]
                    )
                if "infraRsIaclSpineProfile" in item:
                    cobra.model.infra.RsIaclSpineProfile(
                        mo, **item["infraRsIaclSpineProfile"]
                    )
                if "infraRsSpinePGrpToCdpIfPol" in item:
                    cobra.model.infra.RsSpinePGrpToCdpIfPol(
                        mo, **item["infraRsSpinePGrpToCdpIfPol"]
                    )
                if "infraRsSpinePGrpToLldpIfPol" in item:
                    cobra.model.infra.RsSpinePGrpToLldpIfPol(
                        mo, **item["infraRsSpinePGrpToLldpIfPol"]
                    )
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[infraSpineAccNodePGrpError]: " + str(e)

    def infraSpAccPortP(self, value):
        """
        Fabric > Access Policies > Interfaces > Spine Interfaces > Profiles
        """
        try:
            for item in value:
                mo = cobra.model.infra.SpAccPortP(self.__infra, **item)
                if "infraSHPortS" in item:
                    for sport_s in item["infraSHPortS"]:
                        sh_port_s = cobra.model.infra.SHPortS(mo, **sport_s)
                        if "infraRsSpAccGrp" in sport_s:
                            cobra.model.infra.RsSpAccGrp(
                                sh_port_s, **sport_s["infraRsSpAccGrp"]
                            )
                        if "infraPortBlk" in sport_s:
                            for block in sport_s["infraPortBlk"]:
                                cobra.model.infra.PortBlk(sh_port_s, **block)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[infraSpAccPortPError]: " + str(e)

    def infraSpAccPortGrp(self, value):
        """
        Fabric > Access Policies > Interfaces > Spine Interfaces > Policy Groups
        """
        try:
            for item in value:
                funcp = cobra.model.infra.FuncP(self.__infra)
                mo = cobra.model.infra.SpAccPortGrp(funcp, **item)
                if "infraRsHIfPol" in item:
                    cobra.model.infra.RsHIfPol(mo, **item["infraRsHIfPol"])
                if "infraRsCdpIfPol" in item:
                    cobra.model.infra.RsCdpIfPol(mo, **item["infraRsCdpIfPol"])
                if "infraRsMacsecIfPol" in item:
                    cobra.model.infra.RsMacsecIfPol(mo, **item["infraRsMacsecIfPol"])
                if "infraRsAttEntP" in item:
                    cobra.model.infra.RsAttEntP(mo, **item["infraRsAttEntP"])
                if "infraRsLinkFlapPol" in item:
                    cobra.model.infra.RsLinkFlapPol(mo, **item["infraRsLinkFlapPol"])
                if "infraRsCoppIfPol" in item:
                    cobra.model.infra.RsCoppIfPol(mo, **item["infraRsCoppIfPol"])
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[infraSpAccPortGrpError]: " + str(e)

    def infraAccPortP(self, value):
        """
        Fabric > Access Policies > Interfaces > Leaf Interfaces > Profiles
        """
        try:
            for infraAccPortP in value:
                AccPortP = cobra.model.infra.AccPortP(self.__infra, **infraAccPortP)
                self.config.addMo(AccPortP)
                if "infraHPortS" in infraAccPortP:
                    for infraHPortS in infraAccPortP["infraHPortS"]:
                        HPortS = cobra.model.infra.HPortS(AccPortP, **infraHPortS)
                        self.config.addMo(HPortS)
                        if "infraRsAccBaseGrp" in infraHPortS:
                            if check("tDn", infraHPortS["infraRsAccBaseGrp"]):
                                RsAccBaseGrp = cobra.model.infra.RsAccBaseGrp(
                                    HPortS, **infraHPortS["infraRsAccBaseGrp"]
                                )
                                self.config.addMo(RsAccBaseGrp)
                        if "infraPortBlk" in infraHPortS:
                            for infraPortBlk in infraHPortS["infraPortBlk"]:
                                if check("fromPort", infraPortBlk):
                                    PortBlk = cobra.model.infra.PortBlk(
                                        HPortS, **infraPortBlk
                                    )
                                    self.config.addMo(PortBlk)
        except Exception as e:
            self._result.log = "[infraAccPortPError]: " + str(e)

    def infraFexP(self, value):
        """
        Fabric > Access Policies > Interfaces > Leaf Interfaces > FEX Profiles
        """
        try:
            for item in value:
                mo = cobra.model.infra.FexP(self.__infra, **item)
                if "infraHPortS" in item:
                    for port_s in item["infraHPortS"]:
                        h_port_s = cobra.model.infra.HPortS(mo, **port_s)
                        if "infraRsAccBaseGrp" in port_s:
                            cobra.model.infra.RsAccBaseGrp(
                                h_port_s, **port_s["infraRsAccBaseGrp"]
                            )
                        if "infraPortBlk" in port_s:
                            for block in port_s["infraPortBlk"]:
                                cobra.model.infra.PortBlk(h_port_s, **block)
                if "infraFexBndlGrp" in item:
                    cobra.model.infra.FexBndlGrp(mo, **item["infraFexBndlGrp"])
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[infraFexPError]: " + str(e)

    def infraAccPortGrp(self, value):
        """
        Fabric > Access Policies > Interfaces > Leaf Interfaces > Policy Groups > Access
        """
        try:
            for infraAccPortGrp in value:
                FuncP = cobra.model.infra.FuncP(self.__infra)
                AccPortGrp = cobra.model.infra.AccPortGrp(FuncP, **infraAccPortGrp)
                self.config.addMo(AccPortGrp)
                if "infraRsAttEntP" in infraAccPortGrp:
                    if check("tDn", infraAccPortGrp["infraRsAttEntP"]):
                        RsAttEntP = cobra.model.infra.RsAttEntP(
                            AccPortGrp, **infraAccPortGrp["infraRsAttEntP"]
                        )
                        self.config.addMo(RsAttEntP)
                if "infraRsStpIfPol" in infraAccPortGrp:
                    if check("tnStpIfPolName", infraAccPortGrp["infraRsStpIfPol"]):
                        RsStpIfPol = cobra.model.infra.RsStpIfPol(
                            AccPortGrp, **infraAccPortGrp["infraRsStpIfPol"]
                        )
                        self.config.addMo(RsStpIfPol)
                if "infraRsQosLlfcIfPol" in infraAccPortGrp:
                    if check(
                        "tnQosLlfcIfPolName", infraAccPortGrp["infraRsQosLlfcIfPol"]
                    ):
                        RsQosLlfcIfPol = cobra.model.infra.RsQosLlfcIfPol(
                            AccPortGrp, **infraAccPortGrp["infraRsQosLlfcIfPol"]
                        )
                        self.config.addMo(RsQosLlfcIfPol)
                if "infraRsQosIngressDppIfPol" in infraAccPortGrp:
                    if check(
                        "tnQosDppPolName", infraAccPortGrp["infraRsQosIngressDppIfPol"]
                    ):
                        RsQosIngressDppIfPol = cobra.model.infra.RsQosIngressDppIfPol(
                            AccPortGrp, **infraAccPortGrp["infraRsQosIngressDppIfPol"]
                        )
                        self.config.addMo(RsQosIngressDppIfPol)
                if "infraRsStormctrlIfPol" in infraAccPortGrp:
                    if check(
                        "tnStormctrlIfPolName", infraAccPortGrp["infraRsStormctrlIfPol"]
                    ):
                        RsStormctrlIfPol = cobra.model.infra.RsStormctrlIfPol(
                            AccPortGrp, **infraAccPortGrp["infraRsStormctrlIfPol"]
                        )
                        self.config.addMo(RsStormctrlIfPol)
                if "infraRsQosEgressDppIfPol" in infraAccPortGrp:
                    if check(
                        "tnQosDppPolName", infraAccPortGrp["infraRsQosEgressDppIfPol"]
                    ):
                        RsQosEgressDppIfPol = cobra.model.infra.RsQosEgressDppIfPol(
                            AccPortGrp, **infraAccPortGrp["infraRsQosEgressDppIfPol"]
                        )
                        self.config.addMo(RsQosEgressDppIfPol)
                if "infraRsMonIfInfraPol" in infraAccPortGrp:
                    if check(
                        "tnMonInfraPolName", infraAccPortGrp["infraRsMonIfInfraPol"]
                    ):
                        RsMonIfInfraPol = cobra.model.infra.RsMonIfInfraPol(
                            AccPortGrp, **infraAccPortGrp["infraRsMonIfInfraPol"]
                        )
                        self.config.addMo(RsMonIfInfraPol)
                if "infraRsMcpIfPol" in infraAccPortGrp:
                    if check("tnMcpIfPolName", infraAccPortGrp["infraRsMcpIfPol"]):
                        RsMcpIfPol = cobra.model.infra.RsMcpIfPol(
                            AccPortGrp, **infraAccPortGrp["infraRsMcpIfPol"]
                        )
                        self.config.addMo(RsMcpIfPol)
                if "infraRsMacsecIfPol" in infraAccPortGrp:
                    if check(
                        "tnMacsecIfPolName", infraAccPortGrp["infraRsMacsecIfPol"]
                    ):
                        RsMacsecIfPol = cobra.model.infra.RsMacsecIfPol(
                            AccPortGrp, **infraAccPortGrp["infraRsMacsecIfPol"]
                        )
                        self.config.addMo(RsMacsecIfPol)
                if "infraRsQosSdIfPol" in infraAccPortGrp:
                    if check("tnQosSdIfPolName", infraAccPortGrp["infraRsQosSdIfPol"]):
                        RsQosSdIfPol = cobra.model.infra.RsQosSdIfPol(
                            AccPortGrp, **infraAccPortGrp["infraRsQosSdIfPol"]
                        )
                        self.config.addMo(RsQosSdIfPol)
                if "infraRsCdpIfPol" in infraAccPortGrp:
                    if check("tnCdpIfPolName", infraAccPortGrp["infraRsCdpIfPol"]):
                        RsCdpIfPol = cobra.model.infra.RsCdpIfPol(
                            AccPortGrp, **infraAccPortGrp["infraRsCdpIfPol"]
                        )
                        self.config.addMo(RsCdpIfPol)
                if "infraRsL2IfPol" in infraAccPortGrp:
                    if check("tnL2IfPolName", infraAccPortGrp["infraRsL2IfPol"]):
                        RsL2IfPol = cobra.model.infra.RsL2IfPol(
                            AccPortGrp, **infraAccPortGrp["infraRsL2IfPol"]
                        )
                        self.config.addMo(RsL2IfPol)
                if "infraRsQosDppIfPol" in infraAccPortGrp:
                    if check("tnQosDppPolName", infraAccPortGrp["infraRsQosDppIfPol"]):
                        RsQosDppIfPol = cobra.model.infra.RsQosDppIfPol(
                            AccPortGrp, **infraAccPortGrp["infraRsQosDppIfPol"]
                        )
                        self.config.addMo(RsQosDppIfPol)
                if "infraRsCoppIfPol" in infraAccPortGrp:
                    if check("tnCoppIfPolName", infraAccPortGrp["infraRsCoppIfPol"]):
                        RsCoppIfPol = cobra.model.infra.RsCoppIfPol(
                            AccPortGrp, **infraAccPortGrp["infraRsCoppIfPol"]
                        )
                        self.config.addMo(RsCoppIfPol)
                if "infraRsDwdmIfPol" in infraAccPortGrp:
                    if check("tnDwdmIfPolName", infraAccPortGrp["infraRsDwdmIfPol"]):
                        RsDwdmIfPol = cobra.model.infra.RsDwdmIfPol(
                            AccPortGrp, **infraAccPortGrp["infraRsDwdmIfPol"]
                        )
                        self.config.addMo(RsDwdmIfPol)
                if "infraRsLinkFlapPol" in infraAccPortGrp:
                    if check(
                        "tnFabricLinkFlapPolName", infraAccPortGrp["infraRsLinkFlapPol"]
                    ):
                        RsLinkFlapPol = cobra.model.infra.RsLinkFlapPol(
                            AccPortGrp, **infraAccPortGrp["infraRsLinkFlapPol"]
                        )
                        self.config.addMo(RsLinkFlapPol)
                if "infraRsLldpIfPol" in infraAccPortGrp:
                    if check("tnLldpIfPolName", infraAccPortGrp["infraRsLldpIfPol"]):
                        RsLldpIfPol = cobra.model.infra.RsLldpIfPol(
                            AccPortGrp, **infraAccPortGrp["infraRsLldpIfPol"]
                        )
                        self.config.addMo(RsLldpIfPol)
                if "infraRsFcIfPol" in infraAccPortGrp:
                    if check("tnFcIfPolName", infraAccPortGrp["infraRsFcIfPol"]):
                        RsFcIfPol = cobra.model.infra.RsFcIfPol(
                            AccPortGrp, **infraAccPortGrp["infraRsFcIfPol"]
                        )
                        self.config.addMo(RsFcIfPol)
                if "infraRsQosPfcIfPol" in infraAccPortGrp:
                    if check(
                        "tnQosPfcIfPolName", infraAccPortGrp["infraRsQosPfcIfPol"]
                    ):
                        RsQosPfcIfPol = cobra.model.infra.RsQosPfcIfPol(
                            AccPortGrp, **infraAccPortGrp["infraRsQosPfcIfPol"]
                        )
                        self.config.addMo(RsQosPfcIfPol)
                if "infraRsHIfPol" in infraAccPortGrp:
                    if check("tnFabricHIfPolName", infraAccPortGrp["infraRsHIfPol"]):
                        RsHIfPol = cobra.model.infra.RsHIfPol(
                            AccPortGrp, **infraAccPortGrp["infraRsHIfPol"]
                        )
                        self.config.addMo(RsHIfPol)
                if "infraRsL2PortSecurityPol" in infraAccPortGrp:
                    if check(
                        "tnL2PortSecurityPolName",
                        infraAccPortGrp["infraRsL2PortSecurityPol"],
                    ):
                        RsL2PortSecurityPol = cobra.model.infra.RsL2PortSecurityPol(
                            AccPortGrp, **infraAccPortGrp["infraRsL2PortSecurityPol"]
                        )
                        self.config.addMo(RsL2PortSecurityPol)
                if "infraRsL2PortAuthPol" in infraAccPortGrp:
                    if check(
                        "tnL2PortAuthPolName", infraAccPortGrp["infraRsL2PortAuthPol"]
                    ):
                        RsL2PortAuthPol = cobra.model.infra.RsL2PortAuthPol(
                            AccPortGrp, **infraAccPortGrp["infraRsL2PortAuthPol"]
                        )
                        self.config.addMo(RsL2PortAuthPol)
        except Exception as e:
            self._result.log = "[infraAccPortGrpError]: " + str(e)

    def infraAccBndlGrp(self, value):
        """
        Fabric > Access Policies > Interfaces > Leaf Interfaces > Policy Groups > PC or VPC
        """
        try:
            for infraAccBndlGrp in value:
                FuncP = cobra.model.infra.FuncP(self.__infra)
                AccBndlGrp = cobra.model.infra.AccBndlGrp(FuncP, **infraAccBndlGrp)
                self.config.addMo(AccBndlGrp)
                if "infraRsAttEntP" in infraAccBndlGrp:
                    if check("tDn", infraAccBndlGrp["infraRsAttEntP"]):
                        RsAttEntP = cobra.model.infra.RsAttEntP(
                            AccBndlGrp, **infraAccBndlGrp["infraRsAttEntP"]
                        )
                        self.config.addMo(RsAttEntP)
                if "infraRsStpIfPol" in infraAccBndlGrp:
                    if check("tnStpIfPolName", infraAccBndlGrp["infraRsStpIfPol"]):
                        RsStpIfPol = cobra.model.infra.RsStpIfPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsStpIfPol"]
                        )
                        self.config.addMo(RsStpIfPol)
                if "infraRsQosLlfcIfPol" in infraAccBndlGrp:
                    if check(
                        "tnQosLlfcIfPolName", infraAccBndlGrp["infraRsQosLlfcIfPol"]
                    ):
                        RsQosLlfcIfPol = cobra.model.infra.RsQosLlfcIfPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsQosLlfcIfPol"]
                        )
                        self.config.addMo(RsQosLlfcIfPol)
                if "infraRsQosIngressDppIfPol" in infraAccBndlGrp:
                    if check(
                        "tnQosDppPolName", infraAccBndlGrp["infraRsQosIngressDppIfPol"]
                    ):
                        RsQosIngressDppIfPol = cobra.model.infra.RsQosIngressDppIfPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsQosIngressDppIfPol"]
                        )
                        self.config.addMo(RsQosIngressDppIfPol)
                if "infraRsStormctrlIfPol" in infraAccBndlGrp:
                    if check(
                        "tnStormctrlIfPolName", infraAccBndlGrp["infraRsStormctrlIfPol"]
                    ):
                        RsStormctrlIfPol = cobra.model.infra.RsStormctrlIfPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsStormctrlIfPol"]
                        )
                        self.config.addMo(RsStormctrlIfPol)
                if "infraRsQosEgressDppIfPol" in infraAccBndlGrp:
                    if check(
                        "tnQosDppPolName", infraAccBndlGrp["infraRsQosEgressDppIfPol"]
                    ):
                        RsQosEgressDppIfPol = cobra.model.infra.RsQosEgressDppIfPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsQosEgressDppIfPol"]
                        )
                        self.config.addMo(RsQosEgressDppIfPol)
                if "infraRsMonIfInfraPol" in infraAccBndlGrp:
                    if check(
                        "tnMonInfraPolName", infraAccBndlGrp["infraRsMonIfInfraPol"]
                    ):
                        RsMonIfInfraPol = cobra.model.infra.RsMonIfInfraPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsMonIfInfraPol"]
                        )
                        self.config.addMo(RsMonIfInfraPol)
                if "infraRsMcpIfPol" in infraAccBndlGrp:
                    if check("tnMcpIfPolName", infraAccBndlGrp["infraRsMcpIfPol"]):
                        RsMcpIfPol = cobra.model.infra.RsMcpIfPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsMcpIfPol"]
                        )
                        self.config.addMo(RsMcpIfPol)
                if "infraRsMacsecIfPol" in infraAccBndlGrp:
                    if check(
                        "tnMacsecIfPolName", infraAccBndlGrp["infraRsMacsecIfPol"]
                    ):
                        RsMacsecIfPol = cobra.model.infra.RsMacsecIfPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsMacsecIfPol"]
                        )
                        self.config.addMo(RsMacsecIfPol)
                if "infraRsQosSdIfPol" in infraAccBndlGrp:
                    if check("tnQosSdIfPolName", infraAccBndlGrp["infraRsQosSdIfPol"]):
                        RsQosSdIfPol = cobra.model.infra.RsQosSdIfPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsQosSdIfPol"]
                        )
                        self.config.addMo(RsQosSdIfPol)
                if "infraRsCdpIfPol" in infraAccBndlGrp:
                    if check("tnCdpIfPolName", infraAccBndlGrp["infraRsCdpIfPol"]):
                        RsCdpIfPol = cobra.model.infra.RsCdpIfPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsCdpIfPol"]
                        )
                        self.config.addMo(RsCdpIfPol)
                if "infraRsL2IfPol" in infraAccBndlGrp:
                    if check("tnL2IfPolName", infraAccBndlGrp["infraRsL2IfPol"]):
                        RsL2IfPol = cobra.model.infra.RsL2IfPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsL2IfPol"]
                        )
                        self.config.addMo(RsL2IfPol)
                if "infraRsQosDppIfPol" in infraAccBndlGrp:
                    if check("tnQosDppPolName", infraAccBndlGrp["infraRsQosDppIfPol"]):
                        RsQosDppIfPol = cobra.model.infra.RsQosDppIfPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsQosDppIfPol"]
                        )
                        self.config.addMo(RsQosDppIfPol)
                if "infraRsCoppIfPol" in infraAccBndlGrp:
                    if check("tnCoppIfPolName", infraAccBndlGrp["infraRsCoppIfPol"]):
                        RsCoppIfPol = cobra.model.infra.RsCoppIfPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsCoppIfPol"]
                        )
                        self.config.addMo(RsCoppIfPol)
                if "infraRsLldpIfPol" in infraAccBndlGrp:
                    if check("tnLldpIfPolName", infraAccBndlGrp["infraRsLldpIfPol"]):
                        RsLldpIfPol = cobra.model.infra.RsLldpIfPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsLldpIfPol"]
                        )
                        self.config.addMo(RsLldpIfPol)
                if "infraRsFcIfPol" in infraAccBndlGrp:
                    if check("tnFcIfPolName", infraAccBndlGrp["infraRsFcIfPol"]):
                        RsFcIfPol = cobra.model.infra.RsFcIfPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsFcIfPol"]
                        )
                        self.config.addMo(RsFcIfPol)
                if "infraRsQosPfcIfPol" in infraAccBndlGrp:
                    if check(
                        "tnQosPfcIfPolName", infraAccBndlGrp["infraRsQosPfcIfPol"]
                    ):
                        RsQosPfcIfPol = cobra.model.infra.RsQosPfcIfPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsQosPfcIfPol"]
                        )
                        self.config.addMo(RsQosPfcIfPol)
                if "infraRsHIfPol" in infraAccBndlGrp:
                    if check("tnFabricHIfPolName", infraAccBndlGrp["infraRsHIfPol"]):
                        RsHIfPol = cobra.model.infra.RsHIfPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsHIfPol"]
                        )
                        self.config.addMo(RsHIfPol)
                if "infraRsL2PortSecurityPol" in infraAccBndlGrp:
                    if check(
                        "tnL2PortSecurityPolName",
                        infraAccBndlGrp["infraRsL2PortSecurityPol"],
                    ):
                        RsL2PortSecurityPol = cobra.model.infra.RsL2PortSecurityPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsL2PortSecurityPol"]
                        )
                        self.config.addMo(RsL2PortSecurityPol)
                if "infraRsL2PortAuthPol" in infraAccBndlGrp:
                    if check(
                        "tnL2PortAuthPolName", infraAccBndlGrp["infraRsL2PortAuthPol"]
                    ):
                        RsL2PortAuthPol = cobra.model.infra.RsL2PortAuthPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsL2PortAuthPol"]
                        )
                        self.config.addMo(RsL2PortAuthPol)
                if "infraRsLacpPol" in infraAccBndlGrp:
                    if check("tnLacpLagPolName", infraAccBndlGrp["infraRsLacpPol"]):
                        RsLacpPol = cobra.model.infra.RsLacpPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsLacpPol"]
                        )
                        self.config.addMo(RsLacpPol)
                if "infraRsLinkFlapPol" in infraAccBndlGrp:
                    if check(
                        "tnFabricLinkFlapPolName", infraAccBndlGrp["infraRsLinkFlapPol"]
                    ):
                        RsLinkFlapPol = cobra.model.infra.RsLinkFlapPol(
                            AccBndlGrp, **infraAccBndlGrp["infraRsLinkFlapPol"]
                        )
                        self.config.addMo(RsLinkFlapPol)
        except Exception as e:
            self._result.log = "[infraAccBndlGrpError]: " + str(e)

    def fabricProtPol(self, value):
        """
        Fabric > Access Policies > Policies > Switch > Virtual Port Channel default
        """
        try:
            for item in value:
                fabric_inst = cobra.model.fabric.Inst(self.__uni)
                mo = cobra.model.fabric.ProtPol(fabric_inst, **item)
                if "fabricExplicitGEp" in item:
                    for explicit_gep in item["fabricExplicitGEp"]:
                        fabric_explicit_gep = cobra.model.fabric.ExplicitGEp(
                            mo, **explicit_gep
                        )
                        if "fabricRsVpcInstPol" in explicit_gep:
                            cobra.model.fabric.RsVpcInstPol(
                                fabric_explicit_gep,
                                **explicit_gep["fabricRsVpcInstPol"],
                            )
                        if "fabricNodePEp" in explicit_gep:
                            for node_pep in explicit_gep["fabricNodePEp"]:
                                cobra.model.fabric.NodePEp(
                                    fabric_explicit_gep, **node_pep
                                )
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[fabricProtPolError]: " + str(e)

    def fabricHIfPol(self, value):
        """
        Fabric > Access Policies > Policies > Interface > Link Level
        """
        try:
            for item in value:
                mo = cobra.model.fabric.HIfPol(self.__infra, **item)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[fabricHIfPolError]: " + str(e)

    def qosPfcIfPol(self, value):
        """
        Fabric > Access Policies > Policies > Interface > Priority Flow Control
        """
        try:
            for item in value:
                mo = cobra.model.qos.PfcIfPol(self.__infra, **item)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[qosPfcIfPolError]: " + str(e)

    def cdpIfPol(self, value):
        """
        Fabric > Access Policies > Policies > Interface > CDP Interface
        """
        try:
            for item in value:
                mo = cobra.model.cdp.IfPol(self.__infra, **item)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[cdpIfPolError]: " + str(e)

    def lldpIfPol(self, value):
        """
        Fabric > Access Policies > Policies > Interface > LLDP Interface
        """
        try:
            for item in value:
                mo = cobra.model.lldp.IfPol(self.__infra, **item)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[lldpIfPolError]: " + str(e)

    def lacpLagPol(self, value):
        """
        Fabric > Access Policies > Policies > Interface > Port Channel
        """
        try:
            for item in value:
                mo = cobra.model.lacp.LagPol(self.__infra, **item)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[lacpLagPolError]: " + str(e)

    def stpIfPol(self, value) -> None:
        """
        Fabric > Access Policies > Policies > Interface > Spanning Tree Interface
        """
        try:
            for item in value:
                mo = cobra.model.stp.IfPol(self.__infra, **item)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[stpIfPolError]: " + str(e)

    def stormctrlIfPol(self, value) -> None:
        """
        Fabric > Access Policies > Policies > Interface > Storm Control
        """
        try:
            for item in value:
                mo = cobra.model.stormctrl.IfPol(self.__infra, **item)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[stormctrlIfPolError]: " + str(e)

    def mcpIfPol(self, value):
        """
        Fabric > Access Policies > Policies > Interface > MCP Interface
        """
        try:
            for item in value:
                mo = cobra.model.mcp.IfPol(self.__infra, **item)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[mcpIfPolError]: " + str(e)

    def infraAttEntityP(self, value):
        """
        Fabric > Access Policies > Policies > Global > Attachable Access Entity Profiles
        """
        try:
            for infraAttEntityP in value:
                AttEntityP = cobra.model.infra.AttEntityP(
                    self.__infra, **infraAttEntityP
                )
                self.config.addMo(AttEntityP)
                if "infraRsDomP" in infraAttEntityP:
                    for infraRsDomP in infraAttEntityP["infraRsDomP"]:
                        RsDomP = cobra.model.infra.RsDomP(AttEntityP, **infraRsDomP)
                        self.config.addMo(RsDomP)
        except Exception as e:
            self._result.log = "[infraAttEntityPError]: " + str(e)

    def fvnsVlanInstP(self, value):
        """
        Fabric > Access Policies > Pools > VLAN
        """
        try:
            for fvnsVlanInstP in value:
                VlanInstP = cobra.model.fvns.VlanInstP(self.__infra, **fvnsVlanInstP)
                self.config.addMo(VlanInstP)
                if "fvnsEncapBlk" in fvnsVlanInstP:
                    for fvnsEncapBlk in fvnsVlanInstP["fvnsEncapBlk"]:
                        EncapBlk = cobra.model.fvns.EncapBlk(VlanInstP, **fvnsEncapBlk)
                        self.config.addMo(EncapBlk)
        except Exception as e:
            self._result.log = "[fvnsVlanInstPError]: " + str(e)

    def physDomP(self, value):
        """
        Fabric > Access Policies > Physical and External Domains > Physical Domain
        """
        try:
            for physDomP in value:
                DomP = cobra.model.phys.DomP(self.__uni, **physDomP)
                self.config.addMo(DomP)
                if "infraRsVlanNs" in physDomP:
                    RsVlanNs = cobra.model.infra.RsVlanNs(
                        DomP, **physDomP["infraRsVlanNs"]
                    )
                    self.config.addMo(RsVlanNs)
        except Exception as e:
            self._result.log = "[physDomPError]: " + str(e)

    def l3extDomP(self, value):
        """
        Fabric > Access Policies > Physical and External Domains > L3 Domains
        """
        try:
            for item in value:
                mo = cobra.model.l3ext.DomP(self.__uni, **item)
                if "infraRsVlanNs" in item:
                    cobra.model.infra.RsVlanNs(mo, **item["infraRsVlanNs"])
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[l3extDomPError]: " + str(e)

    def l2extDomP(self, value):
        """
        Fabric > Access Policies > Physical and External Domains > External Bridged Domains
        """
        try:
            for item in value:
                mo = cobra.model.l2ext.DomP(self.__uni, **item)
                if "infraRsVlanNs" in item:
                    cobra.model.infra.RsVlanNs(mo, **item["infraRsVlanNs"])
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[l2extDomPError]: " + str(e)

    def bgpInstPol(self, value) -> None:
        """
        System Settings > All Tenants
        """
        try:
            for bgpInstPol in value:
                InstPol = cobra.model.bgp.InstPol(self.__fabric_inst, **bgpInstPol)
                if "bgpAsP" in bgpInstPol:
                    if check("asn", bgpInstPol["bgpAsP"]):
                        AsP = cobra.model.bgp.AsP(InstPol, **bgpInstPol["bgpAsP"])
                        self.config.addMo(AsP)
                if "bgpRRP" in bgpInstPol:
                    RRP = cobra.model.bgp.RRP(InstPol)
                    self.config.addMo(RRP)
                    for bgpRRP in bgpInstPol["bgpRRP"]:
                        if "bgpRRNodePEp" in bgpRRP:
                            RRNodePEp = cobra.model.bgp.RRNodePEp(
                                RRP, **bgpRRP["bgpRRNodePEp"]
                            )
                            self.config.addMo(RRNodePEp)
                if "ExtRRP" in bgpInstPol:
                    ExtRRP = cobra.model.bgp.ExtRRP(InstPol)
                    for ExtRRP in bgpInstPol["ExtRRP"]:
                        RRNodePEp = cobra.model.bgp.RRNodePEp(ExtRRP, **ExtRRP)
                        self.config.addMo(RRNodePEp)
        except Exception as e:
            self._result.log = "[bgpInstPolError]: " + str(e)

    def coopPol(self, value) -> None:
        """
        System Settings > COOP Group
        """
        try:
            mo = cobra.model.coop.Pol(self.__fabric_inst, **value)
            self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[coopPolError]: " + str(e)

    def datetimeFormat(self, value) -> None:
        """
        System Settings > Date and Time
        """
        try:
            mo = cobra.model.datetime.Format(self.__fabric_inst, **value)
            self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[datetimeFormatError]: " + str(e)

    def aaaFabricSec(self, value) -> None:
        """
        System Settings > Fabric Security
        """
        try:
            UserEp = cobra.model.aaa.UserEp(self.__uni)
            mo = cobra.model.aaa.FabricSec(UserEp, **value)
            self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[aaaFabricSecError]: " + str(e)

    def aaaPreLoginBanner(self, value) -> None:
        """
        System Settings > System Alias and Banners
        """
        try:
            UserEp = cobra.model.aaa.UserEp(self.__uni)
            mo = cobra.model.aaa.PreLoginBanner(UserEp, **value)
            self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[aaaPreLoginBannerError]: " + str(e)

    def pkiExportEncryptionKey(self, value) -> None:
        """
        System Settings > Fabric Security
        """
        try:
            mo = cobra.model.pki.ExportEncryptionKey(self.__uni, **value)
            self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[pkiExportEncryptionKeyError]: " + str(e)

    def epLoopProtectP(self, value) -> None:
        """
        System Settings > Enpoint Controls > The endpoint loop protection
        """
        try:
            mo = cobra.model.ep.LoopProtectP(self.__infra, **value)
            self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[epLoopProtectPError]: " + str(e)

    def epControlP(self, value) -> None:
        """
        System Settings > Enpoint Controls > Rogue EP Control
        """
        try:
            mo = cobra.model.ep.ControlP(self.__infra, **value)
            self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[epControlPError]: " + str(e)

    def epIpAgingP(self, value) -> None:
        """
        System Settings > Enpoint Controls > IP Aging
        """
        try:
            mo = cobra.model.ep.IpAgingP(self.__infra, **value)
            self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[epIpAgingPError]: " + str(e)

    def infraSetPol(self, value) -> None:
        """
        System Settings > Fabric-Wide Settings
        """
        try:
            mo = cobra.model.infra.SetPol(self.__infra, **value)
            self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[infraSetPolError]: " + str(e)

    def isisDomPol(self, value) -> None:
        """
        System Settings > ISIS Policy
        """
        try:
            mo = cobra.model.isis.DomPol(self.__fabric_inst, **value)
            self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[isisDomPolError]: " + str(e)

    def infraPortTrackPol(self, value) -> None:
        """
        System Settings > Port Tracking
        """
        try:
            mo = cobra.model.infra.PortTrackPol(self.__infra, **value)
            self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[infraPortTrackPolError]: " + str(e)

    def mcpInstPol(self, value) -> None:
        """
        Fabric > Access Policies > Global > MCP Instance Policy default
        """
        try:
            for mcpInstPol in value:
                mo = cobra.model.mcp.InstPol(self.__infra, **mcpInstPol)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[mcpInstPolPolError]: " + str(e)

    def fabricNodeControl(self, value) -> None:
        """
        Fabric > Fabric Policies > Policies > Monitoring > Fabric Node Controls > default
        """
        try:
            for fabricNodeControl in value:
                mo = cobra.model.fabric.NodeControl(self.__fabric_inst, **fabricNodeControl)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[fabricNodeControlError]: " + str(e)

    def geoSite(self, value) -> None:
        """
        Fabric > Fabric Policies > Policies > Geolocation
        """
        try:
            Inst = cobra.model.fabric.Inst(self.__uni)
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
                                                Row = cobra.model.geo.Row(
                                                    Room, **geoRow
                                                )
                                                self.config.addMo(Row)
                                                if "geoRack" in geoRow:
                                                    for geoRack in geoRow["geoRack"]:
                                                        if check("name", geoRack):
                                                            Rack = cobra.model.geo.Rack(
                                                                Row, **geoRack
                                                            )
                                                            self.config.addMo(Rack)
                                                            if (
                                                                "geoRsNodeLocation"
                                                                in geoRack
                                                            ):
                                                                for (
                                                                    geoRsNodeLocation
                                                                ) in geoRack[
                                                                    "geoRsNodeLocation"
                                                                ]:
                                                                    if check(
                                                                        "tDn",
                                                                        geoRsNodeLocation,
                                                                    ):
                                                                        RsNodeLocation = cobra.model.geo.RsNodeLocation(
                                                                            Rack,
                                                                            **geoRsNodeLocation,
                                                                        )
                                                                        self.config.addMo(
                                                                            RsNodeLocation
                                                                        )
        except Exception as e:
            self._result.log = "[fabricNodeControlError]: " + str(e)

    def latencyPtpMode(self, value) -> None:
        """
        Fabric > Fabric Policies > Policies > Monitoring > Fabric Node Controls > default
        """
        try:
            mo = cobra.model.latency.PtpMode(self.__fabric_inst, **value)
            self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[latencyPtpModeError]: " + str(e)

    def infrazoneZoneP(self, value) -> None:
        """
        Fabric > Fabric Policies > Policies > Monitoring > Fabric Node Controls > default
        """
        try:
            ZoneP = cobra.model.infrazone.ZoneP(self.__infra, **value)
            if "infrazoneZone" in value:
                for infrazoneZone in value["infrazoneZone"]:
                    if "name" in infrazoneZone:
                        Zone = cobra.model.infrazone.Zone(ZoneP, **infrazoneZone)
                        self.config.addMo(Zone)
        except Exception as e:
            self._result.log = "[infrazoneZoneError]: " + str(e)


def check(key, value):
    if key in value:
        if not value[key] == "":
            return True
    return False


def not_nan(value):
    return not any(valor == "nan" for valor in value.values())
