<!-- MD+:META
title = "How to use Generators"
skip_generating = True
 -->


# Generators in General

Generators can be placed anywhere in markdown files to define the generation of parts of the file.
Generators are defined by the following:
- A start tag, enclosed by multline-markdown comments `<!-- ... -->`, containing: 
    - The generator name `MD+:<generator_group>.<generator_name>`
    - A list of arguments for the generator below it. These arguments are defined in Python-like syntax.
- An end tag, also enclosed by multline-markdown comments `<!-- ... -->`, containing:
    - The generator name `MD+FIN:<generator_group>.<generator_name>`

For example, the content generator would be defined as follows:
```markdown
<!-- MD+:generate.content
header = '# Content Header'
level = 1 # The header level
dirs = True # Include dirs in the overview
md_files = True # Include markdown files in the overview
-->
... Here come the generated content
<!-- MD+FIN:generate.content -->
```

Everything outside the generator tags is not affected by the generator and will be copied to the output file as is.


Every generator has always at least the following arguments:
- `header = ''` - The header of the generated content.
- `level = 1` - The header level of the headers in the generated content. 2 means, that every "# Header" becomes "## Header", etc. 

> [!NOTE]
> You don't have to specify the arguments and the end tag the first time you include the generator. The generator will generate both, you can adjust the arguments afterwards.

# `generate` Generators

## `generate.getting_started.pakk` - Getting Started with Pakk

**Generates**:
- installation instructions with pakk
- usage instructions with pakk

**Usage examples**:
```markdown
<!-- MD+:generate.getting_started.pakk 
header = '# Getting Started using [pakk](https://github.com/iCampus-Wildau/pakk)'
level = 1
installation = True
usage = True
-->
# Getting Started using [pakk](https://github.com/iCampus-Wildau/pakk)
Using [pakk](https://github.com/iCampus-Wildau/pakk) package manager is recommended for automating the installation and management of ROS 2 packages.

Installation with pakk:
'''bash
pakk install ...
'''

After the installation completes, start the ... package:
'''bash
pakk start ...  # Run as a service until a reboot / manual stop, or ...
pakk enable ...  # ... start it now and on every system boot.  
'''
```
<!-- MD+FIN:generate.getting_started.pakk -->


## `generate.content` - Content overview

Generates an overview table of the content of the repo in the following way:
* Each directory in the repo gets an entry in the table, containing:
  * the directory name with a link to the directory
  * a short content description of the directory
* The short content description is generated from:
  * If a README.md is present in the directory:
    * if present, the `title` argument from `MD+:META` is taken as description.
    * if not, take the **first non-header** line as description.
  * If no README.md is present, the directory name is taken as description. 
* If you want to exclude a directory from the table, add an empty `MDP_IGNORE` file to the directory.  
* Optionally (if argument `md_files = True`), each markdown file in the directory gets an entry in the table, containing:
  * the file name with a link to the file.
  * the `title` argument from `MD+:META` as description.


**Usage Example**:
```markdown
# Your project

Example of the content generator:
<!-- MD+:generate.content 
header = '# Contents of this Repository'
level = 1
dirs = True
md_files = False
-->
# Contents of this Repository

|      Dir     |            Content            |
|--------------|-------------------------------|
|[`docs`](docs)|The documentation for package. |
|[`foo`](foo)  |Some directory of your project.|
<!-- MD+FIN:generate.content -->
```

# `include` Generators

## `include.example` - Include an example file

This generator includes an example from the given file into your markdown file.

**Currently supported file types**:
* Python `.py` files

**Behavior of the included example file**:
* The `title` of the `MD+:META` block is used as the header of the included example, if you set the generator header argument to `None`.
* The code of the example file is structured by multi-line-comments (`""" ... """`). The content of the comments is taken as text description for the following code, which is included as code block.
* Inside the code block you can use `#` to structure the comments by header levels. They get automatically converted to the correct header level in the generated Markdown file.

**Options for the included example file**:

Inside the included file, you can add the following flags to control the inclusion:
* `MD+flag:IGNORE:LINE`: Add this flag at the end of the line to ignore the line.
* `MD+flag:IGNORE:START` and `#MD+flag:IGNORE:END`: Everything between those two flags is ignored.
* `MD+flag:IGNORE:START` (without END flag): Everything after this flag is ignored.

**Usage Example**:

```markdown
<!-- MD+:include.example 
header = 'Basic Publishing Example'
level = 1
path = '../examples/publishing.py'
-->
# [Basic Publishing Example](../examples/publishing.py)
'''python
your code here
'''
```


<!-- MD+FIN:include.example -->

# `ros` Generators


## `ros.launchs` - 

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


## `ros.nodes` - 

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

## `ros.interfaces` - 


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
<!-- MD+:ros.interfaces 
header = '# ROS Interface Definitions'
level = 2
-->
## Message definitions of your_package

|         Name        |  Type |      Package      |
|---------------------|-------|-------------------|
|[`JsonMsg`](#jsonmsg)|Message|your_package|
|[`JsonSrv`](#jsonsrv)|Service|your_package|

### Message definitions of your_package

#### [`JsonMsg`](./your_package/msg/JsonMsg.msg)

'''python
string topic
string type
string data
'''
<!-- MD+FIN:ros.interfaces -->
```



# META Definition

