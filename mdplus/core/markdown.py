import logging
import os

from mdplus.core.modules import MdpModule


logger = logging.getLogger(__name__)


class Document:
    def __init__(self, file_path: str, context: dict[str, any] = None):
        self.file_path = os.path.abspath(file_path)
        self.file_dir = os.path.dirname(file_path)
        
        text = ""
        logger.info(f"Parsing {self.file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        self.context = context if context is not None else dict()
        if "root" not in self.context:
            self.context["root"] = os.path.dirname(file_path)
        self.context["file_path"] = file_path
        self.context["file_dir"] = self.file_dir
            
        self.origin_text = text
        self.modules = MdpModule.get_all_modules(text, self.context)

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
            file_path = self.file_path

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.get_generated_content())
