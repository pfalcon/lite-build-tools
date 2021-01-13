#!/usr/bin/env python3
import sys
import re
import copy

import yaml


class Lexer:

    def __init__(self, s):
        self.s = s

    def empty(self):
        return not self.s

    def rest(self):
        return self.s

    def match(self, what):
        if not self.s.startswith(what):
            return None
        self.s = self.s[len(what):]
        return what

    def match_re(self, regex):
        m = re.match(regex, self.s)
        if not m:
            return m
        res = m.group()
        self.s = self.s[len(res):]
        return res


def get_val(s, struct):
    if s.startswith("@"):
        lex = Lexer(s[1:])
        filename = lex.match_re("[^[=]+?:")
        if filename:
            filename = filename[:-1]
            with open(filename) as f:
                struct = yaml.safe_load(f)
        el = process_selector(struct, lex.rest())
        el = copy.deepcopy(el)
        return el
    elif s.isdigit():
        return int(s)
    return s


# In case of assignment "selector", updates inplace.
def process_selector(struct, sel):
    # struct keep pointing to the root of YAML structure, while el points
    # to the current element.
    el = struct
    lex = Lexer(sel)
    key = None
    while not lex.empty():
        if key is not None:
            if lex.match("="):
                el[key] = get_val(lex.rest(), struct)
                break
            else:
                el = el[key]

        if lex.match("["):
            key = int(lex.match_re("[0-9]+"))
            assert lex.match("]")
        elif lex.match(".") or key is None:
            key = lex.match_re("[-a-zA-Z0-9_]+")
            assert key
        else:
            assert 0, "Expected one of operators: '.[='"

    # Return last referenced element.
    if key:
        el = el[key]
    return el


def main():
    with open(sys.argv[1]) as f:
        text = f.read()

    # Process all textual substitutions first.
    for pat in sys.argv[2:]:
        if pat.startswith("{"):
            srch, repl = pat.split("=", 1)
            text = text.replace(srch, repl)

    job = yaml.safe_load(text)

    # Process all YAML substitutions next.
    for assign in sys.argv[2:]:
        if not pat.startswith("{"):
            process_selector(job, assign)

    print(yaml.dump(job))


if __name__ == "__main__":
    main()
