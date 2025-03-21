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
from typing import Optional
from datetime import datetime

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
        self.__infra = cobra.model.infra.Infra(self.__uni)
        self.config = cobra.mit.request.ConfigRequest()

        # --------------   Output Information

        self._result = CobraResult()

    # -------------------------------------------------   Control

    def render(self, jinja: JinjaResult) -> CobraResult:
        try:
            if jinja.success:
                for key, value in jinja.output.items():
                    try:
                        caller = getattr(CobraClass, key)
                        caller(self, value)
                    except AttributeError as e:
                        self._result.log = "[AttributeError]: " + str(e)

                if self.config.configMos:
                    self._result.output = self.config
                    self._result.success = True
                    self._result.log = (
                        "[CobraClass]: Template was sucessfully rendered."
                    )
            else:
                self._result.log = jinja.log
                self._result.success = False
        except TypeError as e:
            self._result.log = "[TypeError]: " + str(e)
        except Exception as e:
            self._result.log = "[CobraError]: " + str(e)

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
            for item in value:
                mo = cobra.model.fv.Ap(self.tenant(**item), **item)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[fvApError]: " + str(e)
        return self._mo

    def fvAEPg(self, value) -> None:
        """
        Tenants > Application Profiles > Application EPGs
        """
        try:
            for item in value:
                mo = cobra.model.fv.AEPg(self.ap(**item), **item)
                if "fvRsBd" in item:
                    cobra.model.fv.RsBd(mo, **item["fvRsBd"])
                if "fvRsDomAtt" in item:
                    for rs_dom_att in item["fvRsDomAtt"]:
                        cobra.model.fv.RsDomAtt(mo, **rs_dom_att)
                if "fvRsPathAtt" in item:
                    for rs_path_att in item["fvRsPathAtt"]:
                        cobra.model.fv.RsPathAtt(mo, **rs_path_att)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[fvAEPgError]: " + str(e)

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
            for item in value:
                mo = cobra.model.fv.BD(self.tenant(**item), **item)
                if "fvRsCtx" in item:
                    cobra.model.fv.RsCtx(mo, **item["fvRsCtx"])
                if "fvSubnet" in item:
                    cobra.model.fv.Subnet(mo, **item["fvSubnet"])
                if "fvRsBDToOut" in item:
                    cobra.model.fv.RsBDToOut(mo, **item["fvRsBDToOut"])
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[fvBDError]: " + str(e)

    def fvCtx(self, value) -> None:
        """
        Tenants > Networking > VRFs
        """
        try:
            for item in value:
                mo = cobra.model.fv.Ctx(self.tenant(**item), **item)
                if "fvRsVrfValidationPol" in item:
                    cobra.model.fv.RsVrfValidationPol(
                        mo, **item["fvRsVrfValidationPol"]
                    )
                if "fvRsOspfCtxPol" in item:
                    cobra.model.fv.RsOspfCtxPol(mo, **item["fvRsOspfCtxPol"])
                if "fvRsBgpCtxPol" in item:
                    cobra.model.fv.RsBgpCtxPol(mo, **item["fvRsBgpCtxPol"])
                if "fvRsCtxToEpRet" in item:
                    cobra.model.fv.RsCtxToEpRet(mo, **item["fvRsCtxToEpRet"])
                if "fvRsCtxToExtRouteTagPol" in item:
                    cobra.model.fv.RsCtxToExtRouteTagPol(
                        mo, **item["fvRsCtxToExtRouteTagPol"]
                    )
                self.config.addMo(mo)
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

    def tenant_address_pool(self, value):
        """
        Tenants > IP Address Pools
        """
        return self._mo

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
    
    def fabricRsOosPath(self, value):
        """
        Fabric > RsOosPath
        """
        try:
            for item in value:
                fabric_inst = cobra.model.fabric.Inst(self.__uni)
                ser_pol = cobra.model.fabric.OOServicePol(fabric_inst)
                mo = cobra.model.fabric.RsOosPath(ser_pol, **item)
                self.config.addMo(mo)
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

    def fabricNodeIdentP(self, value):
        """
        Fabric > Inventory > Fabric Membership
        """
        try:
            for item in value:
                ctrlr_inst = cobra.model.ctrlr.Inst(self.__uni)
                node_ident_pol = cobra.model.fabric.NodeIdentPol(ctrlr_inst)
                mo = cobra.model.fabric.NodeIdentP(node_ident_pol, **item)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[fabricNodeIdentPError]: " + str(e)

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
            for item in value:
                fabric_inst = cobra.model.fabric.Inst(self.__uni)
                mo = cobra.model.datetime.Pol(fabric_inst, **item)
                if "datetimeNtpAuthKey" in item:
                    for ntp_auth_key in item["datetimeNtpAuthKey"]:
                        cobra.model.datetime.NtpAuthKey(mo, **ntp_auth_key)
                if "datetimeNtpProv" in item:
                    for ntp_prov in item["datetimeNtpProv"]:
                        mo_ntp_prov = cobra.model.datetime.NtpProv(mo, **ntp_prov)
                        if "datetimeRsNtpProvToNtpAuthKey" in ntp_prov:
                            cobra.model.datetime.RsNtpProvToNtpAuthKey(
                                mo_ntp_prov, **ntp_prov["datetimeRsNtpProvToNtpAuthKey"]
                            )
                        if "datetimeRsNtpProvToEpg" in ntp_prov:
                            cobra.model.datetime.RsNtpProvToEpg(
                                mo_ntp_prov, **ntp_prov["datetimeRsNtpProvToEpg"]
                            )
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[datetimePolError]: " + str(e)

    def snmpPol(self, value):
        """
        Fabric > Fabric Policies > Policies > Pod > SNMP
        """

        try:
            for item in value:
                fabric_inst = cobra.model.fabric.Inst(self.__uni)
                mo = cobra.model.snmp.Pol(fabric_inst, **item)
                if "snmpClientGrpP" in item:
                    for client_grp_p in item["snmpClientGrpP"]:
                        mo_client_grp_p = cobra.model.snmp.ClientGrpP(
                            mo, **client_grp_p
                        )
                        if "snmpRsEpg" in client_grp_p:
                            cobra.model.snmp.RsEpg(
                                mo_client_grp_p, **client_grp_p["snmpRsEpg"]
                            )
                        if "snmpClientP" in client_grp_p:
                            for client_p in client_grp_p["snmpClientP"]:
                                cobra.model.snmp.ClientP(mo_client_grp_p, **client_p)
                if "snmpUserP" in item:
                    for user_p in item["snmpUserP"]:
                        cobra.model.snmp.UserP(mo, **user_p)
                if "snmpCommunityP" in item:
                    for community_p in item["snmpCommunityP"]:
                        cobra.model.snmp.CommunityP(mo, **community_p)
                if "snmpTrapFwdServerP" in item:
                    for trap_fwd in item["snmpTrapFwdServerP"]:
                        cobra.model.snmp.TrapFwdServerP(mo, **trap_fwd)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[snmpPolError]: " + str(e)

    def commPol(self, value):
        """
        Fabric > Fabric Policies > Policies > Pod > Management Access
        """
        try:
            for item in value:
                fabric_inst = cobra.model.fabric.Inst(self.__uni)
                mo = cobra.model.comm.Pol(fabric_inst, **item)
                if "commTelnet" in item:
                    cobra.model.comm.Telnet(mo, **item["commTelnet"])
                if "commSsh" in item:
                    cobra.model.comm.Ssh(mo, **item["commSsh"])
                if "commShellinabox" in item:
                    cobra.model.comm.Shellinabox(mo, **item["commShellinabox"])
                if "commHttps" in item:
                    cobra.model.comm.Https(mo, **item["commHttps"])
                if "commHttp" in item:
                    cobra.model.comm.Http(mo, **item["commHttp"])
                self.config.addMo(mo)
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
            for item in value:
                mo = cobra.model.infra.NodeP(self.__infra, **item)
                if "infraLeafS" in item:
                    for leaf_s in item["infraLeafS"]:
                        mo_leaf_s = cobra.model.infra.LeafS(mo, **leaf_s)
                        if "infraRsAccNodePGrp" in leaf_s:
                            cobra.model.infra.RsAccNodePGrp(
                                mo_leaf_s, **leaf_s["infraRsAccNodePGrp"]
                            )
                        if "infraNodeBlk" in leaf_s:
                            cobra.model.infra.NodeBlk(
                                mo_leaf_s, **leaf_s["infraNodeBlk"]
                            )
                if "infraRsAccPortP" in item:
                    cobra.model.infra.RsAccPortP(mo, **item["infraRsAccPortP"])
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[infraNodePError]: " + str(e)

    def infraAccNodePGrp(self, value):
        """
        Fabric > Access Policies > Switches > Leaf Switches > Policy Groups
        """
        try:
            for item in value:
                funcp = cobra.model.infra.FuncP(self.__infra)
                mo = cobra.model.infra.AccNodePGrp(funcp, **item)
                if "infraRsMstInstPol" in item:
                    cobra.model.infra.RsMstInstPol(mo, **item["infraRsMstInstPol"])
                if "infraRsBfdIpv4InstPol" in item:
                    cobra.model.infra.RsBfdIpv4InstPol(
                        mo, **item["infraRsBfdIpv4InstPol"]
                    )
                if "infraRsBfdIpv6InstPol" in item:
                    cobra.model.infra.RsBfdIpv6InstPol(
                        mo, **item["infraRsBfdIpv6InstPol"]
                    )
                if "infraRsBfdMhIpv4InstPol" in item:
                    cobra.model.infra.RsBfdMhIpv4InstPol(
                        mo, **item["infraRsBfdMhIpv4InstPol"]
                    )
                if "infraRsBfdMhIpv6InstPol" in item:
                    cobra.model.infra.RsBfdMhIpv6InstPol(
                        mo, **item["infraRsBfdMhIpv6InstPol"]
                    )
                if "infraRsFcInstPol" in item:
                    cobra.model.infra.RsFcInstPol(mo, **item["infraRsFcInstPol"])
                if "infraRsPoeInstPol" in item:
                    cobra.model.infra.RsPoeInstPol(mo, **item["infraRsPoeInstPol"])
                if "infraRsFcFabricPol" in item:
                    cobra.model.infra.RsFcFabricPol(mo, **item["infraRsFcFabricPol"])
                if "infraRsMonNodeInfraPol" in item:
                    cobra.model.infra.RsMonNodeInfraPol(
                        mo, **item["infraRsMonNodeInfraPol"]
                    )
                if "infraRsLeafCoppProfile" in item:
                    cobra.model.infra.RsLeafCoppProfile(
                        mo, **item["infraRsLeafCoppProfile"]
                    )
                if "infraRsTopoctrlFwdScaleProfPol" in item:
                    cobra.model.infra.RsTopoctrlFwdScaleProfPol(
                        mo, **item["infraRsTopoctrlFwdScaleProfPol"]
                    )
                if "infraRsTopoctrlFastLinkFailoverInstPol" in item:
                    cobra.model.infra.RsTopoctrlFastLinkFailoverInstPol(
                        mo, **item["infraRsTopoctrlFastLinkFailoverInstPol"]
                    )
                if "infraRsL2NodeAuthPol" in item:
                    cobra.model.infra.RsL2NodeAuthPol(
                        mo, **item["infraRsL2NodeAuthPol"]
                    )
                if "infraRsIaclLeafProfile" in item:
                    cobra.model.infra.RsIaclLeafProfile(
                        mo, **item["infraRsIaclLeafProfile"]
                    )
                if "infraRsEquipmentFlashConfigPol" in item:
                    cobra.model.infra.RsEquipmentFlashConfigPol(
                        mo, **item["infraRsEquipmentFlashConfigPol"]
                    )
                if "infraRsLeafPGrpToCdpIfPol" in item:
                    cobra.model.infra.RsLeafPGrpToCdpIfPol(
                        mo, **item["infraRsLeafPGrpToCdpIfPol"]
                    )
                if "infraRsLeafPGrpToLldpIfPol" in item:
                    cobra.model.infra.RsLeafPGrpToLldpIfPol(
                        mo, **item["infraRsLeafPGrpToLldpIfPol"]
                    )
                self.config.addMo(mo)
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
            for item in value:
                mo = cobra.model.infra.AccPortP(self.__infra, **item)
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
                self.config.addMo(mo)
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
            for item in value:
                funcp = cobra.model.infra.FuncP(self.__infra)
                mo = cobra.model.infra.AccPortGrp(funcp, **item)
                if "infraRsHIfPol" in item:
                    cobra.model.infra.RsHIfPol(mo, **item["infraRsHIfPol"])
                if "infraRsMcpIfPol" in item:
                    cobra.model.infra.RsMcpIfPol(mo, **item["infraRsMcpIfPol"])
                if "infraRsCdpIfPol" in item:
                    cobra.model.infra.RsCdpIfPol(mo, **item["infraRsCdpIfPol"])
                if "infraRsLldpIfPol" in item:
                    cobra.model.infra.RsLldpIfPol(mo, **item["infraRsLldpIfPol"])
                if "infraRsStpIfPol" in item:
                    cobra.model.infra.RsStpIfPol(mo, **item["infraRsStpIfPol"])
                if "infraRsStormctrlIfPol" in item:
                    cobra.model.infra.RsStormctrlIfPol(
                        mo, **item["infraRsStormctrlIfPol"]
                    )
                if "infraRsMonIfInfraPol" in item:
                    cobra.model.infra.RsMonIfInfraPol(
                        mo, **item["infraRsMonIfInfraPol"]
                    )
                if "infraRsQosPfcIfPol" in item:
                    cobra.model.infra.RsQosPfcIfPol(mo, **item["infraRsQosPfcIfPol"])
                if "infraRsAttEntP" in item:
                    cobra.model.infra.RsAttEntP(mo, **item["infraRsAttEntP"])
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[infraAccPortGrpError]: " + str(e)

    def infraAccBndlGrp(self, value):
        """
        Fabric > Access Policies > Interfaces > Leaf Interfaces > Policy Groups > PC or VPC
        """
        try:
            for item in value:
                funcp = cobra.model.infra.FuncP(self.__infra)
                mo = cobra.model.infra.AccBndlGrp(funcp, **item)
                if "infraRsHIfPol" in item:
                    cobra.model.infra.RsHIfPol(mo, **item["infraRsHIfPol"])
                if "infraRsMcpIfPol" in item:
                    cobra.model.infra.RsMcpIfPol(mo, **item["infraRsMcpIfPol"])
                if "infraRsCdpIfPol" in item:
                    cobra.model.infra.RsCdpIfPol(mo, **item["infraRsCdpIfPol"])
                if "infraRsLldpIfPol" in item:
                    cobra.model.infra.RsLldpIfPol(mo, **item["infraRsLldpIfPol"])
                if "infraRsStpIfPol" in item:
                    cobra.model.infra.RsStpIfPol(mo, **item["infraRsStpIfPol"])
                if "infraRsStormctrlIfPol" in item:
                    cobra.model.infra.RsStormctrlIfPol(
                        mo, **item["infraRsStormctrlIfPol"]
                    )
                if "infraRsLacpPol" in item:
                    cobra.model.infra.RsLacpPol(mo, **item["infraRsLacpPol"])
                if "infraRsMonIfInfraPol" in item:
                    cobra.model.infra.RsMonIfInfraPol(
                        mo, **item["infraRsMonIfInfraPol"]
                    )
                if "infraRsQosPfcIfPol" in item:
                    cobra.model.infra.RsQosPfcIfPol(mo, **item["infraRsQosPfcIfPol"])
                if "infraRsAttEntP" in item:
                    cobra.model.infra.RsAttEntP(mo, **item["infraRsAttEntP"])
                self.config.addMo(mo)
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
            for item in value:
                mo = cobra.model.infra.AttEntityP(self.__infra, **item)
                if "infraRsDomP" in item:
                    for domain in item["infraRsDomP"]:
                        cobra.model.infra.RsDomP(mo, **domain)
                if "infraProvAcc" in item:
                    prov_acc = cobra.model.infra.ProvAcc(mo, item["infraProvAcc"])
                    cobra.model.infra.RsFuncToEpg(
                        prov_acc,
                        encap=item["infraProvAcc"]["encap"],
                        instrImedcy="lazy",
                        mode="regular",
                        primaryEncap="unknown",
                        tDn="uni/tn-infra/ap-access/epg-default",
                    )
                    cobra.model.dhcp.InfraProvP(prov_acc, mode="controller")
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[infraAttEntityPError]: " + str(e)

    def fvnsVlanInstP(self, value):
        """
        Fabric > Access Policies > Pools > VLAN
        """
        try:
            for item in value:
                mo = cobra.model.fvns.VlanInstP(self.__infra, **item)
                if "fvnsEncapBlk" in item:
                    for block in item["fvnsEncapBlk"]:
                        cobra.model.fvns.EncapBlk(mo, **block)
                self.config.addMo(mo)
        except Exception as e:
            self._result.log = "[fvnsVlanInstPError]: " + str(e)

    def physDomP(self, value):
        """
        Fabric > Access Policies > Physical and External Domains > Physical Domain
        """
        try:
            for item in value:
                mo = cobra.model.phys.DomP(self.__uni, **item)
                if "infraRsVlanNs" in item:
                    cobra.model.infra.RsVlanNs(mo, **item["infraRsVlanNs"])
                self.config.addMo(mo)
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
