import os
import logging

from mdplus.core.modules import MdpModule
from mdplus.util.file_utils import join_relative_path
from mdplus.config import ExamplesConfig

from markdownTable import markdownTable

import pandas as pd

from mdplus.util.hooks import Hooks

logger = logging.getLogger(__name__)


class ContentMdpModule(MdpModule):
    """Creates a table of contents of the given directory"""
    def __init__(self, command: str, arguments: dict[str, any]):
        super().__init__(command, arguments)

        self.arg_header = self.get_arg("header", "# Contents of this Repository")

    def get_content(self) -> str:
        
        content = list()
        content.append(self.arg_header)

        dir_path = self.root

        logger.info(f"Creating content of {dir_path}")

        # Check if directory exists
        if not os.path.isdir(dir_path):
            logger.error(f"Directory {dir_path} for creating table of contents does not exist")
            content.append(f"# {dir_path} NOT FOUND")
        else:
            entries = dict()

            # Iterate over all directories in the given directory and search for README.md files
            for file in os.listdir(dir_path):
                if file.startswith(".") or file.startswith("_"):
                    continue

                # Check if file is a directory
                dir = os.path.join(dir_path, file)
                if os.path.isdir(dir):
                    info = file

                    # Check if directory contains a MDP_IGNORE file
                    if os.path.isfile(os.path.join(dir, "MDP_IGNORE")):
                        continue

                    # Check if dir has a mdplus.json file
                    mdplus_json = os.path.join(dir, "mdplus.json")
                    if os.path.isfile(mdplus_json):
                        mdplus_config = ExamplesConfig.from_file(mdplus_json)
                        if mdplus_config.info:
                            info = mdplus_config.info

                    # Check if dir has a README.md file
                    elif os.path.isfile(os.path.join(dir, "README.md")):
                        # Extract the first row of this file
                        with open(os.path.join(dir, "README.md"), "r", encoding="utf-8") as f:
                            logger.info(f"Read contents of {os.path.join(dir, 'README.md')}")

                            # Search for the first row of the file that is not a header
                            lines = [l.strip() for l in f.readlines()]
                            lines = [l for l in lines if len(l) > 0]
                            found = False
                            for line in lines:
                                if line.startswith("#"):
                                    continue

                                info = line
                                found = True
                                break

                            # If there are only headers
                            if not found:
                                for line in lines:
                                    if line.startswith("#"):
                                        info = line.replace("#", "").strip()
                                        break

                    file_entry = f"[`{file}`]({file})"
                    entries[file_entry] = info

            # Convert entries to a dataframe
            df = pd.DataFrame(entries.items(), columns=["Dir", "Content"])

            # Create a Markdown table out of the dataframe
            mkdict = df.to_dict(orient="records")
            content.append(markdownTable(mkdict).setParams(row_sep="markdown", quote=False).getMarkdown())

            return "\n\n".join(content)


module = ContentMdpModule