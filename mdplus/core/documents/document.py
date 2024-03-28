from __future__ import annotations
import logging
import os

from mdplus.core.documents.definitions import CommentDefinition
from mdplus.core.documents.block import MdpBlock
from mdplus.core.generator import MdpGenerator

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from mdplus.core.documents.structure import Workspace

logger = logging.getLogger(__name__)



class Document:
    """
    Base class for documents in a workspace.
    """

    def __init__(self, 
                 file_path: str, 
                 workspace: Workspace,
                 comment_definition: CommentDefinition = CommentDefinition.get_python_style(),
                ):
        self.full_path = os.path.abspath(file_path)
        self.dir_path = os.path.dirname(file_path)
        self.file_name = os.path.basename(file_path)

        self.comment_definition = comment_definition


        self.workspace = workspace
        workspace.document_map[file_path] = self

        self.is_readme = self.file_name.lower() in ["readme.md", "readme"]

        # logger.debug(f"Creating document {self.full_path} {self.file_name} {self.is_readme}")

        self.mdp_pattern = MdpBlock.get_pattern(comment_definition)
        
        self._args: dict[str, any] = None
        """MDP args of the document."""

        # TODO: Parse meta info from the document

    @property
    def args(self) -> dict[str, any]:
        if self._args is None:
            self._args = self.parse_args()
        return self._args


    def parse_args(self):

        # Read the first lines that are either empty or multiline comments
        relevant_lines: list[str] = []
        
        with open(self.full_path, "r", encoding="utf-8") as f:
            started = False
            for line in f:
                if line.strip() == "":
                    continue

                # TODO: At the moment we ignore single line comments
                # if line.strip().startswith(self.comment_definition.single_line):
                #     relevant_lines.append(line.strip()[len(self.comment_definition.single_line):])
                #     continue

                if any([line.strip().startswith(start) for start in self.comment_definition.multi_line_start]):
                    started = True
                    relevant_lines.append(line.strip())
                    
                    if any([line.strip().endswith(end) for end in self.comment_definition.multi_line_end]):
                        break

                    continue
                else:
                    if not started:
                        break

                    if started:
                        relevant_lines.append(line.strip())
                        if any([line.strip().endswith(end) for end in self.comment_definition.multi_line_end]):
                            break

        block = "\n".join(relevant_lines)
        # logger.debug(f"Found block in {self.full_path}: {block}")
        if (match := self.mdp_pattern.search(block)) is not None:
            mdp_block = MdpBlock(match)
            mdp_block.arguments_str
            # logger.debug(f"Found MDP block in {self.full_path}: {mdp_block.command} {mdp_block.arguments_str} {mdp_block.arguments}")
            return mdp_block.arguments

        return {}

    def from_file(file_path: str, workspace: Workspace) -> Document:
        ending = os.path.splitext(file_path)[1]
        if ending == ".md":
            return GeneratedDocument(file_path, workspace, CommentDefinition.get_markdown_style())
        
        if ending == ".py":
            return Document(file_path, workspace, CommentDefinition.get_python_style())
        
        return Document(file_path, workspace, CommentDefinition.get_cpp_style())




class GeneratedDocument(Document):
    def __init__(self, file_path: str, workspace: Workspace, comment_definition: CommentDefinition = CommentDefinition.get_python_style()):
        super().__init__(file_path, workspace, comment_definition)

        self.origin_text = None

        return
        # text = ""
        # logger.info(f"Parsing {self.full_path}")
        # with open(file_path, "r", encoding="utf-8") as f:
        #     text = f.read()

        # self.context = context if context is not None else dict()
        # if "root" not in self.context:
        #     self.context["root"] = os.path.dirname(file_path)
        # self.context["file_path"] = file_path
        # self.context["file_dir"] = self.dir_path

        # self.origin_text = text
        # self.modules = MdpGenerator.get_all_generators(text, self.context)

    def process(self):
        logger.info(f"Processing document: {self.full_path}")

        text = ""
        with open(self.full_path, "r", encoding="utf-8") as f:
            text = f.read()

        # self.context = context if context is not None else dict()
        # if "root" not in self.context:
        #     self.context["root"] = os.path.dirname(file_path)
        # self.context["file_path"] = file_path
        # self.context["file_dir"] = self.dir_path

        self.origin_text = text
        self.modules = MdpGenerator.get_all_generators(text, self)

    def get_generated_content(self):
        s = ""
        for module in self.modules:
            try:
                s += module.get_entry()
            except Exception as e:
                logger.error(f"Error in module {module.command}: {e}")
                s += module.origin_text

        return s

    def write(self, file_path: str = None):
        if file_path is None:
            file_path = self.full_path

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.get_generated_content())



# class Document:
#     def __init__(self, file_path: str, context: dict[str, any] = None):
#         self.file_path = os.path.abspath(file_path)
#         self.file_dir = os.path.dirname(file_path)
        
#         text = ""
#         logger.info(f"Parsing {self.file_path}")
#         with open(file_path, "r", encoding="utf-8") as f:
#             text = f.read()

#         self.context = context if context is not None else dict()
#         if "root" not in self.context:
#             self.context["root"] = os.path.dirname(file_path)
#         self.context["file_path"] = file_path
#         self.context["file_dir"] = self.file_dir


#         # TODO: Parse meta info from the document

            
#         self.origin_text = text
#         self.modules = MdpGenerator.get_all_modules(text, self.context)

#     def get_generated_content(self):
#         s = ""
#         for module in self.modules:
#             try:
#                 s += module.get_entry()
#             except Exception as e:
#                 logger.error(f"Error in module {module.command}: {e}")
#                 s += module.origin_text

#         return s

#     def write(self, file_path: str = None):
#         if file_path is None:
#             file_path = self.file_path

#         with open(file_path, "w", encoding="utf-8") as f:
#             f.write(self.get_generated_content())
