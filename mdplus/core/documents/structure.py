from __future__ import annotations
import logging
import os

from mdplus.core.documents.document import Document, GeneratedDocument

logger = logging.getLogger(__name__)

class Directory:
    """
    A directory containing documents.
    """

    def __init__(self, path: str, workspace: Workspace):
        self.path = path
        self.workspace = workspace

        workspace.directory_map[path] = self

        self.readme: Document = None

        self.directories: list[Directory] = list()
        self.documents: list[Document] = list()
    
        # Parse the directory and create documents and subdirectories
        self._parse()

    def _parse(self):
        logger.debug(f"Parsing directory {self.path}")

        self.directories.clear()
        self.documents.clear()

        for file in os.listdir(self.path):
            if file.startswith("."): # or file.startswith("_"):
                continue

            file_path = os.path.join(self.path, file)

            if os.path.isdir(file_path):
                # Check, if the dir has a MDP_IGNORE file
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


    


class Workspace:
    """
    The workspace containing all markdown plus files.
    """

    def __init__(self, root: str):
        self.root_path = root

        self.directory_map: dict[str, Directory] = dict()
        self.document_map: dict[str, Document] = dict()

        self.generated_documents: list[GeneratedDocument] = list()

        self.root_dir = Directory(root, self)

        if logging.DEBUG >= logging.root.level:
            for doc in self.generated_documents:
                logger.debug(f"Found generatable document: {doc.full_path}")
                if len(doc.args) > 0:
                    logger.debug(f"\tArgs: {doc.args}")

    def process(self):
        for doc in self.generated_documents:
            doc.process()
        

