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
        self._output = None
        self._success = False
        self._log = str()

    @property
    def output(self) -> dict:
        return self._output

    @property
    def success(self) -> bool:
        return self._success

    @property
    def log(self) -> str:
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
        self._log = value

    @output.setter
    def output(self, value) -> None:
        self._output = value

    def __str__(self):
        return "DeployerResult"


# ------------------------------------------   Deployer Class


class DeployClass:
    """
    Cobra Deployer Class from Cobra SDK
    """

    def __init__(self, **kwargs):
        # --------------   Render Information
        self._template = kwargs.get("template", None)
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

        self._jinja = JinjaClass()
        self._cobra = CobraClass()
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

    def render(self) -> None:
        """
        Render Template
        """
        if self._template:
            self._jinja.render(self._template)
            self._cobra.render(self._jinja.result)
            if self.logging:
                self.record()
        else:
            print("\x1b[31;1m[RenderError]: No Valid Template.\x1b[0m")

    def deploy(self) -> None:
        """
        Deploy configuration
        """
        if self._template:
            self._jinja.render(self._template)
            self._cobra.render(self._jinja.result)
        try:
            if self._cobra.result.output:
                if self.login():
                    self._result.output = json.loads(self._cobra.result.output.data)
                    self.__modir.commit(self._cobra.result.output)
                    self._result.success = True
                    self.logout()
                    self._result.log = (
                        f"[DeployClass]: {self._template} was succesfully deployed."
                    )
                    print(f"\x1b[32;1m{self._result.log}\x1b[0m")
            else:
                # self._result.log = "[DeployError]: No valid Cobra template."
                self._result.log = self._cobra.result.log
                print(f"\x1b[31;1m{self._result.log}\x1b[0m")
        except cobra.mit.request.CommitError as e:
            print(f"\x1b[31;1m[DeployError]: {str(e)}\x1b[0m")
            self._result.success = False
            self._result.log = f"[DeployError]: {str(e)}"
        except Exception as e:
            print(f"\x1b[31;1m[DeployException]: {str(e)}\x1b[0m")
            self._result.success = False
            self._result.log = f"[DeployException]: {str(e)}"
        finally:
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
    def template(self) -> Union[str, list[str]]:
        return self._template

    @template.setter
    def template(self, value) -> None:
        self._template = value
