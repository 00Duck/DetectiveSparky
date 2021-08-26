# DetectiveSparky
A command line tool to assist ServiceNow developers with finding code in one or more ServiceNow instances.

Sparky is able to query every table that contains a script, HTML, or XML field. In additional, workflows can be queried by name and will return any published activities whose associated script fields contain the value queried.

Custom files can also be used (see Querying below) to narrow down the selection of table/fields to query for each type.

## Installation
Download the latest .tar.gz or .whl file from the Release section of Github.

Navigate to the location where the file was downloaded and run the following command:
```
pip3 install DetectiveSparky-<version>-py3-none-any.whl
```
After installation, you may see an error message similar to this:

`WARNING: The script sparky is installed in '/Users/blake/Library/Python/3.8/bin' which is not on PATH.`

In order for the `sparky` command to work, you must add your (not mine) Python's bin folder to $PATH. Here's an example of how to do this:

```
export PATH=$PATH:/Users/blake/Library/Python/3.8/bin
```

Running this command in a terminal alone will not persist the change. For MacOS/Linux users, you can permanently add this location to PATH by updating your `.zshrc` or `.bashrc` file (located in your home folder).

## Usage
To make sure sparky is running correctly, you can type `sparky -h` and you should see a list of help options to get started. Here's a quick breakdown. Using -h or --help after each command is the best reference for what sparky is able to do.

### Profile
Example profile management:
```
sparky profile new
```
(enter details)

```
sparky profile list
```
```
sparky profile select
```
(select the profile you just created)

### Querying
By default, sparky will query all available tables for the type you select (script, HTML, XML). For workflows, currently only one workflow can be queried at a time.

```
sparky query script
```
```
sparky query html
```

For each query prompt, you will be asked to enter the corresponding details. Sparky will then check to ensure you are able to search against the corresponding records, then start the main scan.

Custom querying involves first creating a plain text file with the correct format (table_name,field_name). Example:
```
touch mycustomquery
```
```
nano mycustomquery
```
Enter the following details:
```
sys_script_include,script
sys_script,script
```
Save the file (if you are using nano, Ctrl + O, Enter, Ctrl + X) and then run the custom query:
```
sparky query script -f mycustomquery
```
(Enter string to search)

## Upgrading
Simply download the latest wheel and run `pip install DetectiveSparky-<version>-py3-none-any.whl`  

## Building from source/contributing
You have the option to manually download and build this project. To do so, first `git clone` this repository to your computer.

Navigate to the cloned location and type the following to start the virtual environment:
```
source bin/activate
```

Install sparky in the virtual environment in editable mode
```
pip install --editable .
```

Note that the sparky installed in the virtual environment is different (and uses a different database) than the sparky installed directly in python. However, keychains will be shared between sparky versions.

When you are ready to build the project, create a wheel and tar by running the following:
```
python -m build
```