import os
import re
import sys
import unittest

# Make backend modules importable when tests are run from repository root.
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from routers import translate  # noqa: E402


class FakeModel:
    def __init__(self, responses, alignment_candidates=None):
        self.responses = responses
        self.alignment_candidates = alignment_candidates or {}

    def create_chat_completion(self, messages, max_tokens, temperature):
        user_text = messages[-1]["content"]
        content = self.responses.get(user_text, "")
        return {"choices": [{"message": {"content": content}}]}

    def create_completion(self, prompt, max_tokens, temperature):
        if prompt.startswith("You are aligning a translation"):
            focus_match = re.search(r"Original focus word: (.*)", prompt)
            focus_word = focus_match.group(1).strip() if focus_match else ""
            candidate = self.alignment_candidates.get(focus_word)
            if candidate:
                return {"choices": [{"text": candidate}]}

            candidate = self.responses.get(focus_word, "")
            if candidate:
                return {"choices": [{"text": candidate}]}

            return {"choices": [{"text": ""}]}

        if prompt.startswith("You are helping a language learner"):
            focus_match = re.search(r"Original focus word: (.*)", prompt)
            focus_word = focus_match.group(1).strip() if focus_match else ""
            candidate = self.responses.get(f"alternatives:{focus_word}", "")
            return {"choices": [{"text": candidate}]}

        match = re.search(r"Text:\n(.*?)\n\nTranslation:\n", prompt, flags=re.DOTALL)
        input_text = match.group(1) if match else ""
        content = self.responses.get(input_text, "")
        return {"choices": [{"text": content}]}


