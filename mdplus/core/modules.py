from __future__ import annotations
import logging

import ast
import importlib
import importlib.util
import re
from types import ModuleType

"""
# MD+:generate.install()

<!-- 
MD+:generate.installation
- header: "# Installation"
- ...
 -->
# Installation

<!-- MD+FIN:generate.installation -->
"""

logger = logging.getLogger(__name__)

class ModuleImporter:
    modules: dict[str, ModuleType] = {}
    
    @staticmethod
    def get_module(command: str) -> MdpModule | None:
        
        if command not in ModuleImporter.modules:
            module_name = f"mdplus.modules.{command}"
            spec = importlib.util.find_spec(module_name)
            if spec is not None:
                logger.debug("Importing module %s", module_name)
                ModuleImporter.modules[command] = importlib.import_module(module_name)

            else:
                logger.warning("Module %s not found", module_name)
                ModuleImporter.modules[command] = None

        cmd_module = ModuleImporter.modules[command]
        if cmd_module is not None:
            # print(cmd_module)
            
            if not hasattr(cmd_module, "module"):
                logger.error(
                    "Module %s is a package or does not have defined `module = MyModuleClass`!",
                    cmd_module
                )
                return None
            
            return cmd_module.module
            
            # if not hasattr(cmd_module, "main") or not callable(
            #     cmd_module.main
            # ):
            #     logger.error(
            #         "Module %s is a package or does not have a main() function. Call with package.module!",
            #         cmd_module
            #     )
            #     continue
            
            # return cmd_module.main
            
        return None


