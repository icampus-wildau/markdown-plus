import os
import logging
from typing import Dict, List

from markdownTable import markdownTable

from mdplus.util.file_utils import join_relative_path
from mdplus.util.hooks import Hooks

from mdplus.util.parser.ros2_parser import Package, MessageType, ServiceType, Workspace, Topic, PackageType
from mdplus.util.markdown import get_anchor_from_header

import pandas as pd

logger = logging.getLogger(__name__)


def main(*args, **kwargs):
    """Creates a table of messages and services found in the ROS-packages"""

    dir_path = args[0]
    root = kwargs["root"]

    dir_path = join_relative_path(root, dir_path)
    logger.info(f"Create ROS message and service information for {dir_path}")

    packages = kwargs["packages"] if "packages" in kwargs else Package.getPackages(dir_path)

    hooks: Hooks = kwargs["hooks"]
    content = list()

    content.append(f"# ROS Message and Service Definitions")
    hooks.append_to_content(__name__, "", content)

    for package in packages:
        if package.package_type == PackageType.CMAKE:
            if len(package.messages) > 0 or len(package.services) > 0:
                content.append(get_table(package, msgs=True, srv=True))

    for package in packages:
        if package.package_type == PackageType.CMAKE:
            if len(package.messages) > 0:
                content.append(f"## Message definitions of {package.name}")
                for message in package.messages:
                    content.append(message.get_wiki_entry(3, root))
            if len(package.services) > 0:
                content.append(f"## Service definitions of {package.name}")
                for service in package.services:
                    content.append(service.get_wiki_entry(3, root))

    if len(content) == 1:
        content.append(f"This package has no custom message or service type definitions.")

    return "\n\n".join(content)


def get_table(package: Package, msgs=True, srv=True):
    """Creates a table of messages and services found in the ROS-packages"""

    msg_data: List[Dict[str, str]] = list()
    srv_data: List[Dict[str, str]] = list()

    if msgs:
        for msg in package.messages:
            msg_data.append({"Name": f"[`{msg.name}`](#{get_anchor_from_header(msg.name)})", "Type": "Message", "Package": package.name})

    if srv:
        for srv in package.services:
            srv_data.append({"Name": f"[`{srv.name}`](#{get_anchor_from_header(srv.name)})", "Type": "Service", "Package": package.name})

    msg_data.sort(key=lambda x: x["Name"])
    srv_data.sort(key=lambda x: x["Name"])

    return markdownTable(msg_data + srv_data).setParams(row_sep="markdown", quote=False).getMarkdown()