class TranslateHighlightTests(unittest.TestCase):
    def test_highlight_uses_requested_occurrence_index(self):
        source = "The bank by the river is not the bank downtown."
        translated = "Die Bank am Fluss ist nicht die Bank in der Innenstadt."
        model = FakeModel(
            {
                source: translated,
                "bank": "Bank",
            }
        )

        result = translate._translate_chunk(
            model,
            source,
            "German",
            focus_word="bank",
            focus_word_index=1,
            highlight_focus=True,
        )

        self.assertEqual(
            result,
            "Die Bank am Fluss ist nicht die [[[Bank]]] in der Innenstadt.",
        )

    def test_highlight_defaults_to_first_occurrence(self):
        source = "The bank by the river is not the bank downtown."
        translated = "Die Bank am Fluss ist nicht die Bank in der Innenstadt."
        model = FakeModel(
            {
                source: translated,
                "bank": "Bank",
            }
        )

        result = translate._translate_chunk(
            model,
            source,
            "German",
            focus_word="bank",
            highlight_focus=True,
        )

        self.assertEqual(
            result,
            "Die [[[Bank]]] am Fluss ist nicht die Bank in der Innenstadt.",
        )

    def test_existing_markers_are_preserved(self):
        already_marked = "Die [[[Bank]]] ist dort."
        model = FakeModel({})

        result = translate._ensure_focus_highlight(
            model,
            already_marked,
            "The bank is there.",
            "German",
            "bank",
            focus_word_index=0,
        )

        self.assertEqual(result, already_marked)

    def test_misplaced_markers_are_repositioned(self):
        source = "The bank is here."
        translated = "Die Bank ist hier [[[Bank]]]."
        model = FakeModel(
            {
                source: translated,
                "bank": "Bank",
            }
        )

        result = translate._translate_chunk(
            model,
            source,
            "German",
            focus_word="bank",
            focus_word_index=0,
            highlight_focus=True,
        )

        self.assertEqual(result, "Die [[[Bank]]] ist hier.")

    def test_longer_token_wins_over_trailing_raw_focus_word(self):
        source = "Rektorn gjorde en otålig gest."
        translated = "The principal made an impatient gesture. gest"
        model = FakeModel(
            {
                source: translated,
                "gest": "gest",
            },
            alignment_candidates={"gest": "gesture"},
        )

        result = translate._translate_chunk(
            model,
            source,
            "English",
            focus_word="gest",
            focus_word_index=4,
            highlight_focus=True,
        )

        self.assertEqual(result, "The principal made an impatient [[[gesture]]].")

    def test_translated_equivalent_wins_over_trailing_raw_token(self):
        source = "Rektorn gjorde en otålig gest."
        translated = "The principal made an impatient gesture. gest"
        model = FakeModel(
            {
                source: translated,
                "gest": "gesture",
            },
            alignment_candidates={"gest": "gesture"},
        )

        result = translate._translate_chunk(
            model,
            source,
            "English",
            focus_word="gest",
            focus_word_index=4,
            highlight_focus=True,
        )

        self.assertEqual(result, "The principal made an impatient [[[gesture]]].")

    def test_swedish_example_highlights_translated_word_not_raw_suffix(self):
        source = "Rektorn gjorde en otålig gest."
        translated = "The principal made an impatient gesture. gest"
        model = FakeModel(
            {
                source: translated,
                "gest": "gest",
            },
            alignment_candidates={"gest": "gesture"},
        )

        result = translate._translate_chunk(
            model,
            source,
            "English",
            focus_word="gest",
            focus_word_index=4,
            highlight_focus=True,
        )

        self.assertEqual(result, "The principal made an impatient [[[gesture]]].")

    def test_position_fallback_marks_translated_token_when_no_candidate_match(self):
        model = FakeModel({"focus": ""})

        result = translate._ensure_focus_highlight(
            model,
            "Hallo Welt",
            "Hello world",
            "German",
            "focus",
            focus_word_index=0,
        )

        self.assertEqual(result, "[[[Hallo]]] Welt")

    def test_position_fallback_avoids_first_word_for_mid_sentence_focus(self):
        source = "Du kommer på tapeten i morgon."
        translated = "You will be in the spotlight tomorrow."
        model = FakeModel(
            {
                source: translated,
                "kommer": "",
            }
        )

        result = translate._translate_chunk(
            model,
            source,
            "English",
            focus_word="kommer",
            focus_word_index=1,
            highlight_focus=True,
        )

        self.assertEqual(result, "You [[[will]]] be in the spotlight tomorrow.")

    def test_live_ui_sentence_chooses_has_not_tail_har(self):
        source = "—■ Att han verkligen har fräckheten att komma med sån strunt!"
        translated = "That he has the audacity to come up with such nonsense! har"
        model = FakeModel(
            {
                source: translated,
                "har": "has",
            },
            alignment_candidates={"har": "has"},
        )

        result = translate._translate_chunk(
            model,
            source,
            "English",
            focus_word="har",
            focus_word_index=3,
            highlight_focus=True,
        )

        self.assertEqual(
            result,
            "That he [[[has]]] the audacity to come up with such nonsense!",
        )

    def test_full_sentence_alignment_candidate_is_ignored(self):
        source = "The bank is here."
        translated = "Die Bank ist hier."
        model = FakeModel(
            {
                source: translated,
                "bank": translated,
            }
        )

        result = translate._translate_chunk(
            model,
            source,
            "German",
            focus_word="bank",
            focus_word_index=0,
            highlight_focus=True,
        )

        self.assertEqual(result, "Die [[[Bank]]] ist hier.")

    def test_parse_translation_alternatives_limits_to_five(self):
        raw = "arrive, come, show up, appear, reach, get"
        parsed = translate._parse_translation_alternatives(raw, "kommer")
        self.assertEqual(parsed, ["arrive", "come", "show up", "appear", "reach"])

    def test_suggest_translation_alternatives_uses_prompt_result(self):
        source = "Du kommer pa tapeten i morgon."
        translated = "You will be in the spotlight tomorrow."
        model = FakeModel({"alternatives:kommer": "arrive, come, show up, appear, reach"})

        alternatives = translate._suggest_translation_alternatives(
            model,
            source,
            translated,
            "kommer",
            "English",
        )

        self.assertEqual(alternatives, ["arrive", "come", "show up", "appear", "reach"])


if __name__ == "__main__":
    unittest.main()
