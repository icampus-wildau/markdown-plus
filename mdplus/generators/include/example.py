import logging
import os
import re

from mdplus.core.documents.block import MdpBlock
from mdplus.core.documents.document import Document
from mdplus.core.generator import MdpGenerator
from mdplus.generators.flags import Flags
from mdplus.util.regex import replace_pattern

from overrides import overrides

logger = logging.getLogger(__name__)

ignore_line = re.compile(r".*?(" + re.escape(Flags.IGNORE_LINE) + r").*?\n")
ignore_section = re.compile(r"#\s*?" + re.escape(Flags.IGNORE_START) + r".*?" + re.escape(Flags.IGNORE_END), re.DOTALL)
ignore_start = re.compile(r"#\s*?" + re.escape(Flags.IGNORE_START) + r".*?", re.DOTALL)

empty_lines = re.compile(r"(\s*?\n){3,}", re.MULTILINE)


class ExampleIncluder(MdpGenerator):
    def __init__(self, document: Document, mdp_block: MdpBlock):
        super().__init__(document, mdp_block)

        self.arg_path = self.get_arg("path", None)
        self.arg_header = self.get_arg("header", None)

    @overrides
    def get_content(self) -> str:
        logger.info(f"Including example file: {self.arg_path} in {self.document.full_path}")

        # Check if file exists
        contents = []
        contents.append(self.process_py())

        return "\n".join(contents)

        return "ERROR"

    @staticmethod
    def remove_empty_lines(text: str):
        return empty_lines.sub("\n\n", text.strip())

    @staticmethod
    def process_ignored(text: str):
        text = replace_pattern(text, ignore_line, only_first=False)
        text = replace_pattern(text, ignore_section, only_first=False)
        text = replace_pattern(text, ignore_start, only_first=False)
        return text

    def process_py(self):
        output = ""
        file_path = os.path.abspath(os.path.join(self.document.dir_path, self.arg_path))
        relative_link = self.arg_path

        if not os.path.isfile(file_path):
            logger.error(f"File {file_path} does not exist")
            return f"ERROR: File {self.arg_path} does not exist"

        with open(file_path, "r", encoding="utf-8") as f:
            input_text = f.read()

            # Remove shebang and other top level comments
            while input_text.startswith("#"):
                input_text = input_text[input_text.find("\n") + 1 :]

            input_text = self.process_ignored(input_text)

            comment_block_pattern = re.compile(r'"""((""?(?!")|[^"])*)"""')

            first_comment_block = comment_block_pattern.search(input_text)
            if first_comment_block is not None:
                text: str = first_comment_block.group(1)
                # If we do not have an explicit header starting with markdowns header-# in the example
                if not text.strip().startswith("# "):
                    header = self.arg_header or os.path.basename(file_path)
                    
                    # output += f"# [{header}]({relative_link})\n"
                    output += f"# {header}\n"
                    # output += f"See [{relative_link.lstrip('./')}](./" + relative_link + ").\n\n"


                # If we have an explicit header in the example
                else:
                    header_pattern = re.compile(r"# (.*?)\n\n")
                    m = header_pattern.search(text)
                    if m is not None:
                        header = self.arg_header or m.group(1)
                        start, end = m.span()
                        
                        # text = text[:start] + f"# [{header}]({relative_link})\n" + text[end:]
                        end = text[end:]
                        text = text[:start] + f"# {header}\n" 
                        text += f"See [{relative_link.lstrip('./')}](./" + relative_link + ").\n\n"
                        text += end



                    input_text = (
                        input_text[: first_comment_block.start(1)] + text + input_text[first_comment_block.end(1) :]
                    )

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

            output += f"Source of the above code: [{relative_link.lstrip('./')}](./" + relative_link + ").\n\n"


        return self.remove_empty_lines(output)