class MdpModule:
    PATTERN = re.compile(r"<!--[\s\n]*?MD\+:([^\s\n-]*)(.*?)-->", re.MULTILINE | re.DOTALL)
    """
    The regex pattern for the start tag of a module.
    Group 1: command
    Group 2: arguments
    """
    
    COMMANDS = []
    def __init__(self, command: str, arguments: dict[str, any]):
        self.command = command
        self.arguments = arguments
        self.origin_text = ""
        
        self.root = self.get_arg("root", None)
        self.file_path = self.get_arg("file_dir", None)
        self.file_dir = self.get_arg("file_dir", None)        
        
        self.end_tag = f"<!-- MD+FIN:{command} -->"
        
        self.arg_header = self.get_arg("header", None)
        self.header_level = 0
    
    def is_applicable(self) -> bool:
        """Check if the module is applicable to the current context.

        Returns
        -------
        bool
            True if the module is applicable, False otherwise.
        """
        return True
    
    def get_arg(self, name: str, default=None):
        """Get the value of an argument by name"""
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
        all_args_keys = [key for key in self.__dict__.keys() if key.startswith("arg_") and not callable(getattr(self, key))]
        arg_dict = {key[4:]: getattr(self, key) for key in all_args_keys}
        
        # Get the string representation of all arguments
        for key, value in arg_dict.items():
            args_string += f"{key} = {repr(value)}\n"
        return args_string
    
    def get_start_tag(self) -> str:
        """Get the start tag of the module, containing the command and arguments.

        Returns
        -------
        str
            Start tag of the module.
        """
        args_string = self.get_args_string()
        s = f"<!-- MD+:{self.command} "
        if args_string != "":
            s += "\n" + args_string
        s += "-->"
        return s
    
    def get_entry(self) -> str:
        """Get the entry of the module, containing the start and end tag.

        Returns
        -------
        str
            The entry of the module.
        """
        logger.info("Generating entry for %s", self.command)
        return "\n".join([self.get_start_tag(), self.get_content(), self.end_tag])
    
    def get_content(self) -> str:
        """Generate the content of the module.

        Returns
        -------
        str
            The content of the module.
        """
        raise NotImplementedError(f"Method get_content() not implemented for {self.__class__.__name__}")
        
    @staticmethod
    def parse_arguments(arguments: str) -> dict[str, str]:
        """Parse the arguments of the module from the string representation.

        Parameters
        ----------
        arguments : str
            The string representation of the arguments in the markdown text.

        Returns
        -------
        dict[str, str]
            Dictionary containing the arguments.
        """
        
        if arguments.strip() == "":
            return {}

        # Remove leading and trailing whitespaces from lines based on intend on the first line
        lines = arguments.split("\n")
        first_none_empty_line = next((i for i, line in enumerate(lines) if line.strip() != ""), None)
        first_none_empty_line = lines[first_none_empty_line] if first_none_empty_line is not None else None
        if first_none_empty_line is not None:
            intend = len(first_none_empty_line) - len(first_none_empty_line.lstrip())
            lines = [line[intend:] for line in lines]
            arguments = "\n".join(lines)
        # print(arguments)
            
        parsed_dict = {}
        parsed_ast = ast.parse(arguments)

        global_vars = {}

        for node in parsed_ast.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        var_value = node.value

                        # Evaluate the expression if it's not a simple value assignment
                        if isinstance(var_value, ast.Expr):
                            var_value = ast.literal_eval(var_value.value)
                        else:
                            try:
                                var_value = eval(compile(ast.Expression(var_value), '', 'eval'), global_vars, parsed_dict)
                            except Exception as _:   
                                string_of_expression = ast.get_source_segment(arguments, node.value)
                                logger.error("Error evaluating expression '%s'", string_of_expression)
                                var_value = None
                        parsed_dict[var_name] = var_value
                    else:
                        logger.warning("Unsupported target type %s", target)
            else:
                logger.warning("Unsupported node type %s", node)
        return parsed_dict
            
    def get_fin_pattern(self):
        """Get the regex pattern for the end tag of the module

        Returns
        -------
        re.Pattern
            The regex pattern for the end tag
        """
        regex = r"<!--[\s\n]*?MD\+FIN:" + self.command + r"[\s\n]*?-->"
        return re.compile(regex, re.MULTILINE | re.DOTALL)
        
        
    @staticmethod
    def get_all_modules(text: str, context: dict[str, any] = None) -> list[MdpModule]:
        """Get all modules from the markdown text.
        The modules list contains non-changing modules for text that is not part of a MDP module.

        Parameters
        ----------
        text : str
            The markdown text.

        Returns
        -------
        list[MdpModule]
            The list of modules.
        """
        modules: list[MdpModule] = []
                
        start = 0
        while True:
            match = MdpModule.PATTERN.search(text, start)
            if match is None:
                # Add final NoChangeModule
                if start < len(text):
                    modules.append(NoChangeModule(text[start:]))
                break
            
            command = match.group(1)
            arguments = match.group(2)
            
            module_cls = ModuleImporter.get_module(command)
            
            if module_cls is not None:
                # Add NoChangeModule for text before the command
                if start < match.start():
                    modules.append(NoChangeModule(text[start:match.start()]))
                
                # Add module defined by the command
                
                arguments = MdpModule.parse_arguments(arguments)
                arguments.update(context)
                module: MdpModule = module_cls(command, arguments)
                module.origin_text = text[match.start():match.end()]
                modules.append(module)
                
                # Find end tag for that module and continue search
                start = match.end()
                end_pattern = module.get_fin_pattern()
                match = end_pattern.search(text, start)
                if match is None:
                    logger.warning(f"End tag for {command} not found")
                else:
                    start = match.end()
            else:
                modules.append(NoChangeModule(text[start:match.end()]))
                start = match.end()
        
        return modules
        
    
class NoChangeModule(MdpModule):
    """Module that does not change the text. Used for parts between mdp modules."""
    def __init__(self, text: str):
        """Initialize the NoChangeModule

        Parameters
        ----------
        text : str
            The normal markdown text.
        """
        super().__init__("nochange", {})
        self.text = text
        
    def get_content(self) -> str:
        return self.text
        
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
    
    modules = MdpModule.get_all_modules(text)
    print(modules)
    
    for module in modules:
        print(module.get_entry())