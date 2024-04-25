import re
from typing import List, Union


def replace_pattern(
    file_content: str,
    pattern: Union[str, re.Pattern],
    group: Union[int, List[int]] = 0,
    substitution: str = "",
    only_first=True,
) -> str:
    """Replaces all matches of the given pattern with the given replacement.

    Args:
        file_content (str): The content of the file to be modified.
        pattern (Union[str, re.Pattern]): The regex pattern to be replaced.
        group (Union[int, List[int]], optional): If != 0 just replace the specified group of the match. Defaults to 0.
        substitution (str, optional): Replacement string. Defaults to "".
        only_first (bool, optional): If True only the first match is replaced. Defaults to True.

    Returns:
        str: The modified file content.
    """

    if isinstance(pattern, str):
        pattern = re.compile(pattern)

    content = file_content
    pos = 0

    while True:
        match = pattern.search(content, pos)
        if match:
            pos = match.start() + len(substitution)
            if isinstance(group, int):
                start_pos, end_pos = match.span(group)
                content = content[:start_pos] + substitution + content[end_pos:]
            elif isinstance(group, list):
                group.reverse()
                for g in group:
                    start_pos, end_pos = match.span(g)
                    content = content[:start_pos] + substitution + content[end_pos:]

        else:
            break

        if only_first:
            break

    return content
