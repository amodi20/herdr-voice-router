#!/usr/bin/env python3
"""Claude Code UserPromptSubmit hook: forward a prompt to other Herdr panes.

If a prompt mentions another pane's name anywhere ("how many users signed up? ask backend"),
it goes to that pane instead of this one. A pane can have several names
separated by "/" ("backend / api"). Prompts without a name pass through.

If you ask two or more panes in one prompt ("ask backend X, and ask frontend Y"),
each pane gets its own part.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pane_router import list_panes, send  # noqa: E402

# Routing words around a name. A name with a cue ("ask backend", "the billing chat",
# "backend, ...") is being asked something; a bare name is just mentioned.
BEFORE = (r"(?P<hey>\b(?:hey|ok|okay)\b[\s,]*)?"
          r"(?P<verb>\b(?:ask|tell|in|to|for|with|send\s+to)\s+)?(?:\b(?:the|my)\s+)?")
AFTER = r"(?P<noun>\s+(?:chat|pane|terminal|session|window|tab)\b)?(?P<comma>\s*[,:])?"
CONNECTORS = r"(?:[\s,;:-]|\b(?:and|also|then|plus)\b)+"


def name_pattern(name):
    """Whole-word match; spaces/dashes interchangeable; plural 's' optional."""
    parts = [re.escape(w) for w in re.split(r"[\s_-]+", name.strip().lower()) if w]
    if not parts:
        return None
    if len(parts[-1]) > 3 and parts[-1].endswith("s"):
        parts[-1] = parts[-1][:-1]
    return re.compile(BEFORE + r"\b" + r"[\s_-]+".join(parts) + r"s?\b" + AFTER, re.IGNORECASE)


def find_mentions(prompt, panes):
    """Every mention of another pane: [(pane, start, end, asked)], in order."""
    found = []
    for pane in panes:
        for pattern in filter(None, map(name_pattern, pane[1].split("/"))):
            for m in pattern.finditer(prompt):
                at_sentence_start = re.search(r"(^|[.?!]\s*)$", prompt[:m.start()])
                asked = bool(m["hey"] or m["verb"] or m["noun"] or (m["comma"] and at_sentence_start))
                found.append((pane, m.start(), m.end(), asked))
    found.sort(key=lambda f: (f[1], -f[2]))  # earliest first, longest first
    mentions = []
    for f in found:
        if mentions and f[1] < mentions[-1][2]:
            continue  # overlaps a longer name already kept
        prev = mentions[-1] if mentions else None
        if prev and prev[0] == f[0] and not prompt[prev[2]:f[1]].strip(" ,"):
            # "Backend API": two names of one pane in a row are one mention
            mentions[-1] = (prev[0], prev[1], f[2], prev[3] or f[3])
        else:
            mentions.append(f)
    return mentions


def split_by_pane(prompt, mentions):
    """[(pane, text)] for each pane being asked something."""
    asked = [m for m in mentions if m[3]]
    if len({m[0] for m in asked}) < 2:
        pane, start, end, _ = mentions[0]  # one pane: the first name gets it all
        return [(pane, prompt[:start] + " " + prompt[end:])]

    def name_comes_last(i):  # "How many signups? Ask backend." names the pane afterwards
        nxt = asked[i + 1][1] if i + 1 < len(asked) else len(prompt)
        return re.match(r"\s*([.?!]|$)", prompt[asked[i][2]:nxt]) is not None

    parts, pending = [], prompt[:asked[0][1]]
    for i, (pane, start, end, _) in enumerate(asked):
        nxt = asked[i + 1][1] if i + 1 < len(asked) else len(prompt)
        after = prompt[end:nxt]
        if name_comes_last(i):
            parts.append((pane, pending))
            pending = re.sub(r"^\s*[.?!]+", "", after)
            continue
        own, before, pending = after, pending, ""
        if i + 1 < len(asked) and name_comes_last(i + 1):
            # the next pane is named after its question: give it the last sentence
            cut = [m.end() for m in re.finditer(r"[.?!]\s+", after.rstrip())]
            if cut:
                own, pending = after[:cut[-1]], after[cut[-1]:]
        parts.append((pane, before + " " + own))
    if pending.strip():
        parts[-1] = (parts[-1][0], parts[-1][1] + " " + pending)

    merged = {}
    for pane, text in parts:
        merged[pane] = (merged.get(pane, "") + " " + text).strip()
    return list(merged.items())


def tidy(text):
    text = re.sub(r"\s+([?.!,;:])", r"\1", text)  # "total ?" -> "total?"
    text = re.sub(r"([?.!])[.,;:]+", r"\1", text)  # "?." -> "?"
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"^" + CONNECTORS, "", text)
    text = re.sub(CONNECTORS + r"$", "", text)
    return text[:1].upper() + text[1:]


def block(message):
    """Stop the prompt here and show the message instead."""
    print(json.dumps({"decision": "block", "reason": message}))
    sys.exit(0)


def main():
    prompt = json.load(sys.stdin).get("prompt", "")
    if os.environ.get("HERDR_ENV") != "1":
        return  # not inside Herdr: let it through
    mentions = find_mentions(prompt, list_panes())
    if not mentions:
        return  # no other pane named: keep it here
    report = []
    for (pane_id, name), text in split_by_pane(prompt, mentions):
        question = tidy(text)
        if not question:
            continue
        try:
            send(pane_id, question)
            report.append(f"Sent to {name}: {question}")
        except RuntimeError as e:
            report.append(f"Could not send to {name}: {e}")
    if report:
        block("\n".join(report))


if __name__ == "__main__":
    main()
