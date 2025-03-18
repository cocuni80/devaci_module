"""Jinja module for the ACI Python SDK (cobra)."""

from typing import Optional
from datetime import datetime
from yaml.constructor import SafeConstructor
from yaml.reader import Reader
from yaml.scanner import Scanner, ScannerError
from yaml.parser import Parser
from yaml.composer import Composer
from yaml.resolver import Resolver
from yaml import load

import jinja2
import yaml
from pathlib import Path

# ------------------------------------------   Safe Loader


class MySafeConstructor(SafeConstructor):
    def add_bool(self, node):
        return self.construct_scalar(node)


MySafeConstructor.add_constructor("tag:yaml.org,2002:bool", MySafeConstructor.add_bool)


class MySafeLoader(Reader, Scanner, Parser, Composer, SafeConstructor, Resolver):
    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        SafeConstructor.__init__(self)
        Resolver.__init__(self)


class JinjaError(Exception):
    """
    Jinja2 class manage the exceptions for rendering
    """

    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return self.reason


# ------------------------------------------   Cobra Result Class


class JinjaResult:
    """
    The JinjaResult class return the results for Jinja Render
    """

    def __init__(self):
        self.date = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
        self._output = None
        self._success = False
        self._log = str()

    @property
    def output(self) -> Optional[dict]:
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
        return "JinjaResult"


# ------------------------------------------   Cobra Result Class


class JinjaClass:
    """
    Jinja2 class for templates rendering
    """

    def __init__(self):
        # --------------   Init Information
        self._template = None

        # --------------   Jinja2 Setup
        self._setup = {
            "loader": jinja2.BaseLoader(),
            "extensions": ["jinja2.ext.do"],
        }

        # --------------   Output Information
        self._result = JinjaResult()

    def render(self, path: Path) -> None:
        try:
            with open(path, "r", encoding="utf-8") as file:
                self._template = file.read()
            env = jinja2.Environment(**self._setup)
            render_str = env.from_string(self._template).render()
            self._result.output = load(render_str, MySafeLoader)
            self._result.success = True
            self._result.log = "[JinjaClass]: Jinja template was sucessfully rendered."
        except ScannerError as e:
            self._result.log = f"[ScannerError]: Syntax error {path.name}!. {str(e)}"
            # print(f"\x1b[33;1m[ScannerError]: {str(e)}\x1b[0m")
        except jinja2.exceptions.TemplateSyntaxError as e:
            self._result.log = (
                f"[TemplateSyntaxError]: Syntax error {path.name}!. {str(e)}"
            )
            # print(f"\x1b[33;1m[TemplateSyntaxError]: {str(e)}\x1b[0m")
        except jinja2.exceptions.UndefinedError as e:
            self._result.log = (
                f"[UndefinedError]: Undefined error with {path.name}!. {str(e)}"
            )
            # print(f"\x1b[31;1m[UndefinedError]: {str(e)}\x1b[0m")
        except yaml.MarkedYAMLError as e:
            self._result.log = (
                f"[MarkedYAMLError]: Syntax error  {path.name}!. {str(e)}"
            )
            # print(f"\x1b[31;1m[MarkedYAMLError]: {str(e)}\x1b[0m")
        except Exception as e:
            self._result.log = (
                f"[JinjaException]: Exepction with {path.name}!. {str(e)}"
            )
            # print(f"\x1b[31;1m[JinjaException]: {str(e)}\x1b[0m")

    @property
    def result(self) -> JinjaResult:
        return self._result
