from __future__ import annotations
from configparser import ConfigParser
import os
from mdplus.core.modules import MdpModule

import logging

logger = logging.getLogger(__name__)


class PakkGettingStarted(MdpModule):
    def __init__(self, command: str, arguments: dict[str, any]):
        super().__init__(command, arguments)

        self.arg_header = self.get_arg(
            "header",
            "# Getting Started using [pakk](https://github.com/iCampus-Wildau/pakk)",
        )
        self.arg_installation = self.get_arg("installation", True)
        self.arg_usage = self.get_arg("usage", True)

        # Parse pakk.cfg using configparser
        if not self.is_applicable():
            logger.warning("pakk.cfg not found in the root directory")

        parser = ConfigParser()
        parser.read(os.path.join(self.root, "pakk.cfg"))

        self.package_name = parser.get("info", "id")
        self.package_short_name = self.package_name.split("/")[-1]

    def is_applicable(self) -> bool:
        # Search for pakk.cfg in the root directory
        if os.path.isfile(os.path.join(self.root, "pakk.cfg")):
            return True

        return False

    def get_content(self):
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
            lines.append(
                f"After the installation completes, start the {self.package_short_name} package:"
            )
            lines.append("```bash")
            lines.append(
                f"pakk start {self.package_short_name}  # Start the package until being stopped or system reboot, or ..."
            )
            lines.append(
                f"pakk enable {self.package_short_name}  # ... start it now and on every system boot.  "
            )
            lines.append("```\n")

        return "\n".join(lines)


module = PakkGettingStarted
