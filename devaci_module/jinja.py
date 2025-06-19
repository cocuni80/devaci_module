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


def split_filter(value, delimiter=","):
    return str(value).split(delimiter)


def range_filter(value):
    result = []
    parts = str(value).split(",")
    for part in parts:
        if "-" in part:
            start, end = part.split("-")
            result.extend(range(int(start), int(end) + 1))
        else:
            result.append(int(part))
    return result

def nan_filter(value):
    
    if str(value) == "nan":
        return False
    return True


def str_to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("true", "yes", "1")


def no_convert_int_constructor(loader, node):
    return node.value


def no_convert_float_constructor(loader, node):
    return node.value


def remove_str_nan_keys(d):
    if isinstance(d, dict):
        return {k: remove_str_nan_keys(v) for k, v in d.items() if v != "nan"}
    elif isinstance(d, list):
        return [remove_str_nan_keys(item) for item in d]
    else:
        return d


def replace_str_nan_with_empty(obj):
    """
    Reemplaza todos los valores 'nan' (como string) por una cadena vacía ("")
    en un diccionario o lista multinivel.
    """
    if isinstance(obj, dict):
        return {k: replace_str_nan_with_empty(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_str_nan_with_empty(item) for item in obj]
    elif isinstance(obj, str) and obj.strip().lower() == "nan":
        return ""
    else:
        return obj


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


MySafeLoader.add_constructor("tag:yaml.org,2002:int", no_convert_int_constructor)
MySafeLoader.add_constructor("tag:yaml.org,2002:float", no_convert_float_constructor)

for first_char, resolvers in list(MySafeLoader.yaml_implicit_resolvers.items()):
    filtered = [r for r in resolvers if r[0] != "tag:yaml.org,2002:bool"]
    if filtered:
        MySafeLoader.yaml_implicit_resolvers[first_char] = filtered
    else:
        del MySafeLoader.yaml_implicit_resolvers[first_char]


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

    def render(self, path: Path, **kwargs) -> None:
        try:
            with open(path, "r", encoding="utf-8") as file:
                self._template = file.read()
            env = jinja2.Environment(**self._setup)            
            # Registrar filtros
            env.filters["bool"] = str_to_bool
            env.filters["range"] = range_filter
            env.filters["nan"] = nan_filter
            render_str = env.from_string(self._template).render(kwargs)
            # self._result.output = load(render_str, MySafeLoader)
            # self._result.output = remove_str_nan_keys(load(render_str, MySafeLoader))
            self._result.output = replace_str_nan_with_empty(
                load(render_str, MySafeLoader)
            )
            self._result.success = True
            # print(self._result.output)
            self._result.log = "[JinjaClass]: Jinja template was sucessfully rendered."
        except ScannerError as e:
            self._result.log = f"[ScannerError]: {path.name} error, {str(e)}"
            # print(f"\x1b[33;1m[ScannerError]: {str(e)}\x1b[0m")
        except jinja2.exceptions.TemplateSyntaxError as e:
            self._result.log = f"[TemplateSyntaxError]: {path.name} error, {str(e)}"
            # print(f"\x1b[33;1m[TemplateSyntaxError]: {str(e)}\x1b[0m")
        except jinja2.exceptions.UndefinedError as e:
            self._result.log = f"[UndefinedError]: {path.name} error, {str(e)}"
            # print(f"\x1b[31;1m[UndefinedError]: {str(e)}\x1b[0m")
        except yaml.MarkedYAMLError as e:
            self._result.log = f"[MarkedYAMLError]: {path.name} error, {str(e)}"
            # print(f"\x1b[31;1m[MarkedYAMLError]: {str(e)}\x1b[0m")
        except Exception as e:
            self._result.log = f"[JinjaException]: {path.name} error, {str(e)}"
            # print(f"\x1b[31;1m[JinjaException]: {str(e)}\x1b[0m")

    @property
    def result(self) -> JinjaResult:
        return self._result
