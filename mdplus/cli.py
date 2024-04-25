from __future__ import annotations

from datetime import datetime
import logging
import os

import click
from click_aliases import ClickAliasedGroup
from mdplus.core.documents.structure import Workspace
from rich.logging import RichHandler

logger = logging.getLogger("mdplus")
logger_initialized = False

modules = dict()

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"], max_content_width=800)


def setup_logger(**kwargs):
    global logger_initialized
    if kwargs.get("quiet"):
        logger.setLevel(logging.ERROR)
    elif kwargs.get("verbose"):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if logger_initialized:
        return

    logger_initialized = True
    if kwargs.get("verbose"):
        # FORMAT = "%(asctime)s - %(name)s - %(message)s"
        FORMAT = "%(asctime)s %(message)s"
    else:
        FORMAT = "%(message)s"

    # Set the format and handler for the logger
    handler = RichHandler()
    formatter = logging.Formatter(fmt=FORMAT, datefmt="[%X]")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


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
@click.option("--quiet", "-q", is_flag=True, help="Print less output.")
@click.option("--write-only-new-content", "-N", is_flag=True, help="Only write files with new content.")
@click.option("--is-pre-commit-hook", is_flag=True, help="Enables output for pre-commit hook.")
# @click.option("--recursive", "-r", is_flag=True, help="Parse all subdirectories.")
# @click.option("--root", "-R", help="Root directory parsing the repo.")
@click.argument(
    "root_dir",
    nargs=1,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=False,
)
def parse(root_dir, **kwargs):
    """
    Parse all markdown files in the given ROOT_DIR and generate markdown files with MD+ instructions replaced.
    If no ROOT_DIR is specified, the current working directory is used.
    """
    setup_logger(**kwargs)

    # print(root_dir, kwargs)
    # return

    root_dir = None
    # If no dirname is specified, use the current working directory
    if root_dir is None or len(root_dir) == 0:
        root_dir = os.getcwd()

    logger.debug(f"Starting parsing of {root_dir}")

    workspace = Workspace(root_dir)
    workspace.is_pre_commit_hook = kwargs.get("is_pre_commit_hook", False)
    workspace.process(kwargs.get("write_only_new_content", False))

    return 0


@execute.command(aliases=["i"])
@click.option("--verbose", "-v", is_flag=True, help="Print more output.")
@click.option("--overwrite", "-O", default=False, is_flag=True, help="Overwrites existing files.")
@click.option("--skip-existing", "-S", default=False, is_flag=True, help="Skip existing files.")
@click.option("--include-all", "-A", default=False, is_flag=True, help="Include all files without asking.")
@click.argument(
    "root_dir",
    nargs=1,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=False,
)
# @click.option(
#     "--overwrite", "-O", default=False, is_flag=True, help="Overwrites existing files."
# )
@click.pass_context
def init(ctx, root_dir, **kwargs):
    """Initialize the default MD Plus structure for the given ROOT_DIR."""
    setup_logger(**kwargs)

    if root_dir is None or len(root_dir) == 0:
        root_dir = os.getcwd()

    abs_path = os.path.abspath(root_dir)
    logger.info(f"Initialize mdplus project @ {abs_path}")

    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice
    from InquirerPy.separator import Separator

    # Get a list of all available templates

    template_dir = os.path.join(os.path.dirname(__file__), "templates")

    workspaces: list[Workspace] = list()
    # Parse all direct subdirectories of template_dir
    for file in os.listdir(template_dir):
        file_path = os.path.join(template_dir, file)
        if os.path.isdir(file_path):
            workspaces.append(Workspace(file_path))

    template_workspaces: dict[str, Workspace] = dict()

    for workspace in workspaces:
        if workspace.top_level_readme is not None:
            template_workspaces[workspace.root_dir.dir_name] = workspace
            logger.debug(f"Found template '{workspace.root_dir.dir_name}'")

    # Ask for the template to use
    # choices = [Choice(name, name) for name in template_workspaces.keys()],
    template_choices = []
    for name, ws in template_workspaces.items():
        key = name
        title = ws.top_level_readme.get_title()
        description = f"> {key} <: {title}" if title is not None else key
        c = Choice(key, description)
        template_choices.append(c)

    choices = [
        Separator(),
        *template_choices,
        Separator(),
    ]

    if len(template_choices) == 0:
        logger.error("No templates found")
        return

    if len(template_choices) == 1:
        answer = list(template_workspaces.keys())[0]
    else:
        answer = inquirer.select(
            message="Select a template for initializing the project:",
            choices=choices,
        ).execute()

    if answer is None:
        logger.error("No template selected")
        return

    selected_workspace = template_workspaces[answer]

    # Copy all documents to the target directory
    for doc in selected_workspace.documents:
        logger.debug(f"Processing {doc.file_name}")
        file_path = os.path.abspath(os.path.join(abs_path, doc.args["path"]))
        file_name = os.path.basename(file_path)

        if doc.file_name == "README.md" or kwargs.get("include_all"):
            proceed = True
        else:
            # Ask, if file should be included
            proceed = inquirer.confirm(
                message=f"Create {file_name} @ {file_path}?",
                long_instruction=doc.get_title(),
                default=True,
            ).execute()

        if not proceed:
            continue

        # Make dirs if not exists
        dir_path = os.path.dirname(file_path)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)

        # Check, if file already exists
        if os.path.isfile(file_path):
            if kwargs.get("overwrite"):
                logger.info(f"Overwriting {file_path}")

            else:
                if kwargs.get("skip_existing"):
                    continue

                proceed = inquirer.confirm(
                    message=f"File {file_name} already exists. Create backup before proceeding?",
                    default=False,
                ).execute()

                if not proceed:
                    continue

                # Create backup
                backup_path = f"{file_path}{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
                logger.info(f"Creating backup of {file_path} @ {backup_path}")
                os.rename(file_path, backup_path)

        logger.info(f"Writing {file_name} @ {file_path}")
        with open(file_path, "w") as f:
            with open(doc.full_path, "r") as template:
                for line in template:
                    f.write(line)

    # After template is initialized, ask if mdplus parse should be executed
    if inquirer.confirm("Do you want to parse the initialized template now?", default=True).execute():
        logger.info(f"Starting 'mdplus parse' for {abs_path}")
        ctx.invoke(parse, root_dir=abs_path, **kwargs)
        # parse(abs_path)

    logger.info("Initialization completed! :)")

    return
