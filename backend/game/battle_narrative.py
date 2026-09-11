import hashlib


class BattleNarrativeComposer:
    """Turn authoritative battle events into deterministic presentation text."""

    _templates = {
        "zh-TW": {
            "attack_hit": (
                "{actor}抓住破綻攻向{target}，造成 {damage} 點傷害。",
                "{actor}猛然逼近{target}，一擊造成 {damage} 點傷害。",
            ),
            "skill_hit": (
                "{actor}奮力吶喊，施展【{skill}】攻向{target}，造成 {damage} 點傷害。",
                "{actor}凝聚全身力量，使出【{skill}】，重創{target}並造成 {damage} 點傷害。",
            ),
            "critical_hit": (
                "{actor}高聲喝道，施展【{skill}】，猛烈擊中{target}，暴擊造成 {damage} 點傷害！",
                "{actor}氣勢驟盛，使出【{skill}】直取{target}要害，暴擊造成 {damage} 點傷害！",
            ),
            "attack_miss": (
                "{target}驚險地躲過{actor}的攻擊。",
                "{actor}攻勢凌厲，{target}仍在千鈞一髮之際閃身避開。",
            ),
            "skill_miss": (
                "{actor}使出【{skill}】，卻被{target}驚險避開。",
                "{actor}施展【{skill}】直逼{target}，最終仍落了空。",
            ),
            "counter": (
                "{dodger}驚險地躲過{attacker}的攻擊，旋即反身攻向{target}，造成 {damage} 點傷害。",
                "{dodger}在千鈞一髮之際避開{attacker}，隨即抓住空隙反擊{target}，造成 {damage} 點傷害。",
            ),
            "skill_counter": (
                "{dodger}驚險地躲過{attacker}的攻擊，旋即高聲喝道，施展【{skill}】反擊{target}，造成 {damage} 點傷害。",
                "{dodger}側身避開{attacker}的攻勢，轉瞬使出【{skill}】直取{target}，造成 {damage} 點傷害。",
            ),
        },
        "en": {
            "attack_hit": (
                "{actor} spots an opening and strikes {target} for {damage} damage.",
                "{actor} surges toward {target}, landing a blow for {damage} damage.",
            ),
            "skill_hit": (
                "With a fierce cry, {actor} unleashes [{skill}] at {target} for {damage} damage.",
                "Gathering every ounce of strength, {actor} uses [{skill}] and deals {damage} damage to {target}.",
            ),
            "critical_hit": (
                "With a thunderous shout, {actor} unleashes [{skill}] into {target}'s opening for {damage} critical damage!",
                "{actor}'s spirit flares as [{skill}] finds {target}'s vital point for {damage} critical damage!",
            ),
            "attack_miss": (
                "{target} narrowly slips past {actor}'s attack.",
                "{actor} presses the assault, but {target} evades at the last instant.",
            ),
            "skill_miss": (
                "{actor} unleashes [{skill}], but {target} narrowly evades it.",
                "{actor}'s [{skill}] bears down on {target}, only to miss its mark.",
            ),
            "counter": (
                "{dodger} narrowly evades {attacker}'s attack, then wheels around to strike {target} for {damage} damage.",
                "{dodger} slips past {attacker} at the last instant and counters {target} for {damage} damage.",
            ),
            "skill_counter": (
                "{dodger} narrowly evades {attacker}, then cries out and counters {target} with [{skill}] for {damage} damage.",
                "{dodger} sidesteps {attacker}'s assault and instantly unleashes [{skill}] on {target} for {damage} damage.",
            ),
        },
    }

    def __init__(self, random_seed):
        self.random_seed = int(random_seed)

    def compose(self, rounds, locale):
        if locale not in self._templates:
            raise ValueError("不支援的戰報語系。")
        events = [event for round_data in rounds for event in round_data.get("events", [])]
        lines = []
        index = 0
        while index < len(events):
            event = events[index]
            following = events[index + 1] if index + 1 < len(events) else None
            if self._can_merge_counter(event, following):
                lines.append(self._counter_line(event, following, locale, index))
                index += 2
                continue
            lines.append(self._event_line(event, locale, index))
            index += 1
        return lines

    @staticmethod
    def _can_merge_counter(missed, counter):
        if not counter or missed.get("hit") or not counter.get("hit"):
            return False
        return (
            counter.get("actor_unit_id") in missed.get("target_unit_ids", [])
            and missed.get("actor_unit_id") in counter.get("target_unit_ids", [])
        )

    def _event_type(self, event):
        if not event.get("hit"):
            return "skill_miss" if event.get("action_type") == "skill" else "attack_miss"
        if event.get("critical"):
            return "critical_hit"
        return "skill_hit" if event.get("action_type") == "skill" else "attack_hit"

    def _event_line(self, event, locale, index):
        event_type = self._event_type(event)
        values = self._values(event, locale)
        if event_type == "critical_hit" and not values["skill"]:
            values["skill"] = "致命一擊" if locale == "zh-TW" else "Critical Strike"
        return {
            "event_type": event_type,
            "tone": self._tone(event_type),
            "text": self._render(locale, event_type, index, values),
        }

    def _counter_line(self, missed, counter, locale, index):
        event_type = "skill_counter" if counter.get("action_type") == "skill" else "counter"
        values = self._values(counter, locale)
        missed_values = self._values(missed, locale)
        values.update({"dodger": missed_values["target"], "attacker": missed_values["actor"]})
        return {
            "event_type": event_type,
            "tone": "critical" if counter.get("critical") else ("skill" if event_type == "skill_counter" else "normal"),
            "text": self._render(locale, event_type, index, values),
        }

    @staticmethod
    def _tone(event_type):
        if event_type == "critical_hit":
            return "critical"
        if event_type.startswith("skill"):
            return "skill"
        return "normal"

    @staticmethod
    def _name(event, field, locale):
        if locale == "en":
            return event.get(field + "_en") or event.get(field) or "Unknown"
        return event.get(field) or "未知"

    def _values(self, event, locale):
        skill = event.get("skill_name_en") if locale == "en" else event.get("skill_name")
        if not skill:
            skill = event.get("skill_name") or ""
        return {
            "actor": self._name(event, "actor_name", locale),
            "target": self._name(event, "target_name", locale),
            "skill": skill,
            "damage": event.get("damage", 0),
        }

    def _render(self, locale, event_type, index, values):
        templates = self._templates[locale][event_type]
        identity = "{}:{}:{}:{}".format(
            self.random_seed, index, event_type, values.get("actor", values.get("dodger", ""))
        ).encode("utf-8")
        variant = int.from_bytes(hashlib.blake2b(identity, digest_size=2).digest(), "big") % len(templates)
        return templates[variant].format(**values)
