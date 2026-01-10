# Copyright 2020 Jorge C. Riveros
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ACI module configuration for the ACI Python SDK (cobra)."""

import urllib3
import json
import sys
import time
import pandas as pd
import xml.dom.minidom
import cobra.mit.session
import cobra.mit.access
import cobra.mit.request
from datetime import datetime
from pathlib import Path
import rich
from rich.syntax import Syntax
from .jinja import JinjaClass
from .cobra import CobraClass
import threading
import warnings


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ------------------------------------------   Deployer Result Class


RED = "\033[31;1m"
GREEN = "\033[32;1m"
WHITE = "\033[37;1m"
YELLOW = "\033[33;1m"
MAGENTA = "\033[35;1m"
CYAN = "\033[36;1m"
RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"


class DeployResult:
    """
    The DeployResult class return the results for Deployer logs
    """

    def __init__(self):
        self.date = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
        self._success = False
        self._log = []
        self._path = Path("/")
        self._name = "template"

    @property
    def success(self) -> bool:
        return self._success

    @property
    def log(self) -> list:
        return self._log

    @property
    def path(self) -> Path:
        return self._path

    @property
    def name(self) -> str:
        return self._name

    @property
    def json(self) -> dict:
        return {
            "date": self.date,
            "success": self._success,
            "log": self._log,
            "path": str(self.path),
            "name": self._name,
        }

    @success.setter
    def success(self, value) -> None:
        self._success = value

    @log.setter
    def log(self, value) -> None:
        if isinstance(value, str):
            self._log.append(value)
        elif isinstance(value, list):
            self._log.extend(value)
        else:
            return

    @path.setter
    def path(self, value) -> None:
        self._path = value

    @name.setter
    def name(self, value) -> None:
        self._name = value

    def __str__(self):
        return "DeployResult"


# ------------------------------------------   Deployer Class


class DeployClass:
    """
    Deployment manager for Cisco ACI using the Cobra SDK.

    This class handles the full deployment workflow, including:
    - Template rendering (Jinja2)
    - Cobra model rendering
    - Optional filtering of input variables
    - Output visualization and persistence
    - Optional commit to APIC

    Configuration options:
    - ip (str): APIC IPv4 address
    - username (str): APIC username
    - password (str): APIC password
    - testing (bool): Enable dry-run mode (default: False)
    - filter_by (str): Variable name used for filtering (default: "tag")
    - timer (int): Countdown timer in seconds before commit (default: 5)
    - show_output (bool): Pretty-print rendered output to the terminal
    - file_output (str): Output filename (JSON or XML)
    - secure (bool): Verify SSL certificates (default: False)
    - render_to_xml (bool): Render output as XML instead of JSON (default: True)
    - working_folder (Path): Base directory for templates and data files
    - logging (bool): Enable execution logging to file
    """

    def __init__(self, **kwargs):

        # --------------   Setting Information
        self._ip = kwargs.get("ip", "127.0.0.1")
        self._url = "https://{}".format(self._ip)
        self._username = kwargs.get("username", "admin")
        self.__password = kwargs.get("password", "Cisco123!")
        self._timeout = kwargs.get("timeout", 180)
        self._secure = kwargs.get("secure", False)
        self._testing = kwargs.get("testing", False)
        self._timer = kwargs.get("timer", 5)
        self._show_output = kwargs.get("show_output", False)
        self._file_output = kwargs.get("file_output", None)
        self._logging = kwargs.get("logging", True)
        self._render_to_xml = kwargs.get("render_to_xml", True)
        self._filters_source_sheet = kwargs.get("filters_source_sheet", None)
        self._filters_condition_field = kwargs.get("filters_condition_field", "enabled")
        self._filters_output_field = kwargs.get("filters_output_field", "name")
        self._filters = kwargs.get("filters", None)
        self._filter_by = kwargs.get("filter_by", "tag")
        self._filter_on_excel = kwargs.get("filter_by", "tag")
        self._working_folder: Path = kwargs.get("working_folder", Path.cwd())

        # --------------   Cobra variables

        self._cobra = CobraClass()
        self._session = cobra.mit.session.LoginSession(self._url, self._username, self.__password, self._secure, self._timeout)
        self.__modir = cobra.mit.access.MoDirectory(self._session)

        # --------------   Input Information
        self._template: list = kwargs.get("template", [])

        # --------------   Output Variables
        self._variables: dict = {}
        self._results: list = []

    # -------------------------------------------------   Control

    def deploy(self) -> None:
        """
        Execute the deployment workflow for all configured templates.
        \nWorkflow:
        - Render Jinja templates using loaded variables
        - Render Cobra configuration
        - Collect per-template results
        - Optionally log results, print output, save output, and deploy to APIC
        """

        if not self._template:
            print(f"{YELLOW}[Deploy] -> [ConfigError]: {RED}No templates configured!.{RESET}")
            return

        for template, path in self._template:
            _deploy = DeployResult()
            _deploy.path = path
            _deploy.name = path.name if isinstance(path, Path) else path
            try:
                _jinja = JinjaClass()
                _jinja.template = template
                _jinja.name = _deploy.name
                _jinja.render(**self._variables)
                _deploy.log = _jinja.result.log
                if not _jinja.result.success:
                    _deploy.success = False
                    raise RuntimeError(_jinja.result.log)

                self._cobra.render(_jinja.result)
                _deploy.log = self._cobra.result.log
                if not self._cobra.result.success:
                    _deploy.success = False
                    raise RuntimeError(self._cobra.result.log)

                _deploy.success = True
                print(f"{YELLOW}[Deploy]: {GREEN}Template {path.name} was deployed successfully.{RESET}")
            except Exception as e:
                _deploy.success = False
                print(f"{YELLOW}[Deploy] -> [RenderError]: {RED}Template {path.name} was not deployed.{RESET}")
            self._results.append(_deploy.json)

        if self._show_output:
            self.print_output()

        if self._file_output:
            self.save_output(self._file_output)

        if not self._testing and self._cobra.result.success:
            try:
                timer_thread = self.start_timer(f"{HIDE_CURSOR}{YELLOW}[Deploy]: {CYAN}Deploying templates to APIC [{self._ip}] in")
                timer_thread.join()
                self.__modir.login()
                self.__modir.commit(self._cobra.config)
                print(f"{YELLOW}[Deploy]: {GREEN}Template was succesfully deployed.{RESET}")
            except Exception as e:
                print(f"{YELLOW}[Deploy] -> [{type(e).__name__}]: {RED}{str(e)}{RESET}")
            finally:
                print(f"{SHOW_CURSOR}")
                self.__modir.logout()

        if self._logging:
            with open(self._working_folder / "logging.json", "w", encoding="utf-8") as f:
                json.dump(self._results, f, indent=4, ensure_ascii=False)

    def save_output(self, name: str = "output") -> None:
        """
        Save rendered configuration output to disk in a human-readable format.
        - Writes XML if self._render_to_xml is True
        - Writes JSON otherwise
        - Output file is saved inside the working folder
        """
        if not self.config:
            return

        suffix = "xml" if self._render_to_xml else "json"
        output_path = self._working_folder / f"{name}.{suffix}"
        try:
            if self._render_to_xml:
                dom = xml.dom.minidom.parseString(self.config)
                content = dom.toprettyxml(indent="\t")
            else:
                content = json.dumps(self.config, indent=4, ensure_ascii=False)
            output_path.write_text(content, encoding="utf-8")
        except Exception as e:
            print(f"\x1b[31;1m[SaveOutputError]: Failed to save output file! {e}\x1b[0m")

    def print_output(self, theme: str = "fruity", line_numbers: bool = True) -> None:
        """
        Pretty-print the rendered configuration to the terminal.
        \nSupported themes: monokai, dracula, solarized-dark, solarized-light, github, gruvbox-dark, gruvbox-light, nord, fruity
        - Supports XML and JSON output
        - Uses Rich syntax highlighting
        - Optional line numbers
        """
        if not self.config:
            return
        try:
            print("\n\x1b[1m\x1b[47;1m-------------------> output.\x1b[0m")
            if self._render_to_xml:
                content = xml.dom.minidom.parseString(self.config).toprettyxml(indent="\t")
                lexer = "xml"
            else:
                content = json.dumps(self.config, indent=4, ensure_ascii=False)
                lexer = "json"
            rich.print(Syntax(content, lexer, theme=theme, line_numbers=line_numbers))
        except Exception as e:
            print(f"\x1b[31;1m[PrintOutputError]: Error printing output! {e}\x1b[0m")

    def start_timer(self, msg=""):
        t = threading.Thread(target=self.timer, args=(msg,), daemon=True)
        t.start()
        return t

    def timer(self, msg: str = "") -> None:
        """
        Display a countdown timer with a progress bar in the terminal.
        - Uses ANSI colors for visual feedback
        - Updates the same console line in-place
        - Duration is defined by self._timer (seconds)
        """
        total = self._timer
        block = "██"
        space = "  "

        for remaining in range(total, -1, -1):
            filled = total - remaining
            bar = block * filled + space * remaining
            sys.stdout.write(f"\r{msg} {remaining} seconds " f"[{WHITE}{bar}{CYAN}]")
            sys.stdout.flush()
            time.sleep(1)
        print(f"{RESET}")

    @property
    def results(self):
        """Return the execution results (read-only)."""
        return self._results

    @property
    def variables(self):
        """Return the execution results (read-only)."""
        return self._variables

    @property
    def template(self):
        """
        Load template content into memory.
        \nAccepted inputs:
        - str: template filename (loaded from working_folder)
        - list[str]: multiple template filenames
        - tuple[str, str]: (template_content, template_name)
        - list[tuple[str, str]]: multiple in-memory templates
        \nStored internally as:
        - list of (template_content, template_path)
        """
        return self._template

    @property
    def config(self):
        """Return the execution results (read-only)."""
        return self._cobra.result.xml if self._render_to_xml else self._cobra.result.json

    @property
    def csv(self):
        """Return the execution results (read-only)."""
        return self._variables

    @property
    def xlsx(self):
        """Return the execution results (read-only)."""
        return self._variables

    @variables.setter
    def variables(self, value) -> None:
        self._variables = value

    @template.setter
    def template(self, value) -> None:
        """
        Load template content into memory.
        \nAccepted inputs:
        - str: template filename (loaded from working_folder)
        - list[str]: multiple template filenames
        - tuple[str, str]: (template_content, template_name)
        - list[tuple[str, str]]: multiple in-memory templates
        \nStored internally as:
        - list of (template_content, template_path)
        """
        if not value:
            return
        values = value if isinstance(value, list) else [value]
        for item in values:
            try:
                # Case 1: in-memory template (content, name)
                if isinstance(item, tuple) and len(item) == 2:
                    content, name = item
                    if not isinstance(content, str) or not isinstance(name, str):
                        raise ValueError("Template content and name must be strings")
                    path = Path(name)
                    self._template.append((content, path))
                # Case 2: template loaded from file
                elif isinstance(item, str):
                    path = self._working_folder / item
                    with open(path, "r", encoding="utf-8") as file:
                        self._template.append((file.read(), path))
                else:
                    raise ValueError("Invalid template format")
            except Exception as e:
                print(f"\x1b[31;1m[TemplateException]: Error loading template.\x1b[0m")

    @csv.setter
    def csv(self, value) -> None:
        """
        Insert CSV files path to list of Variables
        """
        files = [value] if isinstance(value, str) else value
        for file in files:
            try:
                filters = self._filters
                path = self._working_folder / file
                name = path.stem
                df = pd.read_csv(path)
                self._variables |= {name: self.apply_filter(df, filters)}
            except Exception as e:
                print(f"\x1b[31;1m[CSVException]: Error loading CSV file! {e}\x1b[0m")

    @xlsx.setter
    def xlsx(self, value) -> None:
        """
        Load XLSX file(s), optionally extract filters, and store processed sheets as variables.
        """
        files = [value] if isinstance(value, str) else value
        for file in files:
            try:
                filters = None
                path = self._working_folder / file

                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", message="Data Validation extension is not supported*", category=UserWarning)
                    sheets = pd.read_excel(path, sheet_name=None)

                if self._filters_source_sheet:
                    df_filters = sheets.get(self._filters_source_sheet)
                    if df_filters is None:
                        raise ValueError(f"Sheet '{self._filters_source_sheet}' does not exist!")
                    filters = df_filters.loc[df_filters[self._filters_condition_field], self._filters_output_field].tolist()
                elif self._filters:
                    filters = self._filters

                self._variables |= {name: self.apply_filter(df, filters) for name, df in sheets.items()}
            except Exception as e:
                print(f"\x1b[31;1m[XLSXException]: Error loading XLSX file '{file}': {e}\x1b[0m")

    def apply_filter(self, df, filters=None):
        """
        Ultra defensive tag filter bound to class config.
        """
        column = self._filter_by
        if not filters or not column or column not in df.columns:
            return df.to_dict("records") if not filters else []

        s = df[column]
        return df[s.notna() & s.astype(str).str.strip().ne("") & s.isin(filters)].to_dict(orient="records")
