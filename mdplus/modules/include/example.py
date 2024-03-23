import os
import logging

import re

from mdplus.core import Replacement

from mdplus.util.markdown import get_header
from mdplus.util.regex import replace_pattern
from mdplus.util.file_utils import join_relative_path

from mdplus.modules.flags import Flags

logger = logging.getLogger(__name__)

ignore_line = re.compile(r".*?(" + re.escape(Flags.IGNORE_LINE) + r").*?\n")
ignore_section = re.compile(re.escape(Flags.IGNORE_START) + r".*?" + re.escape(Flags.IGNORE_END), re.DOTALL)
ignore_start = re.compile(re.escape(Flags.IGNORE_START) + r".*?", re.DOTALL)

empty_lines = re.compile(r"(\s*?\n){3,}", re.MULTILINE)


def remove_empty_lines(text: str):
    return empty_lines.sub("\n\n", text)

def process_ignored(text: str):
    text = replace_pattern(text, ignore_line, only_first=False)
    text = replace_pattern(text, ignore_section, only_first=False)
    text = replace_pattern(text, ignore_start, only_first=False)
    return text


def process_py(file_path: str, relative_link: str, **kwargs) -> Replacement:
    output = ""

    with open(file_path, "r", encoding="utf-8") as f:
        input_text = f.read()

        inline = kwargs.get("inline", False)
        text_before_cmd = kwargs.get("text_before_cmd", "")

        # Remove shebang and other top level comments
        while input_text.startswith("#"):
            input_text = input_text[input_text.find("\n") + 1:]

        input_text = process_ignored(input_text)


        comment_block_pattern = re.compile(r'"""((""?(?!")|[^"])*)"""')
        header_pattern = re.compile(r"# (.*?)\n\n")
        
        first_comment_block = comment_block_pattern.search(input_text)
        if first_comment_block is not None:
            text: str = first_comment_block.group(1)
            
            # If we do not have an explicit header starting with markdowns header-# in the example
            if not text.strip().startswith("# "):
                # If the command is used inline, use the text before the command as header
                if inline and len(text_before_cmd) > 0:
                    header = text_before_cmd
                # Otherwise use the file name as header
                else:
                    header = os.path.basename(file_path)
                output += f"# [{header}]({relative_link})\n"
            # If we have an explicit header in the example
            else:
                m = header_pattern.search(text)
                if m is not None:
                    # If the command is used inline, use the text before the command as header
                    if inline and len(text_before_cmd) > 0:
                        header = text_before_cmd
                    # Otherwise use the header from the example documenation
                    else:
                        header = m.group(1)
                    start, end = m.span()
                    text = text[:start] + f"# [{header}]({relative_link})\n" + text[end:]

                input_text = input_text[:first_comment_block.start(1)] + text + input_text[first_comment_block.end(1):]

        while comment_block := comment_block_pattern.search(input_text):
            start, end = comment_block.span()

            text = comment_block.group(1)

            if start > 0:
                new_part = input_text[:start].strip()
                if len(new_part) > 0:
                    output += "```python\n"
                    output += new_part
                    output += "\n```\n\n"

            if text:
                text = text.strip()
                output += "\n" + text + "\n\n"

            # Remove everything to the section in the input string
            input_text = input_text[end:]

        if len(input_text) > 0:
            new_part = input_text.strip()
            if len(new_part) > 0:
                output += "```python\n"
                output += new_part
                output += "\n```\n\n"

    replacement = Replacement(remove_empty_lines(output))
    # If the command was inline, we also replace the text before the command since we already used it as header
    replacement.replaces_text_before_cmd = inline

    return replacement
    # return remove_empty_lines(output)


def main(*args, **kwargs):
    # print("Hello from include.py", args, kwargs)

    file = args[0]
    relative_link = file

    logger.info(f"Including example {file}")

    root = kwargs["root"]

    file = join_relative_path(root, file)

    # Check if file exists
    if not os.path.isfile(file):
        logger.error(f"Example file {file} to be included does not exist")
        return Replacement(f"# {file} NOT FOUND")
    else:
        return process_py(file, relative_link, **kwargs)

    return "ERROR"
