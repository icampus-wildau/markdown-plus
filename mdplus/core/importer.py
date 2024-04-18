from __future__ import annotations
import importlib
import importlib.util

import inspect
import logging

from types import ModuleType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mdplus.core.generator import MdpGenerator


logger = logging.getLogger(__name__)

# TODO: Allow external generators
GENERATORS_PREFIX = "mdplus.generators"
"""The prefix for all generator modules."""


class ModuleImporter:
    """Dynamic module importer for markdown-plus generators."""

    modules: dict[str, ModuleType] = {}
    """Already imported modules."""

    @staticmethod
    def get_module(command: str) -> MdpGenerator | None:
        """Get a module for a given command."""

        from mdplus.core.generator import MdpGenerator

        if command not in ModuleImporter.modules:
            module_name = f"{GENERATORS_PREFIX}.{command}"
            try:
                spec = importlib.util.find_spec(module_name)
            except ModuleNotFoundError:
                spec = None
            if spec is not None:
                logger.debug("Importing generator %s", module_name)
                ModuleImporter.modules[command] = importlib.import_module(module_name)

            else:
                logger.warning("Generator %s not found", module_name)
                ModuleImporter.modules[command] = None

        cmd_module = ModuleImporter.modules[command]
        if cmd_module is not None:

            # Find the correct class
            classes = [
                cls
                for name, cls in inspect.getmembers(cmd_module, inspect.isclass)
                if inspect.getmodule(cls) == cmd_module and issubclass(cls, MdpGenerator)
            ]

            if len(classes) == 0:
                logger.error("Module %s is a package or does not have class deriving from `MdpGenerator`!", cmd_module)
                return None

            return classes[0]

        return None
