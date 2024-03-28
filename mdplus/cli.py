from configparser import ConfigParser
import logging

import os
import re

import click
from click_aliases import ClickAliasedGroup

import importlib
import importlib.util
import importlib.resources

from mdplus.core.documents.structure import Workspace
from numpy import info

from mdplus.core.documents.document import Document

# from mdplus.logger import Logger
# from mdplus.util.hooks import Hooks
# from mdplus.util.parser.py_parser import get_args
# from mdplus.util.markdown import adapt_header_level

from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

logger = logging.getLogger(__name__)

modules = dict()

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"], max_content_width=800)


@click.group(cls=ClickAliasedGroup, context_settings=CONTEXT_SETTINGS)
def execute():
    pass


@execute.command(aliases=["c"])
def config():
    """Configure the MD Plus settings in the current project."""
    
    # GitHub / GitLab Flavored Markdown
    pass

@execute.command(aliases=["p"])
@click.option("--verbose", "-v", is_flag=True, help="Print more output.")
@click.option("--recursive", "-r", is_flag=True, help="Parse all subdirectories.")
@click.option("--root", "-R", help="Root directory parsing the repo.")
@click.argument(
    "files_or_dirs",
    nargs=-1,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=False,
)
def parse(files_or_dirs, **kwargs: str):
    """
    Parse the specified FILES OR DIRS and generate markdown files with MD+ instructions replaced.
    If no FILES OR DIRS are specified, all .md files in the current directory are parsed.
    """
    logger.setLevel(logging.DEBUG if kwargs.get("verbose") else logging.INFO)
    
    root = None
    # If no dirname is specified, use the current working directory
    if files_or_dirs is None or len(files_or_dirs) == 0:
        files_or_dirs = (os.getcwd(), )
    
    if len(files_or_dirs) == 1 and os.path.isdir(files_or_dirs[0]):
        root = files_or_dirs[0]
        
    if "root" in kwargs and kwargs["root"] is not None:
        root = os.path.abspath(kwargs["root"])
        
        
    logger.debug(f"Starting parsing of {files_or_dirs}")
    
    
    workspace = Workspace(root)
    workspace.process()

    return 
    # Find all fitting files in specified directories
    md_files = []
    recursive = kwargs.get("recursive")

    for file_or_dir in files_or_dirs:
        if os.path.isdir(file_or_dir):
            if recursive:
                for root_dir, dirs, files in os.walk(file_or_dir):
                    for file in files:
                        if file.endswith(".md"):
                            md_files.append(os.path.join(root_dir, file))
            else:
                for file in os.listdir(file_or_dir):
                    if file.endswith(".md"):
                        md_files.append(os.path.join(file_or_dir, file))
        else:
            md_files.append(file_or_dir)
    
    logger.debug(f"Files being parsed: {md_files}")
    # document = Document()

    for md_file in md_files:
        document = Document(md_file, {"root": root})
        document.write()

if __name__ == "__main__":
    parse(("C:/Users/schoc/Documents/iCampus Wildau/md/README.md", ))
