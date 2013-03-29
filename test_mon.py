from functools import partial

import os
import time
import threading

from mon import parse_rules
from mon import execute_action
from mon import expand_names
from mon import first
from mon import Rule
from mon import PollingMonitor

from termcolor import colored

SC = partial(colored, color="green")
EC = partial(colored, color="red")

# TODO: Missing tests:
# - Removed file handling in PollingMonitor
# - Handling of - as stdin in config handling
# - WTF is all this gro ups stuff in parse_rules -- oops, fix.
# - Stopping a monitor
# - Supplying a string instead of a list of strings for rhs.
# - Embedding a name in a list on the rhs,
#   e.g. {rules: {"*.py": ["foo", "@name", "bar"]}}


class TestFirst:

    def test_first_none(self):
        assert first(None) == None

    def test_first_empty(self):
        assert first([]) == None

    def test_first_non_empty(self):
        assert first([1]) == 1
        assert first([1, 2]) == 1
        assert first([1, 2, 3]) == 1

        assert first([3]) == 3
        assert first([3, 2]) == 3
        assert first([3, 2, 1]) == 3


class TestExpandNames:

    rules = [
        Rule(["@lhs"], ["@rhs"])
    ]

    def test_empty_names_section(self):
        result = expand_names(self.rules, {})
        assert result == self.rules

    def test_no_matching_name(self):
        result = expand_names(self.rules, {})
        assert result == self.rules

    def test_lhs(self):
        result = expand_names(self.rules, {"@lhs": ["a", "b", "c"]})
        rule = result[0]
        assert len(result) == 3

        def rule_exists(lhs, rhs):
            for rule in result:
                if rule.patterns == [lhs] and rule.actions == [rhs]:
                    return True
            assert False, "Could not find rule with (lhs=%s, rhs=%s)" % (lhs, rhs)

        assert rule_exists("a", "@rhs")
        assert rule_exists("b", "@rhs")
        assert rule_exists("c", "@rhs")

    def test_rhs(self):
        result = expand_names(self.rules, {"@rhs": ["d", "e", "f"]})
        rule = result[0]
        assert len(result) == 1

        assert rule.patterns == ["@lhs"]
        assert rule.actions == ["d", "e", "f"]

    def test_both(self):
        # Really this should use a pattern list instead of splitting it out.
        # TODO: Fix
        expected_rhs = ["d", "e", "f"]
        result = expand_names(self.rules, {
            "@lhs": ["a", "b", "c"],
            "@rhs": expected_rhs
        })
        rule = result[0]
        assert len(result) == 3

        def rule_exists(lhs):
            for rule in result:
                if rule.patterns == [lhs] and rule.actions == expected_rhs:
                    return True
            assert False, "Could not find rule with (lhs=%s, rhs=%s)" % (lhs, rhs)

        assert rule_exists("a")
        assert rule_exists("b")
        assert rule_exists("c")


class TestParseRules:

    def test_zero(self):
        config = {"rules":{}}
        rules = parse_rules(config)
        assert rules == []

    def test_one_rule_one_action(self):
        test_pattern = "README.txt"
        test_action = "echo 'README updated!'"

        config = {"rules":{test_pattern: test_action}}
        rules = parse_rules(config)

        assert len(rules) == 1
        rule = rules[0]

        assert len(rule.patterns) == 1
        pattern = rule.patterns[0]
        assert pattern == test_pattern

        assert len(rule.actions) == 1
        action = rule.actions[0]
        assert action == test_action

    def test_one_rule_multiple_actions(self):
        test_pattern = "README.txt"
        test_actions = [
            "echo 'README updated!'",
            "echo 'I\\'m so exicted and I just can\\'t hide it!'"
        ]

        config={"rules":{test_pattern: test_actions}}
        rules = parse_rules(config)

        assert len(rules) == 1
        rule = rules[0]

        assert len(rule.patterns) == 1
        pattern = rule.patterns[0]
        assert pattern == test_pattern

        assert len(rule.actions) == 2
        assert rule.actions[0] == test_actions[0]
        assert rule.actions[1] == test_actions[1]

    def test_parse_rules(self):
        config = {
            "names": {
                "@source_files": [
                    "**/*.py",
                    "**/*.html",
                    "**/*.css",
                    "**/*.js",
                    "**/*.coffee"
                ]
            },
            "rules": {
                "@source_files": "echo 'source file changed'"
            },
        }
        rules = parse_rules(config)

        def rule_exists(pat):
            for rule in rules:
                if pat in rule.patterns:
                    return True

        assert len(rules) == 5
        assert rule_exists("**/*.py")
        assert rule_exists("**/*.html")
        assert rule_exists("**/*.css")
        assert rule_exists("**/*.js")
        assert rule_exists("**/*.coffee")


