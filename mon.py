import time
import json
import envoy
import glob2
import argparse
try:
    import pyinotify
except Exception:
    pass

DEFAULT_CONFIG_FILE="mon.json"


class Rule(object):

    def __init__(self, patterns, actions):
        self.patterns = patterns
        self.actions = actions

    def execute_all(self, stdio):
        for action in self.actions:
            execute_action(action, stdio)


def parse_rules(config):
    groups = config.get("groups", [])
    rules = []
    try:
        rules_config = config["rules"]
    except KeyError:
        raise Exception("No \"rules\" section present in config file.")
    for pattern, actions in rules_config.iteritems():
        if pattern in groups:
            pattern = groups[pattern]
        if not isinstance(actions, list):
            actions = [actions]
        rules.append(Rule(pattern, actions))
    return rules


def execute_action(action, stdio):
    print "Running action: ", action
    response = envoy.run(action)
    print "Result: status code ", response.status_code
    if stdio:
        print response.std_out


class AbstractMonitor(object):

    def __init__(self, rules, stdio):
        self.rules = rules
        self.stdio = stdio
        self._timestamps = {}


class InotifyMonitor(AbstractMonitor):
    pass


class PollingMonitor(AbstractMonitor):

    def monitor(self):
        print "Monitoring %d rule%s." % (
            len(self.rules),
            ("s"  if len(self.rules) > 1 else "")
        )
        while 1:
            for rule in self.rules:
                changes = self._detect_changes(rule.patterns)
                if changes:
                    print "Changes detected in the following file%s: %s" % (
                        ("s" if len(changes) > 1 else ""), 
                        ",".join(changes)
                    )
                    rule.execute_all(self.stdio)
                else:
                    time.sleep(1)

    def _detect_changes(self, patterns):
        print "checking patterns: %s" % ",".join(patterns)
        changes = []
        for pattern in patterns:
            pattern_files = glob2.glob(pattern)
            for pfile in pattern_files:
                if self._file_changed(pfile):
                    changes.append(pfile)
        return changes

    def _file_changed(self, pfile):
        last_ts = self._timestamps.get(pfile)
        if not last_ts:
            self._timestamps[pfile] = last_ts
            return True
        file_ts = self._get_file_timestamp(pfile)
        if file_ts > last_ts:
            self._timestamps[pfile] = file_ts
            return True
        # TODO: Handle case where a file disappears.
        return False


def choose_monitor_class():
    if "inotify" in globals():
        return InotifyMonitor
    return PollingMonitor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", default=DEFAULT_CONFIG_FILE)
    parser.add_argument("--stdio", "-s", action="store_true")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)
    rules = parse_rules(config)
    Monitor = choose_monitor_class()
    monitor = Monitor(rules, args.stdio)
    monitor.monitor()
