from __future__ import annotations
from configparser import ConfigParser
import os
from mdplus.core.generator import MdpGenerator

from overrides import overrides

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mdplus.core.documents.document import Document
    from mdplus.core.documents.block import MdpBlock

import logging

logger = logging.getLogger(__name__)


class PakkGettingStartedGenerator(MdpGenerator):
    def __init__(self, document: Document, mdpBlock: MdpBlock):
        super().__init__(document, mdpBlock)

        self.arg_header = self.get_arg(
            "header",
            "# Getting Started using [pakk](https://github.com/iCampus-Wildau/pakk)",
        )
        self.arg_installation = self.get_arg("installation", True)
        self.arg_usage = self.get_arg("usage", True)

        # Parse pakk.cfg using configparser
        if not self.is_applicable():
            logger.warning("pakk.cfg not found in the root directory")

        logger.debug(f"Parsing pakk.cfg in {self.workspace.root_path}")
        parser = ConfigParser()
        parser.read(os.path.join(self.workspace.root_path, "pakk.cfg"))

        self.package_name = parser.get("info", "id")
        self.package_short_name = self.package_name.split("/")[-1]

    def is_applicable(self) -> bool:
        # Search for pakk.cfg in the root directory
        if os.path.isfile(os.path.join(self.workspace.root_path, "pakk.cfg")):
            return True

        return False

    @overrides
    def get_content(self) -> str:
        lines = []
        lines.append(self.arg_header)
        lines.append(
            "Using [pakk](https://github.com/iCampus-Wildau/pakk) package manager is recommended for automating the installation and management of ROS 2 packages.\n"
        )

        if self.arg_installation:
            lines.append("Installation with pakk:")
            lines.append("```bash")
            lines.append(f"pakk install {self.package_name}")
            lines.append("```\n")

        if self.arg_usage:
            lines.append(f"After the installation completes, start the {self.package_short_name} package:")
            lines.append("```bash")
            lines.append(
                f"pakk start {self.package_short_name}  # Run as a service until a reboot / manual stop, or ..."
            )
            lines.append(f"pakk enable {self.package_short_name}  # ... start it now and on every system boot.  ")
            lines.append("```\n")

        return "\n".join(lines)
