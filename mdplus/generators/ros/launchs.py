from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from markdownTable import markdownTable

import mdplus.util.file_utils as file_utils
from mdplus.core.environments.ros2 import Ros2Environment
from mdplus.core.generator import MdpGenerator
from mdplus.util.markdown import adapt_string_for_table, get_link
from mdplus.util.parser.ros2_parser import Package, PackageType
from overrides import overrides

if TYPE_CHECKING:
    from mdplus.core.documents.block import MdpBlock
    from mdplus.core.documents.document import Document

logger = logging.getLogger(__name__)


class RosLaunchMdpModule(MdpGenerator):
    def __init__(self, document: Document, mdpBlock: MdpBlock):
        super().__init__(document, mdpBlock)

        self.arg_header = self.get_arg("header", "# ROS Launch Scripts")

    @overrides
    def get_content(self) -> str:
        """Creates a table of launch scripts found in the ROS-packages"""

        dir_path = self.workspace.root_path
        logger.debug(f"Parsing ROS launch information for {dir_path}")

        env = self.workspace.get_environment("ros2", env_class=Ros2Environment)
        packages: list[Package] = env.packages

        content = list()
        content.append(self.arg_header)

        scripts = list()

        for package in packages:
            if package.package_type == PackageType.PYTHON:
                
                if len(package.launch_scripts) > 0:
                    for script in package.launch_scripts:
                        scripts.append(
                            {
                                "Name": script.name,
                                "Info": adapt_string_for_table(script.info),
                                "Script": get_link(
                                    script.name,
                                    file_utils.get_relative_path(script.launch_file_path, self.document.dir_path),
                                ),
                            }
                        )

        scripts.sort(key=lambda x: x["Name"])

        if len(scripts) > 0:
            content.append(markdownTable(scripts).setParams(row_sep="markdown", quote=False).getMarkdown())
        else:
            content.append("This package has no launch scripts")

        return "\n\n".join(content)
