<!-- MD+:META
path = "README.md"
title = "Default README structure for GitHub projects."
-->

# Markdown Plus

**Markdown / README Generator with advanced features like including files, generate content tables etc.**

Markdowm Plus adds a syntax to markdown files that allows to generate content in place.
Use this tool to avoid unnecessary work writing your README files by generating the generatable stuff! 

# Getting Started 

Install mdplus with pip:

```bash
# from PyPi
pip install mdplus

# ... or from GitHub 
pip install git+https://github.com/icampus-wildau/markdown-plus.git
```

After the installation is completed, you can use *MD+ generators* in your markdown files.

To initialize a project with a mdplus template:
```bash
cd ~/your/project/
mdplus init 
```

In your `README.md` and other *.md* files, use various generators:
```markdown
# Your project

Example of the content generator:
<!-- MD+:generate.content 
IGNORE = True  # Just to avoid generation of this block in this getting started README
-->

...
```

Then, use the `mdplus` command to generate the content:
```bash
cd ~/your/project/
mdplus p
```

This will generate the content in place:
```markdown
# Your project

Example of the content generator:
<!-- MD+:generate.content 
header = '# Contents of this Repository'
level = 1
IGNORE = True  # Just to avoid generation of this block in this getting started README
-->
# Contents of this Repository

|      Dir     |            Content            |
|--------------|-------------------------------|
|[`docs`](docs)|The documentation for package. |
|[`foo`](foo)  |Some directory of your project.|
<!-- MD+FIN:generate.content -->
```


See the [Documentation](#documentation) section for more information.

# Features & Compatibility

Features of the project:
- **parse** markdown files and generate content in place
- initialize projects with **templates**

Future work:
- more generators

<!-- MD+:generate.content 
header = '# Contents of this Repository'
level = 1
-->
# Contents of this Repository

|        Dir       |            Content           |
|------------------|------------------------------|
|  [`docs`](docs)  |The documentation for package.|
|[`mdplus`](mdplus)|            mdplus            |
<!-- MD+FIN:generate.content -->

# Documentation

A more detailed documentation can be found at [`docs/README.md`](docs/README.md).

# Questions/Issues

If you encounter any problems or have any questions, please open an issue on [the GitHub repository](https://github.com/icampus-wildau/markdown-plus/issues).

# Contributing

Contributions to extend the functionality or to solve existing problems are welcome! Requirements for pull requests are:
- All code is tested
- Naming is consistent with project naming
- Commits are squashed and contain a clear commit message describing what functionality is added.

<!-- # Related Projects

Related projects:
-  -->

# License

This project is licensed under the Apache License 2.0. For details, please see the [LICENSE](LICENCE) file. By contributing to this project, you agree to abide by the terms and conditions of the Apache License 2.0.
