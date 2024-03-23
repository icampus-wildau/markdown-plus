import os
import logging

import re

from mdplus.util.markdown import get_header
from mdplus.util.file_utils import join_relative_path

from mdplus.modules.flags import Flags

logger = logging.getLogger(__name__)

# ignore_pattern = re.compile(r"<!--\s*?(#MD\+flag:IGNORE_INCLUDE)\s*?-->")
ignore_pattern = re.compile(r"<!--\s*?(" + re.escape(Flags.IGNORE_START) + ")\s*?-->")


def main(*args, **kwargs):
    # print("Hello from include.py", args, kwargs)

    include_file = args[0]
    relative_link = include_file

    logger.info(f"Including file {include_file}")

    root = kwargs["root"]

    include_file = join_relative_path(root, include_file)

    # Check if file exists
    if not os.path.isfile(include_file):
        logger.error(f"File {include_file} to be included does not exist")
        return f"# {include_file} NOT FOUND"

    with open(include_file, "r") as f:
        text = f.read()

        # Ignore everything that comes after the <!-- #MD+flag:IGNORE_INCLUDE --> flag
        m = ignore_pattern.search(text)
        if m is not None:
            start, end = m.span()
            text = text[:start]

        # Link the header to the source file
        first_header = get_header(text, level=0)
        if first_header is not None:
            start, end = first_header.span()
            hashtags = first_header.group(1)
            header_text = first_header.group(2)

            header_text = f"{hashtags}[{header_text}]({relative_link})"

            # Replace the first header with the link
            text = text[:start] + header_text + text[end:]

        return text
