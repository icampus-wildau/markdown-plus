from __future__ import annotations
import logging

from mdplus.core.importer import ModuleImporter
from mdplus.core.documents.document import MdpBlock

from abc import ABC, abstractmethod

from typing import TYPE_CHECKING

from mdplus.util.markdown import adapt_header_level
from overrides import overrides

if TYPE_CHECKING:
    from mdplus.core.documents.document import Document

logger = logging.getLogger(__name__)


class MdpGenerator(ABC):
    """
    Base class for all markdown-plus generators.
    Override the get_content() method to generate the content of the generator.

    The generators are importet dynamically from the generators package.
    E.g. to create a generator for the command "mygroup.mycommand", create a file mdplus.generators.mygroup.mycommand and define a class MyCommand(MdpGenerator).
    Important: To make the file findable, define a module variable `module = MyCommand` referencing your class in the file.
    This module can be called in the markdown text with the command:
    <!-- MD+:mygroup.mycommand
    arg1 = ...
    arg2 = ...
    -->

    To define arguments for the generator, use the following syntax in your class:
    self.arg_arg1 = self.get_arg("arg1", default_value)
    self.arg_arg2 = self.get_arg("arg2", default_value)
    ...

    Every class member starting with "arg_" is considered an argument and will be automatically generated in the start tag of your generator definition.
    """

    IGNORED_COMMANDS = ["META", "TODO", "TODO:"]
    """Commands that are ignored and thus not recognized as generators."""

    def __init__(self, document: Document, mdpBlock: MdpBlock | None):
        """Initialize a new MdpGenerator

        Parameters
        ----------
        document : Document
            The parent document containing the generator.
        mdpBlock : MdpBlock | None
            The mdp block defining the generator.
        """

        self.document = document
        """The parent document of the generator."""
        self.workspace = document.workspace
        """The workspace of the parent document."""

        self.command = mdpBlock.command if mdpBlock is not None else ""
        """The command of the generator."""

        self.arguments = mdpBlock.arguments if mdpBlock is not None else {}
        """The arguments of the generator."""

        self.origin_text = ""
        """The text inside the generator before the new generation."""

        self.fin_pattern = (
            mdpBlock.get_fin_pattern(self.command, document.comment_definition) if mdpBlock is not None else None
        )
        """The pattern to find the end tag of the generator."""

        self.arg_header = self.get_arg("header", None)
        """The header of the generated text."""
        self.arg_level = self.get_arg("level", 1)
        """The level of the generated text. 1 means, that all h1 headers keep h1, a level of 2 means, that every h1 header is converted to h2, etc."""

    @property
    def start_tag(self):
        """The start tag of the generator."""
        start = self.document.comment_definition.multi_line_start[0]
        end = self.document.comment_definition.multi_line_end[0]
        args_string = self.get_args_string()
        s = f"{start} MD+:{self.command} "
        if args_string != "":
            s += "\n" + args_string
        s += f"{end}"
        return s

    @property
    def end_tag(self):
        """The end tag of the generator."""
        start = self.document.comment_definition.multi_line_start[0]
        end = self.document.comment_definition.multi_line_end[0]
        return f"{start} MD+FIN:{self.command} {end}"

    def is_applicable(self) -> bool:
        """Check if the generator is applicable to the current context.

        Returns
        -------
        bool
            True if the generator is applicable, False otherwise.
        """
        return True

    def get_arg(self, name: str, default=None):
        """Get the value of an argument by name."""
        a = self.arguments.get(name, default)
        if a is None:
            return default

        return a

    def get_args_string(self) -> str:
        """Get the string representation of all arguments of the module

        Returns
        -------
        str
            The string representation of all arguments.
        """
        args_string = ""

        # Get all member of the current instance that start with "arg_" and are not callable
        all_args_keys = [
            key for key in self.__dict__.keys() if key.startswith("arg_") and not callable(getattr(self, key))
        ]
        arg_dict = {key[4:]: getattr(self, key) for key in all_args_keys}

        # Get the string representation of all arguments
        for key, value in arg_dict.items():
            args_string += f"{key} = {repr(value)}\n"
        return args_string

    def get_entry(self) -> str:
        """Get the entry of the module, containing the start and end tag.

        Returns
        -------
        str
            The entry of the module.
        """
        if not self.is_applicable():
            logger.warning("Module %s not applicable", self.command)
            return self.origin_text

        logger.info("Generating entry for %s", self.command)

        # Adapt the header level
        content = self.get_content()
        content = adapt_header_level(content, self.arg_level - 1)

        return "\n".join([self.start_tag, content, self.end_tag])

    @abstractmethod
    def get_content(self) -> str:
        """Generate the content of the module.

        Returns
        -------
        str
            The content of the module.
        """
        raise NotImplementedError(f"Method get_content() not implemented for {self.__class__.__name__}")

    @staticmethod
    def get_all_generators(text: str, document: Document) -> list[MdpGenerator]:
        """Get all generators from the markdown text.
        The generator list contains non-changing generators for text that is not part of a MDP module.

        Parameters
        ----------
        text : str
            The markdown text.

        Returns
        -------
        list[MdpGenerator]
            The list of generators.
        """
        modules: list[MdpGenerator] = []

        start = 0
        while True:
            match = document.mdp_pattern.search(text, start)
            if match is None:
                # Add final NoChangeModule
                if start < len(text):
                    modules.append(NoChangeModule(document, text[start:]))
                break

            # Get the mdp definition out of the regex match
            # and extract the command
            mdp_block = MdpBlock(match)
            command = mdp_block.command            

            if command.upper() in MdpGenerator.IGNORED_COMMANDS:
                module_cls = None
            else:
                module_cls = ModuleImporter.get_module(command)
                if ("IGNORE" in mdp_block.arguments) and (mdp_block.arguments["IGNORE"]):
                    module_cls = None

            if module_cls is not None:
                # Add NoChangeModule for text before the command
                if start < match.start():
                    modules.append(NoChangeModule(document, text[start : match.start()]))

                # Add module defined by the command
                module: MdpGenerator = module_cls(document, mdp_block)
                tag_start = match.start()
                tag_end = match.end()
                modules.append(module)

                # Find end tag for that module and continue search
                start = match.end()
                end_pattern = module.fin_pattern
                match = end_pattern.search(text, start)
                if match is None:
                    logger.warning(f"End tag for {command} not found")
                else:
                    tag_end = match.end()
                    start = match.end()
                module.origin_text = text[tag_start:tag_end]

            else:
                modules.append(NoChangeModule(document, text[start : match.end()]))
                start = match.end()

        return modules


class NoChangeModule(MdpGenerator):
    """Module that does not change the text. Used for parts between mdp modules."""

    def __init__(self, document: Document, text: str):
        """Initialize the NoChangeModule

        Parameters
        ----------
        text : str
            The normal markdown text.
        """
        super().__init__(document, None)
        self.text = text

    @overrides
    def get_content(self) -> str:
        return self.text

    @overrides
    def get_entry(self) -> str:
        return self.text


if __name__ == "__main__":
    text = """
Bla
<!-- MD+:generate.installation
header = "# Installation"
bla = 5
 -->
# Installation

Test Test Test

<!-- MD+FIN:generate.installation -->
Test
    """

    modules = MdpGenerator.get_all_generators(text)
    print(modules)

    for module in modules:
        print(module.get_entry())
