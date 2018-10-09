import io
import yaml
import re
from rasa_core.actions.action import Action

# This added functionality ensures that when the bot encounters an intent, regardless of conversational flow, it skips to a specific topic. Important to ensure immediate response to urgent matters regardless of training.
# after intent, then utter.
# Format in rules.yml file
# pattern_breaker:
#  - after: help
#    then: utter_help_intro
class PatternBreaker(object):
    def __init__(self, rules):
        self.rules = rules if rules is not None else []
        self.actions_to_ignore = ['action_listen', 'pattern_breaker_utterance']

    def ignore_action(self, action_name):
        self.actions_to_ignore.append(action_name)

    def find(self, after):
        for rule in self.rules:
            if re.match(rule['after'], after):
                return rule
        return None

    def get_pattern_breaker(self, parse_data, tracker):
        intent = parse_data["intent"]["name"]
        if intent is None:
            return None
        return self._get_pattern_breaker_template(parse_data, intent)

    def _get_pattern_breaker_template(self, parse_data, intent):
        rule = self.find(intent)
        if rule is None:
            return None
        if rule['then'] is None:
            # ToDo for now, simply ensuring that the info exists, not validating it is an actual template... to be honest, not clear how that works yet. Will implement when I do.
            return None
        return rule['then']

    @staticmethod
    def _load_yaml(rules_file):
        with io.open(rules_file, 'r', encoding='utf-8') as stream:
            try:
                return yaml.load(stream)
            except yaml.YAMLError as exc:
                raise ValueError(exc)


class PatternBreakerUtterance(Action):
    def __init__(self, template):
        self.template = template

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_template(self.template, tracker)

        return []

    def name(self):
        return 'pattern_breaker_utterance'
