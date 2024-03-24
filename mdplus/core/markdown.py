import logging
import os

from mdplus.core.modules import MdpModule


logger = logging.getLogger(__name__)


class Document:
    def __init__(self, file_path: str):
        self.file_path = os.path.abspath(file_path)

        text = ""
        logger.info(f"Parsing {self.file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        self.context = {}
        self.context["root"] = os.path.dirname(file_path)

        self.origin_text = text
        self.modules = MdpModule.get_all_modules(text, self.context)

    def get_generated_content(self):
        s = ""
        for module in self.modules:
            s += module.get_entry()

        return s

    def write(self, file_path: str = None):
        if file_path is None:
            file_path = self.file_path

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.get_generated_content())
