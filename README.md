# RDFlib Fuse adapter

The goal of this tool is to expose the content of an RDF store as a filesystem hierarchy,
easily explorable and modifiable with standard tools (file browser, text editor).

It is usable with

* any RDF store supported by [RDFlib](http://rdflib.readthedocs.org/),
* any operating system supporting [Fuse](https://github.com/libfuse/libfuse).


## Features

- ☑ explore the graphs of the store in a folder hierarchy
- ☑ use your favourite syntax (with the `-F/--format` option)
- ☐ modify a graph by editing the corresponding file
- ☐ remove a graph by deleting the corresponding file
- ☐ creating a new graph in an existing directory
- ☐ creating new directories to create graphs with arbitrary graph names


## Install

You will need:

* Python (2 or 3);
* `libfuse`, including development files
(`apt-get install libfuse-dev` in Debian-based distributions);
* the dependencies in `requiperemnts.txt` (`pip install -r requirements.txt`).


## Run

`python rdffs.py {mount-point} -S {store-spec} [options]`

where `store-spec` has the form `:{store-plugin-name}:{config-string}`.

For a [Sleepycat](https://rdflib.readthedocs.io/en/stable/persistence.html) store,
the config string is a path,
and you can ommit the plugin name prefix, *e.g.*

`python rdfgs.py ~/my/mount/point -S ~/my/sleepycat/folder/`

**Warning**: Sleepycat stores created with Python2 are not compatible with Python3, and conversely.


## What are those `%` files and directories?

The special name `%` is used in place of an empty token,
when two slahes (`/`) follow each other in a graph name,
of the graph name ends with a slash.

For example, a graph named `http://example.com/` will appear under the path
`http:/%/example.com/%`.