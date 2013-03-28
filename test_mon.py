from functools import partial

from mon import parse_rules
from mon import execute_action

from termcolor import colored


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


class TestExecuteAction:

    def test_execute_successful_action_not_quiet(self, capfd):
        execute_action("echo success", False)
        out, err = capfd.readouterr()
        color = "green"
        C = partial(colored, color=color)
        assert out == ("Running action:  echo success\n" +
                       C("Result: status code 0") + "\n" +
                       C("-" * 78) + "\n" +
                       C("success\n") + 
                       "\n" +
                       C("-" * 78) + "\n")

    def test_execute_successful_action_quiet(self, capfd):
        execute_action("echo success", True)
        out, err = capfd.readouterr()
        assert out == "success"


