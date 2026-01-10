"""Jinja module for the ACI Python SDK (cobra)."""

from typing import Optional
from datetime import datetime
from yaml.constructor import SafeConstructor
from yaml.reader import Reader
from yaml.scanner import Scanner
from yaml.parser import Parser
from yaml.composer import Composer
from yaml.resolver import Resolver
from yaml import load

import jinja2

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


def replace_str_nan_with_empty(obj):
    """
    Recursively replaces string values equal to 'nan' (case-insensitive)
    with an empty string ("") in nested dictionaries and lists.

    - Traverses arbitrarily deep dict/list structures
    - Preserves non-string values
    - Ignores real NaN values (float('nan')); only string "nan" is replaced

    :param obj: Any Python object (dict, list, str, or other)
    :return: Object with string 'nan' values replaced by ""
    """
    if isinstance(obj, dict):
        return {k: replace_str_nan_with_empty(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [replace_str_nan_with_empty(v) for v in obj]
    if isinstance(obj, str) and obj.strip().lower() == "nan":
        return ""
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
        self._name = None

        # --------------   Jinja2 Setup
        self._setup = {
            "loader": jinja2.BaseLoader(),
            "extensions": ["jinja2.ext.do"],
        }
        self.env = jinja2.Environment(**self._setup)

        # --------------   Jinja2 Filters
        self.env.filters["bool"] = str_to_bool
        self.env.filters["range"] = range_filter
        self.env.filters["nan"] = nan_filter

        # --------------   Output Information
        self._result = JinjaResult()

    def render(self, **kwargs) -> None:
        RED = "\033[31;1m"
        GREEN = "\033[32;1m"
        WHITE = "\033[37;1m"
        YELLOW = "\033[33;1m"
        MAGENTA = "\033[35;1m"
        RESET = "\033[0m"

        try:
            output = self.env.from_string(self._template).render(**kwargs)
            self._result.output = replace_str_nan_with_empty(load(output, MySafeLoader))
            self._result.log = f"[Jinja]: Template {self._name} was rendered sucessfully."
            self._result.success = True
            print(f"{YELLOW}[Jinja]:{GREEN} Template {self._name} was rendered successfully.{RESET}")
        except Exception as e:
            self._result.log = f"[Jinja] -> [{type(e).__name__}]: {e.message}. Line: {e.lineno}"
            print(f"{YELLOW}[Jinja] -> [{type(e).__name__}]:{RED} {str(e)}. Line: {e.lineno}{RESET}")

    @property
    def template(self) -> str:
        return self._template

    @property
    def name(self) -> str:
        return self._name

    @property
    def result(self) -> JinjaResult:
        return self._result

    @template.setter
    def template(self, value) -> None:
        """
        Insert templates into the JinjaClass
        """
        self._template = value

    @name.setter
    def name(self, value) -> None:
        """
        Insert templates into the JinjaClass
        """
        self._name = value
