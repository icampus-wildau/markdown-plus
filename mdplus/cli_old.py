from configparser import ConfigParser
import logging

import os
import re

import click
from click_aliases import ClickAliasedGroup

import importlib
import importlib.util
import importlib.resources

# from mdplus.core import Replacement

from mdplus.logger import Logger

# from mdplus.util.hooks import Hooks
# from mdplus.util.parser.py_parser import get_args
# from mdplus.util.markdown import adapt_header_level

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
@click.argument(
    "dirname",
    nargs=1,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
    required=False,
)
@click.argument(
    "files",
    nargs=-1,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=False,
)
def parse(dirname, files, **kwargs: str):
    print("Parsing", dirname, files)


@execute.command(aliases=[])
@click.argument(
    "dirname",
    nargs=1,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
    required=False,
)
@click.argument(
    "files",
    nargs=-1,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=False,
)
# @click.option("-s", "--source", default="_README.md", help="Name of the parsed source file")
# @click.option("-o", "--output", default="README.md", help="Name of the output file")
@click.option("--verbose", "-v", is_flag=True, help="Print more output.")
def parse_old(dirname, files, **kwargs: str):
    """Parse the specified directory and generate a markdown file out of the source file."""
    Logger.setup_logger(logging.DEBUG if kwargs["verbose"] else logging.INFO)

    if dirname is None:
        dirname = os.getcwd()

    dirname = os.path.abspath(dirname)

    cfg = ConfigParser()
    # Check if there is a .mdplus.cfg file in the directory
    cfg_file = os.path.join(dirname, ".mdplus.cfg")
    if os.path.isfile(cfg_file):
        cfg.read(cfg_file)

    dirs = []

    for section in cfg.sections():
        if (in_dir := cfg.get(section, "in", fallback=None)) and (out_dir := cfg.get(section, "out", fallback=None)):
            logger.info(f"Found {section} cfg: in='{in_dir}', out='{out_dir}'")
            dirs.append(
                (
                    os.path.abspath(os.path.join(dirname, in_dir)),
                    os.path.abspath(os.path.join(dirname, out_dir)),
                )
            )

    if len(dirs) == 0:
        dirs.append((dirname, dirname))

    # If no files are specified, get all markdown files in the directory that are qualified for parsing:
    # - files starting with an underscore and end with .md
    # - files ending with mdp.md
    rules = [
        [lambda f: f.endswith(".md") and f.startswith("_"), lambda f: f[1:]],
        [lambda f: f.endswith("mdp.md"), lambda f: f[:-7] + ".md"],
    ]

    for in_dir, out_dir in dirs:
        if files is None or len(files) == 0:
            files = [f for f in os.listdir(in_dir) if any([r_check(f) for r_check, r_modify in rules])]

        logger.info(f"Parsing the following files in '{in_dir}':")
        files_str = "\n".join([f" - '{f}'" for f in files])
        logger.info(files_str)

        for source_file in files:
            abs_path = os.path.abspath(in_dir)
            file = os.path.join(abs_path, source_file)
            Logger.get_console().rule(title=f"Parse {file}")
            logger.info(f"Start parsing of '{file}'")

            hooks = Hooks(os.path.join(abs_path, "docs", "HOOKS.md"))

            # Check if file exists
            if not os.path.isfile(file):
                logger.error(f"File {file} does not exist")
                return
            else:
                # Pattern to search for #MD+:command(args) entries
                c = re.compile(r"(#+ )?#MD\+:((.*?)\(((.|[\n\s$^])*?)\))", re.MULTILINE)

                text = ""

                # Open file and search for MD-Plus entries
                with open(file, "r") as f:
                    text = f.read()

                    last_matched_position = 0
                    i = 0
                    # for match in c.finditer(text):
                    while True:
                        i += 1
                        match = c.search(text, last_matched_position)
                        if match is None:
                            break
                        print("")

                        logger.debug(f"FOUND: {match}")
                        start, end = match.span()
                        last_matched_position = start + 1

                        # Check whether the command appears at the start of the line or if it is inside a line
                        check_index = start - 1
                        while check_index >= 0 and text[check_index] != "\n":
                            check_index -= 1

                        inline = False
                        if check_index != start - 1:
                            inline = True

                        text_before_cmd = text[check_index + 1 : start]

                        logger.debug(f"Inline: {inline}")
                        logger.debug(f"Text before command: '{text_before_cmd}'")

                        if inline:
                            # If the command is inline, count the number of # in front of the command
                            header_level = text_before_cmd.count("#") - 1
                            text_before_cmd = text_before_cmd.strip("#").strip()
                        else:
                            header_level = (match.group(1).count("#") - 1) if match.group(1) else 0
                        fun_call = match.group(2)
                        command = match.group(3)

                        logger.debug(
                            f"Start: {start}, end: {end}, header_level: {header_level}, fun_call: {fun_call}, command: {command}"
                        )

                        if command not in modules:
                            module_name = f"mdplus.modules.{command}"
                            spec = importlib.util.find_spec(module_name)
                            if spec is not None:
                                logger.debug(f"Importing module {module_name}")
                                # modules[command] = __import__(module_name)
                                modules[command] = importlib.import_module(module_name)

                            else:
                                logger.warning(f"Module {module_name} not found")
                                modules[command] = None

                        cmd_module = modules[command]
                        if cmd_module is not None:
                            # print(cmd_module)
                            if not hasattr(cmd_module, "main") or not callable(cmd_module.main):
                                logger.error(
                                    f"Module {cmd_module} is a package or does not have a main() function. Call with package.module!"
                                )
                                continue

                            fun = getattr(cmd_module, "main")
                            args, _kwargs = get_args(fun_call)
                            _kwargs["root"] = abs_path
                            _kwargs["hooks"] = hooks
                            _kwargs["inline"] = inline
                            _kwargs["text_before_cmd"] = text_before_cmd

                            logger.debug(
                                f"Running {command} @ header {header_level} with args {args} and kwargs {_kwargs}"
                            )
                            replacement = fun(*args, **_kwargs)
                            if isinstance(replacement, str):
                                replacement = Replacement(replacement)
                            replacement.text = adapt_header_level(replacement.text, header_level)

                            # If the replacement replaces the text before the command, adapt the start index
                            if replacement.replaces_text_before_cmd:
                                start = check_index

                            # Replace match by fun result
                            text = text[:start] + replacement.text + text[end:]

                text += "\n\n Generated with [Markdown Plus](https://icampusnet.th-wildau.de/ros-e/software/infrastructure/markdown-plus)"

                output_fname = source_file

                for rule in rules:
                    if rule[0](source_file):
                        output_fname = rule[1](output_fname)

                outpath = os.path.abspath(os.path.join(out_dir, output_fname))

                # If in and out dir differ, we have to adapt the relative links
                if out_dir != in_dir:
                    # In_dir = ./docs
                    # [Der Code des Nodes](../src/hello_ros_py/hello_ros_py/simple_publisher.py)
                    # Out_dir = ./
                    # [Der Code des Nodes](./src/hello_ros_py/hello_ros_py/simple_publisher.py)

                    # In_dir = ./docs
                    # [Der Code des Nodes](../src/hello_ros_py/hello_ros_py/simple_publisher.py)
                    # Out_dir = ./docs/bla
                    # [Der Code des Nodes](../../src/hello_ros_py/hello_ros_py/simple_publisher.py)

                    link_pattern = re.compile(r"\[([^[\]]+)\]\(([^()]*)\)")

                    start_pos = 0
                    while match := link_pattern.search(text, pos=start_pos):
                        text_before, link = match.groups()
                        # Check if the link is relative
                        if link.startswith("http") or os.path.isabs(link):
                            start_pos = match.end()
                            continue

                        destination = os.path.abspath(os.path.join(in_dir, link))
                        new_link = os.path.join(".", os.path.relpath(destination, out_dir)).replace("\\", "/")
                        logger.debug(f"Transforming relative link:\n  {link} to\n  {new_link}")

                        text = text[: match.start(2)] + new_link + text[match.end(2) :]
                        start_pos = match.start(2) + len(new_link)

                # Write the file to the output
                logger.info(f"Writing output to {outpath}")
                with open(outpath, "w") as f:
                    f.write(text)


