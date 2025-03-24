# Copyright 2020 Jorge C. Riveros
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ACI module configuration for the ACI Python SDK (cobra)."""

import requests
import urllib3
import json
import pandas as pd
import xml.dom.minidom
import cobra.mit.session
import cobra.mit.access
import cobra.mit.request
from datetime import datetime
from pathlib import Path
from typing import Union
from .jinja import JinjaClass
from .cobra import CobraClass


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ------------------------------------------   Deployer Result Class


class DeployResult:
    """
    The DeployResult class return the results for Deployer logs
    """

    def __init__(self):
        self.date = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
        self._output = dict()
        self._success = False
        self._log = dict()

    @property
    def output(self) -> dict:
        return self._output

    @property
    def success(self) -> bool:
        return self._success

    @property
    def log(self) -> dict:
        return self._log

    @property
    def json(self) -> list:
        return [
            {
                "date": self.date,
                "output": self._output,
                "success": self._success,
                "log": self._log,
            }
        ]

    @success.setter
    def success(self, value) -> None:
        self._success = value

    @log.setter
    def log(self, value) -> None:
        self._log.update(value)

    @output.setter
    def output(self, value) -> None:
        self._output.update(value)

    def __str__(self):
        return "DeployerResult"


# ------------------------------------------   Deployer Class


class DeployClass:
    """
    Cobra DeployClass from Cobra SDK
    \n username: APIC username
    \n password: APIC username
    \n ip: APIC IPv4
    \n testing: True or False
    \n log: Logging file path
    \n logging: True or False
    """

    def __init__(self, **kwargs):
        # --------------   Render Information
        self._template: list = kwargs.get("template", [])
        self.log = kwargs.get("log", "logging.json")

        # --------------   Login Information
        self._username = kwargs.get("username", "admin")
        self.__password = kwargs.get("password", "Cisco123!")
        self.__token = kwargs.get("token", None)
        self._timeout = kwargs.get("timeout", 180)
        self._secure = kwargs.get("secure", False)
        self.testing = kwargs.get("testing", False)
        self.logging = kwargs.get("logging", False)
        self.render_to_xml = kwargs.get("render_to_xml", False)

        # --------------   Controller Information
        self._ip = kwargs.get("ip", "127.0.0.1")
        self._url = "https://{}".format(self._ip)

        # --------------   Session Class
        self._session = cobra.mit.session.LoginSession(
            self._url,
            self._username,
            self.__password,
            self._secure,
            self._timeout,
        )
        self.__modir = cobra.mit.access.MoDirectory(self._session)

        self._result = DeployResult()

    # -------------------------------------------------   Control

    def login(self) -> bool:
        """
        Login with credentials
        """
        try:
            self.__modir.login()
            return True
        except cobra.mit.session.LoginError as e:
            msg = f"[LoginError]: {str(e)}"
            self._result.log = {"login": msg}
            print(f"\x1b[31;1m{msg}\x1b[0m")
            return False
        except cobra.mit.request.QueryError as e:
            msg = f"[QueryError]: {str(e)}"
            self._result.log = {"login": msg}
            print(f"\x1b[31;1m{msg}\x1b[0m")
            return False
        except requests.exceptions.ConnectionError as e:
            msg = f"[ConnectionError]: {str(e)}"
            self._result.log = {"login": msg}
            print(f"\x1b[31;1m{msg}\x1b[0m")
            return False
        except Exception as e:
            msg = f"[LoginException]: {str(e)}"
            self._result.log = {"login": msg}
            print(f"\x1b[31;1m{msg}\x1b[0m")
            return False

    def logout(self) -> None:
        try:
            if self.__modir.exists:
                self.__modir.logout()
        except Exception as e:
            msg = f"[LogoutError]: {str(e)}"
            self._result.log = {"logout": msg}
            print(f"\x1b[31;1m{msg}\x1b[0m")

    def session_recreate(self, cookie, version) -> None:
        """
        Recreate Session
        """
        try:
            session = cobra.mit.session.LoginSession(
                self._url, None, None, secure=self._secure, timeout=self._timeout
            )
            session.cookie = cookie
            session._version = version
            self.__modir = cobra.mit.access.MoDirectory(session)
        except Exception as e:
            msg = f"[SessionError]: {str(e)}"
            self._result.log = {"session": msg}
            print(f"\x1b[31;1m{msg}\x1b[0m")

    def render(self, template: Path) -> None:
        """
        Render configuration
        """
        try:
            _jinja = JinjaClass()
            _cobra = CobraClass()
            _jinja.render(template)
            _cobra.render(_jinja.result)
            if _cobra.result.output:
                if self.render_to_xml:
                    self._result.output = {template.name: _cobra.result.output.xmldata}
                else:
                    self._result.output = {
                        template.name: json.loads(_cobra.result.output.data)
                    }
                self._result.success = True
                msg = f"[RenderClass]: {template.name} was validated."
                self._result.log = {template.name: msg}
                print(f"\x1b[32;1m{msg}\x1b[0m")
            else:
                # self._result.log = "[RenderError]: No valid Cobra template."
                self._result.success = False
                self._result.log = {template.name: _cobra.result.log}
                print(f"\x1b[31;1m{_cobra.result.log}\x1b[0m")
        except cobra.mit.request.CommitError as e:
            self._result.success = False
            msg = f"[RenderError]: Error validating {template.name}!. {str(e)}"
            self._result.log = {template.name: msg}
            print(f"\x1b[31;1m{msg}\x1b[0m")
        except Exception as e:
            self._result.success = False
            msg = f"[RenderException]: Error validating {template.name}!. {str(e)}"
            self._result.log = {template.name: msg}
            print(f"\x1b[31;1m{msg}\x1b[0m")

    def commit(self, template: Path) -> None:
        """
        Commit configuration
        """
        try:
            _jinja = JinjaClass()
            _cobra = CobraClass()
            _jinja.render(template)
            _cobra.render(_jinja.result)
            if _cobra.result.output:
                if self.render_to_xml:
                    self._result.output = {template.name: _cobra.result.output.xmldata}
                else:
                    self._result.output = {
                        template.name: json.loads(_cobra.result.output.data)
                    }
                self.__modir.commit(_cobra.result.output)
                self._result.success = True
                msg = f"[DeployClass]: {template.name} was succesfully deployed."
                self._result.log = {template.name: msg}
                print(f"\x1b[32;1m{msg}\x1b[0m")
            else:
                # self._result.log = "[DeployError]: No valid Cobra template."
                self._result.success = False
                self._result.log = {template.name: _cobra.result.log}
                print(f"\x1b[31;1m{_cobra.result.log}\x1b[0m")
        except cobra.mit.request.CommitError as e:
            self._result.success = False
            msg = f"[DeployError]: Error deploying {template.name}!. {str(e)}"
            self._result.log = {template.name: msg}
            print(f"\x1b[31;1m{msg}\x1b[0m")
        except Exception as e:
            self._result.success = False
            msg = f"[DeployException]: Error deploying {template.name}!. {str(e)}"
            self._result.log = {template.name: msg}
            print(f"\x1b[31;1m{msg}\x1b[0m")

    def check(self) -> None:
        """
        Render configuration
        """
        if self._template:
            for temp in self._template:
                self.render(temp)
        else:
            self._result.success = False
            msg = "[RenderException]: No templates configured!."
            self._result.log = {"check": msg}
            print(f"\x1b[31;1m{msg}\x1b[0m")
        if self.logging:
            self.record()

    def deploy(self) -> None:
        """
        Deploy configuration
        """
        if not self._template:
            self._result.success = False
            msg = "[RenderException]: No templates configured!."
            self._result.log = {"render": msg} if self.testing else {"deploy": msg}
            print(f"\x1b[31;1m{msg}\x1b[0m")
            return

        if self.testing:
            for temp in self._template:
                self.render(temp)
        else:
            if self.login():
                for temp in self._template:
                    self.commit(temp)
                self.logout()

        if self.logging:
            self.record()

    def record(self) -> None:
        """
        Save Logging into file
        """
        df = pd.DataFrame(self._result.json)
        df.to_json(
            self.log,
            orient="records",
            indent=4,
            force_ascii=False,
        )

    def show_output(self) -> None:
        """
        Show indent Output
        """
        if self._result.output:
            if self.render_to_xml:
                for key, value in self._result.output.items():
                    print(f"\n------> {key} output. <-------\n")
                    dom = xml.dom.minidom.parseString(value)
                    print(dom.toprettyxml(indent="  "))
            else:
                for key, value in self._result.output.items():
                    print(f"\n------> {key} output. <-------\n")
                    print(json.dumps(value, indent=4, ensure_ascii=False))

    @property
    def result(self):
        return self._result

    @property
    def output(self):
        return self._result.output[0]

    @property
    def template(self) -> list[Path]:
        """
        Define your template:
        \n - Option1: Use Path for define the template, Ex. \n aci.template = Path1
        \n - Option2: List of Path for multiple templates deployments, Ex. \n aci.template = [Path1, Path2, ...]
        \n - Option3: Each time you define a path a list is generated and each new path is added to this list, Ex. \n aci.template = Path1 \n aci.template = Path2 \n Result: aci.template = [Path1, Path2]
        """
        return self._template

    @template.setter
    def template(self, value) -> None:
        if isinstance(value, Path):
            self._template.append(value)
        elif isinstance(value, list) and all(isinstance(item, Path) for item in value):
            self._template = value
        else:
            self._result.success = False
            self._result.log = "[DeployException]: No valid templates!."
            self._template = []
