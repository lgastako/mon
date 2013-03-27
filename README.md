mon: Simple file change monitor
===============================

Introduction
------------

"mon" is a small and simple yet flexible python script for monitoring the filesystem
for changes and taking action on them.  For example, automatically running tests
when a python file changes.

Everything is driven by a Monfile.  A Monfile is a json file which describes what
files to watch and what to do when changes are detected.


Usage
-----

By default mon looks for a Monfile called Monfile.json in the current directory but
this can be overridden with the -c/--config command line options.

In addition the -q/--quiet option can be used to suppress the output from subprocesses.


Monfiles
--------

The simplest Monfile is:

    {
        "rules": {
            "hello.txt": "echo hello world"
        }
    }

This says watch the file hello.txt and if it changes, echo the string "hello world"
to the terminal.  Not very useful, but it's a start.

A more realistic example might be:

    {
        "rules": {
            "setup.py": "pip install -e .",
            "**/*.py": "py.test"
            "**/*.css": "minify.sh"
        }
    }

This Monfile defines three separate rules:
    1. If the "setup.py" script changes, re-install the dev version of the
       project using pip.
    2. If ANY python file changes, re-run the tests.
    3. If ANY css file changes, re-run the minification process.


(COMING SOON!)
You can reference the name of the changed file like so:

    {
        "rules": {
            "**/*": "echo '%(filename)s changed.'",
    }

