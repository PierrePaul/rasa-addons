import io
import yaml
import re
from rasa_core.actions.action import Action
from rasa_core.events import ActionExecuted, ActionReverted, ReminderScheduled, SlotSet
from datetime import timedelta
from datetime import datetime

# easy way to force the bot to follow specific story flows when they are encountered regardless of training
class OutputEnforcer(object):
    def __init__(self, rules):
        self.rules = rules if rules is not None else []
        self.actions_to_ignore = ['action_listen', 'enforced_utterance']

    def ignore_action(self, action_name):
        self.actions_to_ignore.append(action_name)

    def find(self, after, intent, tracker):
        potential_matches = []
        for rule in self.rules:
            if re.match(rule['after'], after) and re.match(rule['then'], intent):
                potential_matches.append(rule)

        if 0 < len(potential_matches):
            return potential_matches.pop()
            # entity_matches = []
            # slot_matches = []
            #
            # is_simple = True
            # for rule in potential_matches:
            #     if 'entities' in rule or 'slots' in rule:
            #         is_simple = False
            #         break
            # if is_simple:
            #     return potential_matches.pop()
            #
            # # TODO missing check to ensure actions exist and add support for "something" value in slots
            # for rule in potential_matches:
            #     is_valid = True
            #     if 'entities' in rule:
            #         for entity in rule['entities']:
            #             if 'key' not in entity or entity['key'] not in parse_entities or 'value' not in entity or entity['value'] not in parse_values:
            #                 is_valid = False
            #         if is_valid:
            #             entity_matches.append(rule)
            #     is_valid = True
            #     if 'slots' in rule:
            #         for slot in rule['slots']:
            #             if 'key' not in slot or tracker.get_slot(slot['key']) is None or 'value' not in slot and entity_values[entity['key']] != tracker.get_slot(slot['key']):
            #                 is_valid = False
            #         if is_valid:
            #             slot_matches.append(rule)
            #
            # # full_match = set(entity_matches).intersection(slot_matches)
            # #
            # # if 0 < len(full_match):
            # #     return full_match.pop()
            #
            # if 0 < len(slot_matches):
            #     return slot_matches.pop()
            #
            # if 0 < len(entity_matches):
            #     return entity_matches.pop()

        return None

    def get_output_enforcer(self, parse_data, tracker):
        previous_action = self._get_previous_action(tracker)
        intent = parse_data["intent"]["name"]
        if previous_action is None:
            return None
        if intent is None:
            return None
        return self.get_output_enforcer_template(parse_data, previous_action, intent, tracker)

    def get_output_enforcer_template(self, parse_data, previous_action, intent, tracker):
        # parse_entities = map(lambda e: e['entity'], parse_data['entities'])
        # parse_values = map(lambda e: e['value'], parse_data['entities'])
        rule = self.find(previous_action, intent, tracker)
        if rule is None:
            return None

        # TODO perhaps a better approach is to get next predicted outcome and if it matches rule['enforce'] return None
        delta_time = 500000
        result = [ActionReverted(), ActionReverted()]
        for action_to_perform in rule['enforce']:
            reminder_at = datetime.now() + timedelta(microseconds=delta_time)
            result.append(ReminderScheduled(action_to_perform, reminder_at, kill_on_user_message=False))
            delta_time += 500000
        for ent in parse_data['entities']:
            if 'value' in ent and 'entity' in ent:
                result.append(SlotSet(ent['entity'], ent['value']))
        return result

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
    def __init__(self, actions):
        self.actions = actions

    def run(self, dispatcher, tracker, domain):
        return self.actions

    def name(self):
        return 'enforced_utterance'
