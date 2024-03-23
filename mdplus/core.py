import re

pattern_headers = re.compile(r"#+ .*")
pattern_headers_inside_code = re.compile(r"```(.|[\n\s$^])*?(# .*?\n)(.|[\n\s$^])*?```")

pattern_code_block = re.compile(r"```(.|[\n\s$^])*?```")

class Replacement:
    """Helper object for replacements of md+ commands in markdown files"""
    def __init__(self, text, replaces_text_before_cmd=False):
        """Craete a new Replacement object

        Parameters
        ----------
        text : str
            The replacement text for the original command
        replaces_text_before_cmd : bool, optional
            If True, the text before the command is also replaced by this replacement, by default False
        """

        self.text = text
        """The replacement text for the original command"""
        self.replaces_text_before_cmd = replaces_text_before_cmd
        """If True, the text before the command is also replaced by this replacement"""

    def __str__(self):
        return self.text

    def adapt_header_level(self, count: int):
        if count < 0:
            count = 0

        if count == 0:
            return

        last_matched_position = 0

        code_blocks: list[tuple[int, int]] = []
        for match in pattern_code_block.finditer(self.text):
            code_blocks.append(match.span())

        while m := pattern_headers.search(self.text, last_matched_position):
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
            self.text = self.text[:start] + "#" * count + self.text[start:]

            # Add count to each value in code_blocks that is greater than start
            for i, code_block in enumerate(code_blocks):
                if code_block[0] >= start:
                    code_blocks[i] = (code_block[0] + count, code_block[1] + count)

        return self.text
