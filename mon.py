import os
import time
import json
import envoy
import glob2
import argparse

from termcolor import colored

try:
    import pyinotify
except Exception:
    pass

DEFAULT_CONFIG_FILE="Monfile.json"


class Rule(object):

    def __init__(self, patterns, actions):
        self.patterns = patterns
        self.actions = actions

    def execute_all(self, quiet):
        for action in self.actions:
            execute_action(action, quiet)


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
        elif not isinstance(pattern, list):
            pattern = [pattern]
        if not isinstance(actions, list):
            actions = [actions]
        rules.append(Rule(pattern, actions))
    return rules


def execute_action(action, quiet):
    print "Running action: ", action

    if isinstance(action, unicode):
        action = action.encode("utf-8")

    response = envoy.run(action)
    if response.status_code == 0:
        color = "green"
    else:
        color = "red"
    print colored("Result: status code %d" % response.status_code, color)
    if not quiet:
        print colored("-" * 78, color)
        print colored(response.std_out, color)
        print colored("-" * 78, color)


class AbstractMonitor(object):

    def __init__(self, rules, quiet):
        self.rules = rules
        self.quiet = quiet
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
                        ", ".join(changes)
                    )
                    rule.execute_all(self.quiet)
                else:
                    time.sleep(1)

    def _detect_changes(self, patterns):
        # print "checking patterns: %s" % ", ".join(patterns)
        changes = []
        for pattern in patterns:
            pattern_files = glob2.glob(pattern)
            for pfile in pattern_files:
                if self._file_changed(pfile):
                    changes.append(pfile)
        return changes

    def _file_changed(self, pfile):
        last_ts = self._timestamps.get(pfile)
        file_ts = self._get_file_timestamp(pfile)
        if not last_ts or file_ts > last_ts:
            self._timestamps[pfile] = file_ts
            return True
        return False

    def _get_file_timestamp(self, pfile):
        return time.ctime(os.path.getmtime(pfile))


def choose_monitor_class():
    if "inotify" in globals():
        return InotifyMonitor
    return PollingMonitor


def load_rules_from_config(fn):
    with open(fn) as f:
        config = json.load(f)
    return parse_rules(config)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config",  default=DEFAULT_CONFIG_FILE)
    parser.add_argument("-q", "--quiet",  action="store_true")
    args = parser.parse_args()

    try:
        rules = load_rules_from_config(args.config)
    except IOError:
        parser.error("Could not read config file: %s" % args.config)
    else:
        Monitor = choose_monitor_class()
        monitor = Monitor(rules, args.quiet)
        monitor.monitor()

