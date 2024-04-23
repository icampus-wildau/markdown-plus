<!-- MD+:META
title = "Develop of new Generators"
skip_generating = True
 -->
 
# Developing new Generators

Generators are the core of markdown-plus. 
They allow you to define the generation of parts of the markdown file. 

## How to develop new Generators

To create a new generator, you need the following:
- a class inheriting from `mdplus.core.generator.MdpGenerator`
- argument members for the generator
- an implementation of the `get_content` method returning the generated content as string

```python

class MyGenerator(MdpGenerator):
    def __init__(self, document: Document, mdpBlock: MdpBlock):
        """
        Each generator receives the document and the MD+ block it is defined in.
        
        Calling the super constructor allows you to access meta information about the file, where the generator is called:
        - the file path & the directory path
        - the arguments of the generator
        - the meta args of the document defined in `MD+:META`
        - the workspace 
        """
        super().__init__(document, mdpBlock)

        """
        To define arguments for the generator, add class members that:
        - begin with `arg_{name}` (thus, they will automatically be recognized as arguments)
        - are initialized with the `get_arg({name})` method, defining the default value
        """
        self.arg_header = self.get_arg("header", "# Header for this Repository")
        self.arg_arg1 = self.get_arg("arg1", True)
        self.arg_arg2 = self.get_arg("arg2", 5)

    def get_content(self) -> str:
        """
        Here you return the generated content of the generator.
        """

        return f"# {self.arg_header}\n\n" + \
               f"Arg1: {self.arg_arg1}\n" + \
               f"Arg2: {self.arg_arg2}\n"
```

