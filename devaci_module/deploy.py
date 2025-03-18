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
    The DeployerResult class return the results for Deployer logs
    """

    def __init__(self):
        self.date = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
        self._output = list()
        self._success = False
        self._log = list()

    @property
    def output(self) -> dict:
        return self._output

    @property
    def success(self) -> bool:
        return self._success

    @property
    def log(self) -> list:
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
        self._log.append(value)

    @output.setter
    def output(self, value) -> None:
        self._output.append(value)

    def __str__(self):
        return "DeployerResult"


# ------------------------------------------   Deployer Class


class DeployClass:
    """
    Cobra Deployer Class from Cobra SDK
    \n username: APIC username
    \n password: APIC username
    \n ip: APIC IPv4
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
        self.logging = kwargs.get("logging", False)

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
            print(f"\x1b[31;1m[LoginError]: {str(e)}\x1b[0m")
            self._result.log = f"[LoginError]: {str(e)}"
            return False
        except cobra.mit.request.QueryError as e:
            print(f"\x1b[31;1m[QueryError]: {str(e)}\x1b[0m")
            self._result.log = f"[QueryError]: {str(e)}"
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"\x1b[31;1m[ConnectionError]: {str(e)}\x1b[0m")
            self._result.log = f"[ConnectionError]: {str(e)}"
            return False
        except Exception as e:
            print(f"\x1b[31;1m[LoginError]: {str(e)}\x1b[0m")
            self._result.log = f"[LoginError]: {str(e)}"
            return False

    def logout(self) -> None:
        try:
            if self.__modir.exists:
                self.__modir.logout()
        except Exception as e:
            print(f"\x1b[31;1m[LogoutError]: {str(e)}\x1b[0m")
            self._result.log = f"[LogoutError]: {str(e)}"

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
            print(f"\x1b[31;1m[SessionError]: {str(e)}\x1b[0m")
            self._result.log = f"[SessionError]: {str(e)}"

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
                self._result.output = {
                    template.name: json.loads(_cobra.result.output.data)
                }
                self.__modir.commit(_cobra.result.output)
                self._result.success = True
                msg = f"[DeployClass]: {template.name} was succesfully deployed."
                print(f"\x1b[32;1m{msg}\x1b[0m")
                self._result.log = msg
            else:
                # self._result.log = "[DeployError]: No valid Cobra template."
                print(f"\x1b[31;1m{_cobra.result.log}\x1b[0m")
                self._result.log = _cobra.result.log
        except cobra.mit.request.CommitError as e:
            print(
                f"\x1b[31;1m[DeployError]: Error deploying {template.name}!. {str(e)}\x1b[0m"
            )
            self._result.success = False
            self._result.log = (
                f"[DeployError]: Error deploying {template.name}!. {str(e)}"
            )
        except Exception as e:
            print(
                f"\x1b[31;1m[DeployException]: Error deploying {template.name}!. {str(e)}\x1b[0m"
            )
            self._result.success = False
            self._result.log = f"\x1b[31;1m[DeployException]: Error deploying {template.name}!. {str(e)}\x1b[0m"

    def deploy(self) -> None:
        """
        Deploy configuration
        """
        if self.login():
            if self._template:
                for temp in self._template:
                    self.commit(temp)
            else:
                msg = "[DeployException]: No templates configured!."
                print(f"\x1b[31;1m{msg}\x1b[0m")
                self._result.success = False
                self._result.log = msg
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
