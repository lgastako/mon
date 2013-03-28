import os
import sys
import time
import json
import envoy
import glob2
import argparse

from functools import partial

from termcolor import colored

try:
    import pyinotify
except Exception:
    pass

DEFAULT_CONFIG_FILE="Monfile.json"


def first(xs):
    try:
        return xs[0]
    except IndexError:
        if xs is None or len(xs) ==0:
            return None
        raise


class Rule(object):

    def __init__(self, patterns, actions):
        self.patterns = patterns
        self.actions = actions

    def fill_references(self, action, changed_files):
        references = {
            "filename": first(changed_files),
            "filenames": " ".join(changed_files),
            "filename_list": ", ".join(changed_files)
        }
        return action % references

    def execute_all(self, quiet, changed_files):
        for action in self.actions:
            final_action = self.fill_references(action, changed_files)
            execute_action(final_action, quiet)

    def __repr__(self):
        return "Rule(%s, %s)" % (self.patterns, self.actions)


def expand_names(rules, names):
    if names is None or len(names) <= 0:
        return rules

    rules = expand_lhs_names(rules, names)
    rules = expand_rhs_names(rules, names)
    return rules


def expand_lhs_names(rules, names):
    new_rules = []
    for rule in rules:
        for pattern in rule.patterns:
            if pattern in names:
                for new_pat in names[pattern]:
                    new_rules.append(Rule([new_pat], rule.actions))
            else:
                new_rules.append(rule)
    return new_rules


def expand_rhs_names(rules, names):
    # This does it inplace, is that ok?
    for rule in rules:
        new_actions = []
        for action in rule.actions:
            if action in names:
                new_actions.extend(names[action])
            else:
                new_actions.append(action)
        rule.actions = new_actions
    return rules


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

    try:
        names_config = config["names"]
        rules = expand_names(rules, names_config)
    except KeyError:
        pass

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
    C = partial(colored, color=color)
    print C("Result: status code %d" % response.status_code)
    if not quiet:
        print C("-" * 78)
        print C(response.std_out)
        print C("-" * 78)


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
                    rule.execute_all(self.quiet, changes)
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
    if fn == "-":
        config = json.load(sys.stdin)
    else:
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

