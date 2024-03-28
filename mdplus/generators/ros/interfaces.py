from __future__ import annotations
import logging
from typing import Dict, List

from markdownTable import markdownTable

from mdplus.core.environments.ros2 import Ros2Environment
from mdplus.util.parser.ros2_parser import Package, PackageType
from mdplus.util.markdown import get_anchor_from_header

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from mdplus.core.documents.document import Document
    from mdplus.core.documents.block import MdpBlock

logger = logging.getLogger(__name__)

from mdplus.core.generator import MdpGenerator


class RosInterfacesMdpModule(MdpGenerator):
    def __init__(self, document: Document, mdpBlock: MdpBlock):
        super().__init__(document, mdpBlock)

        self.arg_header = self.get_arg("header", "# ROS Interface Definitions")

    def get_content(self) -> str:
        """Creates a table of messages and services found in the ROS-packages"""


        dir_path = self.workspace.root_dir
        logger.info(f"Create ROS message and service information for {dir_path}")

        env = self.workspace.get_environment("ros2", env_class=Ros2Environment)
        packages: list[Package] = env.packages

        content = list()

        content.append(self.arg_header)

        for package in packages:
            if package.package_type == PackageType.CMAKE:
                if len(package.messages) > 0 or len(package.services) > 0:
                    content.append(self.get_table(package, msgs=True, srv=True))

        for package in packages:
            if package.package_type == PackageType.CMAKE:
                if len(package.messages) > 0:
                    content.append(f"## Message definitions of {package.name}")
                    for message in package.messages:
                        content.append(message.get_wiki_entry(3, self.document.dir_path))
                if len(package.services) > 0:
                    content.append(f"## Service definitions of {package.name}")
                    for service in package.services:
                        content.append(service.get_wiki_entry(3, self.document.dir_path))

        if len(content) == 1:
            content.append(
                f"This package has no custom message or service type definitions."
            )

        return "\n\n".join(content)

    def get_table(self, package: Package, msgs=True, srv=True):
        """Creates a table of messages and services found in the ROS-packages"""

        msg_data: List[Dict[str, str]] = list()
        srv_data: List[Dict[str, str]] = list()

        if msgs:
            for msg in package.messages:
                msg_data.append(
                    {
                        "Name": f"[`{msg.name}`](#{get_anchor_from_header(msg.name)})",
                        "Type": "Message",
                        "Package": package.name,
                    }
                )

        if srv:
            for srv in package.services:
                srv_data.append(
                    {
                        "Name": f"[`{srv.name}`](#{get_anchor_from_header(srv.name)})",
                        "Type": "Service",
                        "Package": package.name,
                    }
                )

        msg_data.sort(key=lambda x: x["Name"])
        srv_data.sort(key=lambda x: x["Name"])

        return (
            markdownTable(msg_data + srv_data)
            .setParams(row_sep="markdown", quote=False)
            .getMarkdown()
        )

