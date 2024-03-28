import os
import logging
from typing import Dict, List

from mdplus.util.file_utils import join_relative_path

from mdplus.util.parser.ros2_parser import Package

import mdplus.generators.ros.launchs as launchs
import mdplus.generators.ros.interfaces as interfaces
import mdplus.generators.ros.nodes as nodes

from mdplus.util.markdown import adapt_header_level

logger = logging.getLogger(__name__)


def main(*args, **kwargs):
    """Creates a table of messages and services found in the ROS-packages"""

    root = kwargs["root"]
    hooks = kwargs["hooks"]

    path = join_relative_path(root, args[0]) if len(args) > 0 else root
    logger.info(f"Create complete ROS information for {path}")

    content = [kwargs.get("header", "# ROS Information")]
    hooks.append_to_content([__name__, ".".join(__name__.split(".")[:-1])], "", content)

    packages = Package.getPackages(path)
    kwargs["packages"] = packages

    content.extend([
        adapt_header_level(launchs.main(*args, **kwargs), 1),
        adapt_header_level(nodes.main(*args, **kwargs), 1),
        # adapt_header_level(topics.main(*args, **kwargs), 1),
        adapt_header_level(interfaces.main(*args, **kwargs), 1),
    ])

    return "\n\n".join(content)
