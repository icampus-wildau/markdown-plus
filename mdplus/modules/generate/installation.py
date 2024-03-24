import os
import logging

import re
import git
import json

from mdplus.util.file_utils import join_relative_path
from mdplus.util.hooks import Hooks
from mdplus.core.modules import MdpModule

logger = logging.getLogger(__name__)


def clear_git_url(url: str):
    pattern = re.compile(r"oauth2?:.*?@")
    return pattern.sub("", url)

def create_git_instructions(git_repo_path: str, kwargs, header_level=2):
    hooks: Hooks = kwargs["hooks"]

    try:
        repo = git.Repo(git_repo_path)
        basename = os.path.basename(git_repo_path)

        # for remote in repo.remotes:
        #     print(f'- {remote.name} {remote.url}')

        lines = []
        lines.append(f"{'#' * header_level} Standalone from Git\n")
        hooks.append_to_content(__name__, "git", lines)

        lines.append("```bash")

        for i, remote in enumerate(repo.remotes):
            lines.append(f"# Clone repo from {remote.name}")
            lines.append(f"git clone {clear_git_url(remote.url)}")
            if i > 0:
                lines.append("# OR")

        lines.append("")

        # Check if install.sh exists and add install instructions
        if os.path.isfile(os.path.join(git_repo_path, "install.sh")):
            lines.append("# Install and setup")
            lines.append("sudo bash install.sh")
            lines.append("")

        # Check if requirements.txt exists and add install instructions
        if os.path.isfile(os.path.join(git_repo_path, "requirements.txt")):
            lines.append("# Install requirements")
            lines.append("pip install -r requirements.txt")
            lines.append("")

        # Check if is a python package
        if os.path.isfile(os.path.join(git_repo_path, "setup.py")):
            lines.append("# If this should be a standalone python package, install it in your system")
            lines.append(f"cd {basename}")
            lines.append("pip install .")
            lines.append("")

        if len(lines) > 0 and lines[-1] == "":
            lines.pop()
        lines.append("```")

        return "\n".join(lines)
    except git.exc.InvalidGitRepositoryError:
        return None


def create_rosepkg_instructions(rosepkg_path: str, kwargs, header_level=2):
    hooks: Hooks = kwargs["hooks"]

    # Check if module.rose.json exists
    if os.path.isfile(os.path.join(rosepkg_path, "module.rose.json")):
        with open(os.path.join(rosepkg_path, "module.rose.json"), "r") as f:
            module = json.load(f)
            if "id" in module:
                lines = []
                lines.append(f"{'#' * header_level} As rosepkg module\n")
                hooks.append_to_content(__name__, "rosepkg", lines)
                lines.append("```bash")
                lines.append("# Install with rosepkg")
                lines.append(f"rosepkg modules:install {module['id']}")
                lines.append("```")
                return "\n".join(lines)

    return None


def main(*args, **kwargs):
    """Creates installation instructions"""

    dir_path = args[0]
    root = kwargs["root"]
    hooks: Hooks = kwargs["hooks"]
    content = [kwargs.get("header", "# Installation")]
    hooks.append_to_content(__name__, "", content)

    dir_path = join_relative_path(root, dir_path)

    logger.info(f"Creating installation instruction for {dir_path}")

    # Check if directory exists
    if not os.path.isdir(dir_path):
        logger.error(f"Directory {dir_path} for creating installation instruction does not exist")
        return f"# {dir_path} NOT FOUND"

    instructions = [create_git_instructions(dir_path, kwargs, header_level=2),
                    create_rosepkg_instructions(dir_path, kwargs, header_level=2)]

    content.append("\n".join([i for i in instructions if i is not None]))

    return "\n\n".join(content)


class InstallationModule(MdpModule):

    def __init__(self, command: str, arguments: str):
        super().__init__(command, arguments)

    def get_content(self):
        return "INSTALL"


module = InstallationModule