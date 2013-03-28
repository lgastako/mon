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


You can reference the name of the changed file like so:

    {
        "rules": {
            "**/*": "echo '%(filename)s changed.'",
    }


Advanced
--------

You can create named lists to DRY things up:

    {
        "names": {
            "@source_files": [
                "*.py",
                "*.html",
                "*.css",
                "*.js",
            ]
        },
        "rules": {
            "@source_files": "make"
        }
    }

(The strings are normal strings, and the @ has no special meaning but I use it for
 names in my Monfiles by convention to provide a visual cue you are looking at a
 name).

The above has the same effect as this:

    {
        "rules": {
            "*.py": "make",
            "*.html": "make",
            "*.css": "make",
            "*.js": "make"
        }
    }

The latter is actually more terse and readable, but if you decide that instead of
using make you are going to use cmake, now you have to change 4 spots instead of
one.

In this case we're essentially using the names mechanism to have lists as keys
but the name substituion works in actions too, eg:

    {
        "names": {
            "@build_cmds": [
                "make clean",
                "make all",
                "make install",
            ]
        },
        "rules": {
            "*.c": "@build_cmds"
        }
    }

which is equivalent to this:

    {
        "rules": {
            "*.c": ["make clean",
                    "make all",
                    "make install"]
        }
    }

And of course you could use a named list on both the left and
right side so you would end up with the cross product of the two
list mapped as pattern/actions.

This notation is more useful in larger more complex Monfiles.

