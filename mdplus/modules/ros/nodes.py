import os
import logging
from typing import Dict, List

import re

from mdplus.util.file_utils import join_relative_path

from markdownTable import markdownTable

from mdplus.util.hooks import Hooks
from mdplus.util.parser.ros2_parser import Package, MessageType, ServiceType, Workspace, Topic, PackageType, Node
from mdplus.util.markdown import get_anchor_from_header, get_link, adapt_header_level
import mdplus.util.file_utils as file_utils

import pandas as pd

from mdplus.modules.flags import Flags

logger = logging.getLogger(__name__)


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


def get_node_section(node: Node, kwargs) -> str:
    content = []
    topics = []
    hooks: Hooks = kwargs["hooks"]

    content.append(f"## `{node.name}` Node")
    content.append(adapt_header_level(node.doc_string_without_header, 2))

    hooks.append_to_content(__name__, node.name, content)

    only_commented_pub = kwargs["only_commented_publisher"] if "only_commented_publisher" in kwargs else False
    only_commented_sub = kwargs["only_commented_subscription"] if "only_commented_subscription" in kwargs else False
    only_commented_ser = kwargs["only_commented_services"] if "only_commented_services" in kwargs else False
    include_parameters = kwargs["include_parameters"] if "include_parameters" in kwargs else True

    #################################################################################
    ### Topic stuff

    for service in node.services:
        if not only_commented_ser or len(service.comment) > 0:
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
        if not only_commented_pub or len(publisher.comment) > 0:
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
        if not only_commented_sub or len(subscription.comment) > 0:
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
        hooks.append_to_content(__name__, [node.name, "topics"], content, 3)

    #################################################################################
    ### Parameter stuff

    if include_parameters:
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
            hooks.append_to_content(__name__, [node.name, "parameters"], content, 3)

    return "\n\n".join(content)


def main(*args, **kwargs):
    """Creates a table of nodes found in the ROS-packages"""

    dir_path = args[0]
    root = kwargs["root"]

    dir_path = join_relative_path(root, dir_path)
    logger.info(f"Create ROS node information for {dir_path}")

    packages = kwargs["packages"] if "packages" in kwargs else Package.getPackages(dir_path)

    content = list()
    content.append(f"# ROS Nodes")

    hooks: Hooks = kwargs["hooks"]
    hooks.append_to_content(__name__, "", content)

    content.append(get_nodes_table(packages, root))

    has_nodes = False

    for package in packages:
        if package.package_type == PackageType.PYTHON:
            if len(package.nodes) > 0:
                for node in package.nodes:
                    content.append(get_node_section(node, kwargs))
                    has_nodes = True

    if not has_nodes:
        content.append("This package has no ROS nodes.")

    return "\n\n".join(content)
