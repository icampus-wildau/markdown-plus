# Markdown Plus

Markdown / README Generator with advanced features like including files, generate tables etc.

# Table of Contents

[[_TOC_]]

# Installation

## From Git repository

```bash
git clone https://icampusnet.th-wildau.de/ros-e/software/infrastructure/markdown-plus
cd markdown-plus

# Install the package
pip install .
# or editable in development mode
pip install -e .
```


# How to use

## Initialize a project

```bash
cd ~/your/project/directory
mdplus init . # Creates the _README.md and some other files from which the README.md is generated. 
```

## Parsing

The main feature of MDPlus is to parse the `_README.md` file of a directory and generate the corresponding `README.md` file by process the MDPlus Features.


```bash
cd ~/your/project/directory
# Parse the ~/your/project/directory/_README.md file and generate a ~/your/project/directory/README.md file
mdplus parse .
```

# Features in Markdown Plus

MDPlus commands always have a first unnamed argument that specifies the root path for the command (often just `"./"`) or the path to a file.

Furthermore, there can be named arguments after that. E.g.:
* `#MD+:snippet.installation("./", header="# Installation instruction\n\n")`

## Snippets

### `#MD+:snippet.installation("./")` - installation instructions

Adds installation instructions for:
* Installation from git
* Installation as Pakk package

**Arguments:**
* `header`-argument: set the header text of the snippet, defaults to `"# Installation\n\n"`

**Usage examples:**
* `#MD+:snippet.installation("./")`
* `#MD+:snippet.installation("./", header="# Installation instruction\n\n")`

### `#MD+:snippet.content("./")` - Content table of the repo

Adds an overview table of the content of the repo in the following way:
* Each directory in the repo gets an entry in the table, containing:
  * the directory name with a link to the directory
  * a short content description of the directory
* The short content description is generated from:
  * If a README.md is present in the directory, the **first non-header** line is taken as description.
  * If no README.md is present, the directory name is taken as description. 
* If you want to exclude a directory from the table, add an empty `MDP_IGNORE` file to the directory.  

**Arguments:**
* `header`-argument: set the header text of the snippet, defaults to `"# Content\n\n"`

**Usage examples:**
* `#MD+:snippet.content("./")`
* `#MD+:snippet.content("./", header="# Content table\n\n")`

**Converts to (example):**

| Dir                                          | Content                                                        |
| -------------------------------------------- | -------------------------------------------------------------- |
| [`docs`](docs)                               | Documentation                                                  |
| [`message_bridge_msgs`](message_bridge_msgs) | Package containing all message bridge msg and srv definitions. |
| [`message_bridge`](message_bridge)           | Python package containing all message bridge nodes.            |


## Including of files

### `#MD+:include.md("./path/to/file.md")` - Including of another Markdown file 

This snippet just includes another Markdown file into the generated Markdown file.
This allows you to split up your documentation into separate files.

**Options for the included file**
* `<!-- #MD+flag:IGNORE_INCLUDE -->`: This flag can be added somewhere to the 
  included markdown file to ignore everything after this flag.

**Usage examples:**
* `#MD+:include.md("./path/to/file.md")`


### `#MD+:include.example("./path/to/example/file.py")` - Including of an example

This snippet includes an example from the given file into the generated Markdown file.
The command can be used inline, in which case the header for the included file is not taken from the source file but instead from the text before the command.

**Currently supported file types**:
* Python `.py` files

**Behavior of the included example file**:
* The code of the example file is structured by multi-line-comments (`""" ... """`). The content of the comments is taken as text description for the following code, which is included as code block.
* Inside the code block you can use `#` to structure the comments by header levels. They get automatically converted to the correct header level in the generated Markdown file.
* The first multi-line-comment, more precisely the first line of it, is taken as header for the included example.

