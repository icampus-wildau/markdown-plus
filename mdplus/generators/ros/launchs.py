import logging
from typing import Dict


from mdplus.core.generator import MdpGenerator

from markdownTable import markdownTable

from mdplus.util.parser.ros2_parser import Package, PackageType
from mdplus.util.markdown import get_link, adapt_string_for_table
import mdplus.util.file_utils as file_utils


logger = logging.getLogger(__name__)


class RosLaunchMdpModule(MdpGenerator):
    def __init__(self, command: str, arguments: Dict[str, any]):
        super().__init__(command, arguments)

        self.arg_header = self.get_arg("header", "# ROS Launch Scripts")
        
    def get_content(self) -> str:
        """Creates a table of launch scripts found in the ROS-packages"""

        dir_path = self.root
        logger.debug(f"Parsing ROS launch information for {dir_path}")

        packages: list[Package] = self.arguments.get("packages", Package.getPackages(dir_path))
        content = list()
        content.append(self.arg_header)

        scripts = list()

        for package in packages:
            if package.package_type == PackageType.PYTHON:
                print(package)
                if len(package.launch_scripts) > 0:
                    for script in package.launch_scripts:
                        scripts.append(
                            {
                                "Name": script.name,
                                "Info": adapt_string_for_table(script.info),
                                "Script": get_link(script.name, file_utils.get_relative_path(script.launch_file_path, self.file_dir)),
                            }
                        )

        scripts.sort(key=lambda x: x["Name"])

        if len(scripts) > 0:
            content.append(markdownTable(scripts).setParams(row_sep="markdown", quote=False).getMarkdown())
        else:
            content.append("This package has no launch scripts")

        return "\n\n".join(content)


module = RosLaunchMdpModule

# def main(*args, **kwargs):
#     """Creates a table of launch scripts found in the ROS-packages"""

#     dir_path = args[0]
#     root = kwargs["root"]
#     hooks: Hooks = kwargs["hooks"]

#     dir_path = join_relative_path(root, dir_path)
#     logger.info(f"Create ROS launch information for {dir_path}")

#     packages = kwargs["packages"] if "packages" in kwargs else Package.getPackages(dir_path)

#     content = list()
#     content.append(f"# ROS Launch Scripts")
#     hooks.append_to_content(__name__, "", content)

#     scripts = list()

#     for package in packages:
#         if package.package_type == PackageType.PYTHON:
#             if len(package.launch_scripts) > 0:
#                 for script in package.launch_scripts:

#                     scripts.append(
#                         {
#                             "Name": script.name,
#                             "Info": adapt_string_for_table(script.info),
#                             "Script": get_link(script.name, file_utils.get_relative_path(script.launch_file_path, root)),
#                         }
#                     )

#     scripts.sort(key=lambda x: x["Name"])

#     if len(scripts) > 0:
#         content.append(markdownTable(scripts).setParams(row_sep="markdown", quote=False).getMarkdown())
#     else:
#         content.append("This package has no launch scripts")

#     return "\n\n".join(content)
