import io
import yaml
import re
from rasa_core.actions.action import Action
from rasa_core.events import ActionExecuted

# easy way to force the bot to follow specific story flows when they are encountered regardless of training. This could be important for touchy subject matter when deviation from the script could prove troublesome.
# after bot utters x, and user inputs intent y, perform action(s) z.
# Format in rules.yml file
# output_enforcer:
#  - after: utter_ask_mood_activity
#    then: tell_activity
#    enforce: utter_ask_mood_choices
class PatternBreaker(object):
    def __init__(self, rules):
        self.rules = rules if rules is not None else []
        self.actions_to_ignore = ['action_listen', 'enforced_utterance']

    def ignore_action(self, action_name):
        self.actions_to_ignore.append(action_name)

    def find(self, after):
        for rule in self.rules:
            if re.match(rule['after'], after):
                return rule
        return None

    def get_output_enforcer(self, parse_data, tracker):
        previous_action = self._get_previous_action(tracker)
        intent = parse_data["intent"]["name"]
        if previous_action is None:
            return None
        if intent is None:
            return None
        return self.get_output_enforcer_template(parse_data, previous_action, intent)

    def get_output_enforcer_template(self, parse_data, intent):
        rule = self.find(intent)
        if rule is None:
            return None
        if rule['then'] is None:
            # ToDo for now, simply ensuring that the info exists, not that the intent is valid.
            return None
        if rule['enforce'] is None:
            # ToDo for now, simply ensuring that the info exists, not that the template exists.
            return None
        return rule['enforce']

    @staticmethod
    def _load_yaml(rules_file):
        with io.open(rules_file, 'r', encoding='utf-8') as stream:
            try:
                return yaml.load(stream)
            except yaml.YAMLError as exc:
                raise ValueError(exc)

    def _get_previous_action(self, tracker):
        action_listen_found = False
        for i in range(len(tracker.events) - 1, -1, -1):
            if i == 0:
                return None
            if type(tracker.events[i]) is ActionExecuted \
                    and action_listen_found is False \
                    and tracker.events[i].action_name not in self.actions_to_ignore:
                return tracker.events[i].action_name

        return None


class EnforcedUtterance(Action):
    def __init__(self, template):
        self.template = template

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_template(self.template, tracker)

        return []

    def name(self):
        return 'enforced_utterance'