**Options for the included example file**
* `#MD+flag:IGNORE:LINE`: Add this flag at the end of the line to ignore the line.
* `#MD+flag:IGNORE:START` and `#MD+flag:IGNORE:END`: Everything between those two flags is ignored.
* `#MD+flag:IGNORE:START` (without END flag): Everything after this flag is ignored.

**Usage examples:**
* `#MD+:include.example("./path/to/example/file.py")`
* `# Take this header for the included example #MD+:include.example("./path/to/example/file.py")`


### `#MD+:include.examples("./path/to/example/dir/")` - Including of an example directory

This snippet includes examples from the given sub directory into the generated Markdown file.

See [#MD+:include.example](#mdincludeexamplepathtoexamplefilepy-including-of-an-example) for further information about the single example files.

**Configuration of the included example files**

You can configure the behavior of the included example files by adding a `mdplus.json` file to the sub directory.
In this file you can define the following:

```json
{
    ...
    "examples": {
        "order": [
            "first_file_to_be_included.py",
            "second_file_to_be_included.py",
            ...
        ],
        // if true, all files not listed in the order list are ignored
        "ignoreUnlisted": false, 
        "ignore": [
            "file_to_be_ignored.py",
            ...
        ]
    },
    ...
}
```

**Usage examples:**
* `#MD+:include.examples("./path/to/example/dir/")`

## ROS Commands

MDPlus commands starting with `ros.` are for ROS-packages.

### `#MD+:ros.complete("./")` - Complete ROS section

This command combines the following ROS commands:
* Overview of launch scripts
* Overview of ROS nodes
* Overview of message and service types

See the following topics for more information.

**Arguments:**
* `header`-argument: set the header text of the snippet, defaults to `"# ROS Information\n\n"`

### `#MD+:ros.launchs("./")` - Overview of launch scripts

Creates a table with all launch scripts in the ROS package, including:
* the name of the script
* the path to the related python script
* short description, what the script does
  * the information is taken from the first line in the docstring unter the `def generate_launch_description():` line in your launch script.

Example of a launch script:
```python
def generate_launch_description():
    """This line will show up in the launch script table"""

    ...

```

**Converts to (example):**

```
| Name    | Info      | Script                                  |
| ------- | --------- | --------------------------------------- |
| launch1 | Launch 2. | [node1.py](./path/to/launch1.launch.py) |
| launch2 | Launch 1. | [node2.py](./path/to/launch2.launch.py) |
```


### `#MD+:ros.nodes("./")` - Overview of ROS nodes

Creates a table with all nodes in the ROS package, including:
* the name of the node
* the path to the related python script
* short description, what the node is for
  * the information is taken from the first line in the docstring unter the `class MyNode(Node):` ROS-node class definition in your node script.

Example of a ROS node:
```python
import rclpy
from rclpy.node import Node

class MyNode(Node):
    """This line will show up in the ROS node table"""

    ...
```

**Converts to (example):**

```
| Name  | Info    | Script                         |
| ----- | ------- | ------------------------------ |
| node1 | Node 2. | [node1.py](./path/to/node1.py) |
| node2 | Node 1. | [node2.py](./path/to/node2.py) |
```

### `#MD+:ros.msgs("./")` - Overview of the message and service types

Creates a subsection describing all message types in the ROS package, including:
* a table as overview
* each message / service type with the message type definition

The overview table includes the following information:
* the name of the message / service type
* whether the type is a message or a service type
* the root package of the type

After the table, the message type definitions are taken from the source files and added to the section.

**Converts to (example):**

```md
## ROS Messages and services

|         Name        |  Type |      Package      |
|---------------------|-------|-------------------|
|[`JsonMsg`](#jsonmsg)|Message|message_bridge_msgs|
|[`JsonSrv`](#jsonsrv)|Service|message_bridge_msgs|

### Message definitions of message_bridge_msgs

#### [`JsonMsg`](./message_bridge_msgs/msg/JsonMsg.msg)

```python
string topic
string type
string data
´´´

```
