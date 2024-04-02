import json
import os
import logging

import re

from mdplus.core import Replacement

from mdplus.util.markdown import get_header
from mdplus.util.regex import replace_pattern
from mdplus.util.file_utils import join_relative_path

from mdplus.generators.flags import Flags
from mdplus.config import ExamplesConfig, Examples

import mdplus.generators.include.example as example

from mdplus.util.markdown import adapt_header_level


logger = logging.getLogger(__name__)

ignore_line = re.compile(r".*?(" + re.escape(Flags.IGNORE_LINE) + r").*?\n")

def main(*args, **kwargs):
    directory = args[0]
    relative_link = directory

    logger.info(f"Including examples from {directory}")

    root = kwargs["root"]
    header = kwargs.get("header", "# Examples\n\n")

    path = join_relative_path(root, directory)

    # Check if dir exists
    if not os.path.isdir(path):
        logger.error(f"Directory for example files {path} does not exist")
        return Replacement(f"# {path} NOT FOUND")
    else:

        # Search for mdplus.json
        mdplus_json = os.path.join(path, "mdplus.json")
        mdplus_config = ExamplesConfig.from_file(mdplus_json)

        included_files = set()
        content: list[Replacement] = []

        # If order list is given, first iterate all files from that list
        for file in [os.path.join(path, f) for f in mdplus_config.examples.order]:
            included_files.add(file)
            content.append(example.main(file, **kwargs))

        # Iterate over all python files in the directory and call example.main
        if not mdplus_config.examples.ignoreUnlisted:
            for file in os.listdir(path):
                if file.endswith(".py") and not file.startswith("__") and file not in mdplus_config.examples.ignore:
                    f_path = os.path.join(path, file)
                    if f_path not in included_files:
                        included_files.add(f_path)
                        content.append(example.main(os.path.join(path, file), **kwargs))

        # print(content)
        # content = [adapt_header_level(c, 1) for c in content]
        for replacement in content:
            replacement.adapt_header_level(1)

        replacement = Replacement(header + "\n\n".join([str(r) for r in content]))

        return replacement

    return "ERROR"