def get_template(name: str) -> str:
    splits = name.split("/")
    template = "mdplus.templates." + ".".join(splits[:-1])
    return importlib.resources.read_text(template, splits[-1])


@execute.command(aliases=["i"])
@click.argument("dirname")
@click.option("--overwrite", "-O", default=False, is_flag=True, help="Overwrites existing files.")
@click.option(
    "--with-examples",
    "-e",
    default=False,
    is_flag=True,
    help="Creates an examples directory.",
)
def init(dirname, overwrite, with_examples):
    """Initialize the default MD Plus structure for the given project."""

    abs_path = os.path.abspath(dirname)
    logger.info(f"Init mdplus project @ {abs_path}")

    # Add docs and examples directories if not exists
    dirs = ["docs"]
    if with_examples:
        dirs.append("examples")

    for d in dirs:
        dir_path = os.path.join(abs_path, d)
        if not os.path.isdir(dir_path):
            logger.info(f"Creating directory @ {dir_path}")
            os.mkdir(dir_path)

    files = [
        ("_README.md", "init/_README.md"),
        ("docs/AUTHORS.md", "init/docs/AUTHORS.md"),
    ]

    if with_examples:
        files.extend(
            [
                ("examples/example1.py", "init/examples/example1.py"),
                ("examples/mdplus.json", "init/examples/mdplus.json"),
            ]
        )

    for file_tuple in files:
        file, template = file_tuple

        source_file = os.path.join(abs_path, file)
        if overwrite or not os.path.isfile(source_file):
            logger.info(f"Creating {file} @ {source_file}")
            with open(source_file, "w") as f:
                f.write(get_template(template))

    # If there is already a README.md file, append the content to the _README.md file
    readme_file = os.path.join(abs_path, "README.md")
    if os.path.isfile(readme_file):
        logger.info(f"Appending README.md content to _README.md")
        with open(readme_file, "r") as f:
            readme_content = f.read()

        with open(os.path.join(abs_path, "_README.md"), "a") as f:
            f.write("\n\n---\n\n CONTENT OF OLD README FILE\n\n")
            f.write(readme_content)

    # If without examples, delete the examples command
    if not with_examples:
        with open(os.path.join(abs_path, "_README.md"), "r") as f:
            readme_content = f.read()

        readme_content = readme_content.replace('# #MD+:include.examples("./examples/")\n\n', "")

        with open(os.path.join(abs_path, "_README.md"), "w") as f:
            f.write(readme_content)


if __name__ == "__main__":
    parse()
