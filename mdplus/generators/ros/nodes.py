import os
import logging
from typing import Dict, List

import re

from mdplus.util.file_utils import join_relative_path

from mdplus.core.generator import MdpGenerator

from markdownTable import markdownTable

from mdplus.util.hooks import Hooks
from mdplus.util.parser.ros2_parser import Package, MessageType, ServiceType, Workspace, Topic, PackageType, Node
from mdplus.util.markdown import get_anchor_from_header, get_link, adapt_header_level
import mdplus.util.file_utils as file_utils

import pandas as pd

from mdplus.generators.flags import Flags

logger = logging.getLogger(__name__)


class RosNodesMdpModule(MdpGenerator):
    def __init__(self, command: str, arguments: Dict[str, any]):
        super().__init__(command, arguments)

        self.arg_header = self.get_arg("header", "# ROS Nodes")
        
        self.arg_only_commented_publishers = self.get_arg("only_commented_publishers", True)
        self.arg_only_commented_subscriptions = self.get_arg("only_commented_subscriptions", True)
        self.arg_only_commented_services = self.get_arg("only_commented_services", True)
        self.arg_include_parameters = self.get_arg("include_parameters", True)

    @staticmethod
    def get_nodes_table(packages: List[Package], root) -> str:
        nodes = []
        for package in packages:
            if package.package_type == PackageType.PYTHON:
                if len(package.nodes) > 0:
                    for node in package.nodes:
                        anchor = get_anchor_from_header(f"`{node.name}` Node")
                        nodes.append(
                            {
                                "Package": package.name,
                                "Name": get_link(node.name, f"#{anchor}"),  # node.name,
                                "Info": node.info,
                                "Script": get_link(node.script, file_utils.get_relative_path(node.script_path, root)),
                            }
                        )

        nodes.sort(key=lambda x: x["Name"])
        if len(nodes) == 0:
            return ""

        return markdownTable(nodes).setParams(row_sep="markdown", quote=False).getMarkdown()

    def get_content(self) -> str:
        """Creates a table of nodes found in the ROS-packages"""

        dir_path = self.root
        logger.info(f"Create ROS node information for {dir_path}")

        packages: list[Package] = self.arguments.get("packages", Package.getPackages(dir_path))

        content = list()
        content.append(self.arg_header)

        content.append(self.get_nodes_table(packages, self.file_dir))

        has_nodes = False

        for package in packages:
            if package.package_type == PackageType.PYTHON:
                if len(package.nodes) > 0:
                    for node in package.nodes:
                        content.append(self.get_node_section(node))
                        has_nodes = True

        if not has_nodes:
            content.append("This package has no ROS nodes.")

        return "\n\n".join(content)


    def get_node_section(self, node: Node) -> str:
        content = []
        topics = []

        content.append(f"## `{node.name}` Node")
        content.append(adapt_header_level(node.doc_string_without_header, 2))

        #################################################################################
        ### Topic stuff

        for service in node.services:
            if not self.arg_only_commented_services or len(service.comment) > 0:
                if Flags.IGNORE in service.comment:
                    continue
                topics.append(
                    {
                        "Topic": service.topic_name,
                        "Type": service.service_type,
                        "Kind": "Service",
                        "Comment": service.comment,
                    }
                )

        for publisher in node.publisher:
            if not self.arg_only_commented_publishers or len(publisher.comment) > 0:
                if Flags.IGNORE in publisher.comment:
                    continue
                topics.append(
                    {
                        "Topic": publisher.topic_name,
                        "Type": publisher.msg_type,
                        "Kind": "Publisher",
                        "Comment": publisher.comment,
                    }
                )

        for subscription in node.subscriptions:
            if not self.arg_only_commented_subscriptions or len(subscription.comment) > 0:
                if Flags.IGNORE in subscription.comment:
                    continue
                topics.append(
                    {
                        "Topic": subscription.topic_name,
                        "Type": subscription.msg_type,
                        "Kind": "Subscription",
                        "Comment": subscription.comment,
                    }
                )

        # For each topic create a section with the doc string as information
        for topic in topics:
            comment = topic["Comment"]
            topic["Info"] = comment.split("\n")[0] if comment is not None else Flags.NOT_FOUND
            topic["HasLink"] = False
            if comment is None or len(comment) == 0 or Flags.NOT_FOUND in comment or topic["Info"] == comment:
                continue

            topic["HasLink"] = True

            parts = [
                f'### `{topic["Topic"]}`',
                # f'{topic["Kind"]} of type {topic["Type"]}'
            ]
            if comment is not None and len(comment) > 0:
                parts.extend([
                    f"```",
                    f"{comment}",
                    f"```"
                ])
            part = "\n".join(parts)
            content.append(part)

        # Adapt the topics for the Markdown table
        has_other_topics_than_not_found = False
        for topic in topics:
            if topic["HasLink"]:
                topic["Topic"] = get_link(topic["Topic"], f"#{get_anchor_from_header(topic['Topic'])}", emphasize=True)
            else:
                topic["Topic"] = f"`{topic['Topic']}`"

            topic["Type"] = get_link(topic["Type"], f"#{get_anchor_from_header(topic['Type'])}", emphasize=True)

            if topic["Info"] != Flags.NOT_FOUND:
                has_other_topics_than_not_found = True

            del topic["Comment"]
            del topic["HasLink"]

        if not has_other_topics_than_not_found:
            for topic in topics:
                del topic["Info"]

        if len(topics) > 0:
            topics.sort(key=lambda x: x["Topic"])
            table = markdownTable(topics).setParams(row_sep="markdown", quote=False,
                                                    padding_weight='right').getMarkdown()
            content.insert(2, "**Publisher, Subscriber and Services of this node**")
            content.insert(3, table)

        #################################################################################
        ### Parameter stuff

        if self.arg_include_parameters:
            parameters = []
            for parameter in node.parameters:
                if Flags.IGNORE in parameter.comment:
                    continue
                parameters.append(
                    {
                        "Name": parameter.name,
                        # "Type": parameter.type,
                        "Default": parameter.value,
                        "Info": parameter.comment,
                    }
                )
            if len(parameters) > 0:
                parameters.sort(key=lambda x: x["Name"])
                table = markdownTable(parameters).setParams(row_sep="markdown", quote=False,
                                                            padding_weight='right').getMarkdown()
                content.insert(2, "**Parameters of this node**")
                content.insert(3, table)

        return "\n\n".join(content)


module = RosNodesMdpModule
