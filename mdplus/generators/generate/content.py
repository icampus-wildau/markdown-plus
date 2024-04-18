from __future__ import annotations
import os
import logging

from mdplus.core.generator import MdpGenerator

from markdownTable import markdown_table

import pandas as pd


logger = logging.getLogger(__name__)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from mdplus.core.documents.document import Document
    from mdplus.core.documents.block import MdpBlock

class ContentGenerator(MdpGenerator):
    """Creates a table of contents of the given directory"""
    def __init__(self, document: Document, mdpBlock: MdpBlock):
        super().__init__(document, mdpBlock)

        self.arg_header = self.get_arg("header", "# Contents of this Repository")
        self.arg_dirs = self.get_arg("dirs", True)
        self.arg_md_files = self.get_arg("md_files", False)

    def get_content(self) -> str:
        
        content = list()
        if len(self.arg_header) > 0:
            content.append(self.arg_header)

        # dir_path = self.workspace.root_path
        dir_path = self.document.dir_path

        logger.info(f"Creating content of {dir_path}")

        # Check if directory exists
        if not os.path.isdir(dir_path):
            logger.error(f"Directory {dir_path} for creating table of contents does not exist")
            content.append(f"# {dir_path} NOT FOUND")
        else:
            entries = dict()

            # Iterate over all directories in the given directory and search for README.md files
            files = os.listdir(dir_path)
            files.sort()
            for file in files:
                if file.startswith(".") or file.startswith("_"):
                    continue

                # Check if file is a directory
                dir = os.path.join(dir_path, file)
                if os.path.isdir(dir) and self.arg_dirs:
                    info = file

                    # Check if directory contains a MDP_IGNORE file
                    if os.path.isfile(os.path.join(dir, "MDP_IGNORE")):
                        continue

                    mdp_dir = self.workspace.directory_map.get(dir, None)
                    need_parse = True
                    
                    # If there is a readme file in the directory, check for given args in that file
                    if mdp_dir is not None:
                        if mdp_dir.readme is not None:
                            # If title is given in the args, use this as info
                            if "title" in mdp_dir.readme.args:
                                info = mdp_dir.readme.args["title"]
                                need_parse = False

                    # If there are no md+ args, parse the readme file
                    if need_parse and mdp_dir.readme is not None:
                        # Extract the first line of this file
                        with open(mdp_dir.readme.full_path, "r", encoding="utf-8") as f:
                            logger.debug(f"Read contents of {os.path.join(dir, 'README.md')}")

                            # Search for the first line of the file that is not a header
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
                elif self.arg_md_files and file.endswith(".md"):

                    path = os.path.join(dir_path, file)
                    
                    # Skip the own file
                    if path == self.document.full_path:
                        continue

                    doc = self.workspace.document_map.get(path, None)

                    basename = os.path.basename(file)
                    if doc is not None:
                        info = doc.get_title() or doc.file_name
                    else:
                        info = basename
                    
                    file_entry = f"[`{basename}`]({file})"
                    entries[file_entry] = info


            # Convert entries to a dataframe
            df = pd.DataFrame(entries.items(), columns=["Directory", "Content"])

            # Create a Markdown table out of the dataframe
            mkdict = df.to_dict(orient="records")
            content.append(markdown_table(mkdict).set_params(row_sep="markdown", quote=False, padding_weight="right").get_markdown())

            return "\n\n".join(content)
