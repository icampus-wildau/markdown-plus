import re
import string
from typing import List, Tuple

# from mdplus.core import Replacement

headers = re.compile(r"#+ .*")
headers_inside_code = re.compile(r"```(.|[\n\s$^])*?(# .*?\n)(.|[\n\s$^])*?```")

code_block_pattern = re.compile(r"```(.|[\n\s$^])*?```")


# def adapt_header_level(markdown: str | Replacement, count: int):
def adapt_header_level(markdown: str, count: int):
    if count < 0:
        count = 0

    if count == 0:
        return markdown

    last_matched_position = 0

    code_blocks: List[Tuple[int, int]] = []
    for match in code_block_pattern.finditer(markdown):
        code_blocks.append(match.span())

    while True:
        m = headers.search(markdown, last_matched_position)
        if m is None:
            break

        start, end = m.span()
        last_matched_position = end + count

        # Skip code blocks
        skip = False
        for code_block in code_blocks:
            if start >= code_block[0] and end <= code_block[1]:
                last_matched_position = code_block[1]
                skip = True
                break

        if skip:
            continue

        # Add count to header
        markdown = markdown[:start] + "#" * count + markdown[start:]

        # Add count to each value in code_blocks that is greater than start
        for i, code_block in enumerate(code_blocks):
            if code_block[0] >= start:
                code_blocks[i] = (code_block[0] + count, code_block[1] + count)

    return markdown


def get_header(markdown: str, level: int = 0, start_position: int = 0) -> re.Match:
    pattern = r"(#+ )(.*)" if level == 0 else f"(#{'#' * level} )(.*)"
    headers = re.compile(pattern)

    return headers.search(markdown, start_position)


gitlab_punctuation = string.punctuation.replace("_", "")


def get_anchor_from_header(header: str):
    """According to https://docs.gitlab.com/ee/user/markdown.html#header-ids-and-links"""

    # Remove all punctuation
    anchor = header.translate(str.maketrans('', '', gitlab_punctuation))

    # Replace all whitespace with dashes
    splits = re.split(r"\W", anchor)
    anchor = "-".join([s.lower() for s in splits if len(s) > 0])
    return anchor


def get_link(name: str, link: str, emphasize: bool = False) -> str:
    if emphasize:
        return f"[`{name}`]({link})"
    else:
        return f"[{name}]({link})"


def adapt_string_for_table(s: str) -> str:
    s = s.replace("|", "\\|")
    s = s.replace("\n", "<br>")
    return s