class TestExecuteAction:

    def test_execute_successful_action_not_quiet(self, capfd):
        execute_action("true", False)
        out, err = capfd.readouterr()
        C = SC
        expected = "\n".join([
            "Running action:  true",
            C("Result: status code 0"),
            C("-" * 78),
            C(""),
            C("-" * 78),
            ""
        ])
        assert out == expected

    def test_execute_successful_action_quiet(self, capfd):
        execute_action("true", True)
        out, err = capfd.readouterr()
        C = SC
        expected = ("Running action:  true\n" +
                    C("Result: status code 0") + "\n")
        assert out == expected

    def test_execute_error_action_not_quiet(self, capfd):
        execute_action("false", False)
        out, err = capfd.readouterr()
        C = EC
        expected = "\n".join([
            "Running action:  false",
            C("Result: status code 1"),
            C("-" * 78),
            C(""),
            C("-" * 78),
            ""
        ])
        out = out.encode("utf-8")
        assert out == expected


class TestRules:

    def test_can_reference_modified_filename_in_action(self, capfd):
        rule = Rule("*", ["echo 'file changed: %(filename)s'"])
        rule.execute_all(False, ["foo.txt"])

        out, err = capfd.readouterr()
        C = SC

        expected = "\n".join([
            "Running action:  echo 'file changed: foo.txt'",
            C("Result: status code 0"),
            C("-" * 78),
            C("file changed: foo.txt\n"),
            C("-" * 78),
            ""
        ])
        assert out == expected

    def test_can_reference_modified_filenames_in_action(self, capfd):
        rule = Rule("*", ["echo 'file changed: %(filenames)s'"])
        rule.execute_all(False, ["foo.txt", "bar.txt"])

        out, err = capfd.readouterr()
        C = SC

        expected = "\n".join([
            "Running action:  echo 'file changed: foo.txt bar.txt'",
            C("Result: status code 0"),
            C("-" * 78),
            C("file changed: foo.txt bar.txt\n"),
            C("-" * 78),
            ""
        ])
        assert out == expected

    def test_can_reference_modified_filename_list_in_action(self, capfd):
        rule = Rule("*", ["echo 'file changed: %(filename_list)s'"])
        rule.execute_all(False, ["foo.txt", "bar.txt"])

        out, err = capfd.readouterr()
        C = SC

        expected = "\n".join([
            "Running action:  echo 'file changed: foo.txt, bar.txt'",
            C("Result: status code 0"),
            C("-" * 78),
            C("file changed: foo.txt, bar.txt\n"),
            C("-" * 78),
            ""
        ])
        assert out == expected


class TestPollingMonitor:

    default_fn = "foo.ttt"

    def setup_method(self, method):
        self.thread = None
        self.calls = 0

    def make_monitor(self, tmpdir, quiet=False):
        pattern = os.path.join(str(tmpdir), "*.ttt")
        rule = Rule([pattern], "true")
        rule.execute_all = self.execute_all
        monitor = PollingMonitor([rule], quiet)
        return monitor

    def run_in_thread(self, f):
        thread = threading.Thread(target=f)
        thread.daemon = True
        thread.start()
        self.thread = thread
        return thread

    def execute_all(self, quiet, changes):
        # Mock method for our PollingMonitor
        self.calls += 1

    def touch(self, tmpdir, filename=default_fn, data=""):
        with tmpdir.join(filename).open("w") as f:
            f.write(data)

    def start_monitor(self, monitor):
        return self.run_in_thread(lambda: monitor.monitor())

    def stop_monitor(self, monitor):
        time.sleep(0.1)
        monitor.stop()

    def run_mon(self, tmpdir, f, wait=0.05):
        monitor = self.make_monitor(tmpdir)
        try:
            self.start_monitor(monitor)
            time.sleep(wait)
            f()
            time.sleep(wait)
        finally:
            self.stop_monitor(monitor)

    def passe(self):
        pass

    def test_no_call_when_no_change(self, tmpdir):
        self.run_mon(tmpdir, self.passe)
        assert self.calls == 0

    def test_detects_file_changed(self, tmpdir):
        self.touch(tmpdir, data="foo")
        def change_file():
            self.touch(tmpdir, data="bar")
        self.run_mon(tmpdir, change_file, 1)
        assert self.calls == 1

    def test_detects_file_added(self, tmpdir):
        def add_file():
            self.touch(tmpdir)
        self.run_mon(tmpdir, add_file, 0.5)
        assert self.calls == 1

    def test_detects_file_removed(self, tmpdir):
        self.touch(tmpdir)
        def remove_file():
            tmpdir.join(self.default_fn).remove(rec=1)
        self.run_mon(tmpdir, remove_file, 0.5)
        assert self.calls == 1

    def test_stop(self, tmpdir):
        monitor = self.make_monitor(tmpdir)
        thread = self.run_in_thread(lambda: monitor.monitor())
        monitor.stop()
        time.sleep(0.01)
        assert not thread.is_alive()

