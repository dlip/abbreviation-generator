import logging
import utils

log = logging.getLogger("abbrgen")

qwerty = [
    ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
    ["a", "s", "d", "f", "g", "h", "j", "k", "l", ";"],
    ["z", "x", "c", "v", "b", "n", "m", ",", ".", "/"],
]
colemak = [
    ["q", "w", "f", "p", "g", "j", "l", "u", "y", ";"],
    ["a", "r", "s", "t", "d", "h", "n", "e", "i", "o"],
    ["z", "x", "c", "v", "b", "k", "m", ",", ".", "/"],
]
colemak_dh = [
    ["q", "w", "f", "p", "b", "j", "l", "u", "y", ";"],
    ["a", "r", "s", "t", "g", "m", "n", "e", "i", "o"],
    ["z", "x", "c", "d", "v", "k", "h", ",", ".", "/"],
]
canary = [
    ["w", "l", "y", "p", "b", "z", "f", "o", "u", "'"],
    ["c", "r", "s", "t", "g", "m", "n", "e", "i", "a"],
    ["q", "j", "v", "d", "k", "x", "h", ";", ",", "."],
]

finger_maping = [
    [1, 2, 3, 4, 4, 5, 5, 6, 7, 8],
    [1, 2, 3, 4, 4, 5, 5, 6, 7, 8],
    [1, 2, 3, 4, 4, 5, 5, 6, 7, 8],
]

hand_row_maping = [
    ["tl", "tl", "tl", "tl", "tl", "tr", "tr", "tr", "tr", "tr"],
    ["ml", "ml", "ml", "ml", "ml", "mr", "mr", "mr", "mr", "mr"],
    ["bl", "bl", "bl", "bl", "bl", "br", "br", "br", "br", "br"],
]

# https://colemakmods.github.io/mod-dh/model.html
effort_map_standard = [
    [3, 2.5, 2.1, 2.3, 2.6, 3.4, 2.2, 2.0, 2.4, 3.0],
    [1.6, 1.3, 1.1, 1.0, 2.9, 2.9, 1.0, 1.1, 1.3, 1.6],
    [2.7, 2.4, 1.8, 2.2, 3.7, 2.2, 1.8, 2.4, 2.7, 3.3],
]
effort_map_matrix = [
    [3, 2.4, 2.0, 2.2, 3.2, 3.2, 2.2, 2.0, 2.4, 3],
    [1.6, 1.3, 1.1, 1.0, 2.9, 2.9, 1.0, 1.1, 1.3, 1.6],
    [3.2, 2.6, 2.3, 1.6, 3.0, 3.0, 1.6, 2.3, 2.6, 3.2],
]


class EffortCalculator:
    def __init__(self, layout, effort_map):
        self.layout = layout
        self.effort_map = effort_map
        self.layout_map = {}
        self.effort_map = {}
        self.hand_row_map = {}
        for r in range(0, len(layout)):
            for c in range(0, len(layout[r])):
                self.layout_map[layout[r][c]] = finger_maping[r][c]
                self.effort_map[layout[r][c]] = effort_map[r][c]
                self.hand_row_map[layout[r][c]] = hand_row_maping[r][c]

    def get_scissor_count(self, abbr):
        result = 0
        indexes = {
            "tl": 0,
            "ml": 0,
            "bl": 0,
            "tr": 0,
            "mr": 0,
            "br": 0,
        }
        for i in range(0, len(abbr)):
            indexes[self.hand_row_map[abbr[i]]] += 1

        if indexes["tl"] and indexes["bl"]:
            result += min(indexes["tl"], indexes["bl"])

        if indexes["tr"] and indexes["br"]:
            result += min(indexes["tr"], indexes["br"])

        return result

    def get_sfb_count(self, abbr):
        result = 0
        indexes = {}
        for i in range(0, len(abbr)):
            index = self.layout_map[abbr[i]]
            if not index in indexes:
                indexes[index] = 1
            else:
                indexes[index] += 1
        for x in indexes.values():
            if x > 1:
                result += x - 1

        return result

    def calculate(self, abbr, sfb_penalty, scissor_penalty, chorded_mode):
        for i in range(0, len(abbr)):
            if abbr[i] not in self.layout_map:
                log.debug(f"rejected: letter '{abbr[i]}' not in keyboard layout")
                return

        scissor_count = self.get_scissor_count(abbr)
        sfb_count = self.get_sfb_count(abbr)
        if chorded_mode:
            seen = set()
            for char in abbr:
                if char in seen:
                    log.debug(
                        "rejected: duplicate letters not accepted in chorded mode"
                    )
                    return
                seen.add(char)
            if scissor_count:
                log.debug("rejected: scissors not accepted in chorded mode")
                return

            if sfb_count:
                log.debug("rejected: SFBs not accepted in chorded mode")
                return

        result = 0
        for i in range(0, len(abbr)):
            result += self.effort_map[abbr[i]]

        if not chorded_mode:
            if scissor_count:
                log.debug("Applying scissor penalty")
                result += scissor_count * scissor_penalty
            if sfb_count:
                log.debug("Applying SFB penalty")
                result += sfb_count * sfb_penalty

        return result
