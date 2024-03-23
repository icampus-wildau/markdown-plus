import os
import logging

logger = logging.getLogger(__name__)


class HookText():
    def __init__(self, module: str, text: str):
        self.module = module

        text = text.strip()
        while text.startswith("\n"):
            text = text[1:]
        while text.endswith("\n"):
            text = text[:-1]

        self.text = text

    @staticmethod
    def get_from_file_content(file_content: str) -> dict[str, "HookText"]:
        hook_texts = {}
        current_hook = None
        current_text = ""
        for line in file_content.splitlines():
            if line.startswith("# "):
                if current_hook is not None:
                    hook_texts[current_hook] = HookText(current_hook, current_text)
                    current_text = ""

                current_hook = line[2:]
                continue
            else:
                current_text += line + "\n"

            if line.startswith("#"):
                logger.warning(f"Text for hooks should not include subheaders: {line}.")

        if current_hook is not None:
            hook_texts[current_hook] = HookText(current_hook, current_text)

        return hook_texts


class Hooks():
    def __init__(self, path: str):
        self.path = path
        self.file_content = ""
        self.hooks = {}

        self.load_hooks()

    def load_hooks(self):
        if os.path.isfile(self.path):
            with open(self.path, "r") as f:
                self.file_content = f.read()
                self.hooks = HookText.get_from_file_content(self.file_content)

    def __getitem__(self, item):
        return self.hooks[item]

    def append_to_content(self, module_name: str | list[str], part_name: str | list[str], content: list[str], index=None):
        if isinstance(module_name, str):
            module_name = [module_name]

        for mn in module_name:
            if isinstance(part_name, list):
                part_name = ".".join(part_name)
            name = f"{mn}.{part_name}" if len(part_name) > 0 else mn
            if name.startswith("mdplus.modules."):
                name = name[15:]

            if name in self.hooks:
                logger.info(f"Applying {name} hook.")
                t = f"{self.hooks[name].text}"
                if index is None:
                    content.append(t)
                else:
                    content.insert(index, t)

                break
