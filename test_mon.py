from mon import parse_rules


class TestParseRules:

    def test_empty_rules(self):
        config = {"rules":{}}
        rules = parse_rules(config)
        assert rules == []

