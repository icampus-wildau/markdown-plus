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

    def __init__(
        self,
        file_path: str,
        workspace: Workspace,
        comment_definition: CommentDefinition = CommentDefinition.get_python_style(),
    ):
        """Initialize a new document in the workspace.

        Parameters
        ----------
        file_path : str
            The absolute path of the document.
        workspace : Workspace
            The parent workspace.
        comment_definition : CommentDefinition, optional
            The comment definition of the document, by default CommentDefinition.get_python_style()
        """

        self.full_path = os.path.abspath(file_path)
        """Absolute path of the document."""

        self.dir_path = os.path.dirname(file_path)
        """Directory path of the document."""

        self.file_name = os.path.basename(file_path)
        """File name of the document."""

        self.comment_definition = comment_definition
        """Comment definition of the document."""

        self.workspace = workspace
        """Parent workspace of the document."""

        # Store the document in the workspace
        workspace.document_map[file_path] = self

        # Check if the document is a readme
        self.is_readme = self.file_name.lower() in ["readme.md", "readme"]
        """True if the document is a readme file."""

        # logger.debug(f"Creating document {self.full_path} {self.file_name} {self.is_readme}")

        self.mdp_pattern = MdpBlock.get_pattern(comment_definition)
        """Pattern to find MDP blocks in the document."""

        self._args: dict[str, any] = None
        """MDP args of the document."""

    def get_title(self) -> str:
        """Get the title of the document."""

        if "title" in self.args:
            return self.args["title"]

        return None

    @property
    def args(self) -> dict[str, any]:
        if self._args is None:
            self._args = self.parse_args()
        return self._args

    def parse_args(self):
        """Parse the MDP arguments of the document."""

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
        if (match := self.mdp_pattern.search(block)) is not None:
            mdp_block = MdpBlock(match)
            mdp_block.arguments_str
            return mdp_block.arguments

        return {}

    def from_file(file_path: str, workspace: Workspace) -> Document:
        """Create a new document from a file.
        This method tries to automatically detect the file type and returns the correct document type.
        """
        ending = os.path.splitext(file_path)[1]
        if ending == ".md":
            return GeneratedDocument(file_path, workspace, CommentDefinition.get_markdown_style())

        if ending == ".py":
            return Document(file_path, workspace, CommentDefinition.get_python_style())

        return Document(file_path, workspace, CommentDefinition.get_cpp_style())


class GeneratedDocument(Document):
    def __init__(
        self,
        file_path: str,
        workspace: Workspace,
        comment_definition: CommentDefinition = CommentDefinition.get_python_style(),
    ):
        super().__init__(file_path, workspace, comment_definition)

        self.origin_text = None

    @property
    def skip_generating(self):
        flags = ["skip_generating", "skip", "ignore"]

        for flag in flags:
            if flag in self.args:
                return self.args[flag]

        return False

    def process(self):

        # If skip_generating is set, we do not generate the document
        if self.skip_generating:
            logger.info(f"Skipping document: {self.full_path}")
            return

        logger.info(f"Processing document: {self.full_path}")

        text = ""
        with open(self.full_path, "r", encoding="utf-8") as f:
            text = f.read()

        self.origin_text = text
        self.modules = MdpGenerator.get_all_generators(text, self)

        self.write()

    def get_generated_content(self):
        s = ""
        for module in self.modules:
            try:
                s += module.get_entry()
            except Exception as e:
                logger.error(f"Error in module {module.command}: {e}")
                s += module.origin_text
                # raise e

        return s

    def write(self, file_path: str = None):
        if file_path is None:
            file_path = self.full_path

        content = self.get_generated_content()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
