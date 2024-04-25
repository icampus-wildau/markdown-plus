from __future__ import annotations
import logging
import os

from mdplus.core.documents.document import Document, GeneratedDocument
from mdplus.core.environments.base import MdpEnvironment
from typing import Type, TypeVar

logger = logging.getLogger(__name__)


class Directory:
    """
    A directory containing documents.
    """

    def __init__(self, path: str, workspace: Workspace):
        """Initialize a new directory in the workspace.

        Parameters
        ----------
        path : str
            The absolute path of the directory.
        workspace : Workspace
            The parent workspace.
        """

        self.path = path
        """The absolute path of the directory."""

        self.dir_name = os.path.basename(path)
        """The name of the directory."""

        self.workspace = workspace
        """The parent workspace."""

        # Store the directory in the workspace
        workspace.directory_map[path] = self

        self.readme: Document | None = None
        """The readme document of the directory if existing."""

        self.directories: list[Directory] = list()
        """Subdirectories of the directory."""

        self.documents: list[Document] = list()
        """Documents in the directory."""

        # Parse the directory and create documents and subdirectories
        self._parse()

    def _parse(self):
        """Parse the directory and create documents and subdirectories."""

        logger.debug(f"Parsing directory {self.path}")

        self.directories.clear()
        self.documents.clear()

        for file in os.listdir(self.path):

            # We ignore hidden files and directories
            if file.startswith("."):  # or file.startswith("_"):
                continue

            file_path = os.path.join(self.path, file)

            if os.path.isdir(file_path):
                # Check, if the dir has a MDP_IGNORE file and should be ignored
                if os.path.isfile(os.path.join(file_path, "MDP_IGNORE")):
                    logger.debug(f"Ignoring {file_path} because of MDP_IGNORE file")
                    continue

                self.directories.append(Directory(file_path, self.workspace))
            else:
                doc: Document = Document.from_file(file_path, self.workspace)
                self.documents.append(doc)
                if isinstance(doc, GeneratedDocument):
                    self.workspace.generated_documents.append(doc)

                if doc.is_readme:
                    self.readme = doc


T = TypeVar("T", bound=MdpEnvironment)


class Workspace:
    """
    The workspace containing all markdown plus files.
    """

    def __init__(self, root: str):
        """Initialize a new workspace.

        Parameters
        ----------
        root : str
            Root path of the workspace.
        """

        self.is_pre_commit_hook = False

        self.root_path = root
        """The root path of the workspace."""

        self.environments: dict[str, MdpEnvironment] = dict()
        """
        The environments of the workspace.
        You can retreive an environment by calling `get_environment(env_name, YourMdpEnvironmentClass)`.
        """

        self.directory_map: dict[str, Directory] = dict()
        """Map of all directories and their paths as keys."""

        self.document_map: dict[str, Document] = dict()
        """Map of all documents and their paths as keys."""

        self.generated_documents: list[GeneratedDocument] = list()
        """List of all generated documents in the workspace."""

        self.root_dir = Directory(root, self)
        """The root directory object of the workspace."""

        self.top_level_readme: Document | None = self.root_dir.readme
        """The top level readme document of the workspace."""

        if logging.DEBUG >= logging.root.level:
            for doc in self.generated_documents:
                logger.debug(f"Found generatable document: {doc.full_path}")
                if len(doc.args) > 0:
                    logger.debug(f"\tArgs: {doc.args}")

    @property
    def documents(self):
        """All documents in the workspace."""
        return self.document_map.values()

    def get_environment(self, name: str, env_class: Type[T] = MdpEnvironment) -> T:
        """Get an environment by name. If the environment does not exist, it will be created.

        Parameters
        ----------
        name : str
            The name of the environment.
        env_class : Type[T], optional
            The class of the environment, so that your return type fits your desired class, by default MdpEnvironment

        Returns
        -------
        T
            The environment.
        """
        if name not in self.environments:
            self.environments[name] = env_class(self, name)
        return self.environments[name]

    def process(self, check_for_new_content: bool = False):
        """Process all documents in the workspace.

        Parameters
        ----------
        check_for_new_content : bool, optional
            If True, the workspace will check for new content in the written documents before writing them, by default False.
        """

        for doc in self.generated_documents:
            doc.process(check_for_new_content)
