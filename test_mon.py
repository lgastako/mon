from functools import partial

from mon import parse_rules
from mon import execute_action
from mon import expand_names
from mon import Rule

from termcolor import colored

SC = partial(colored, color="green")
EC = partial(colored, color="red")


class TestExpandNames:

    rules = [
    ]

    def test_empty_names_section(self):
        result = expand_names(self.rules, {})
        assert result == self.rules


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
