#!/usr/bin/env python3
"""Pane router: a window (or Herdr popup) that sends questions to panes by name.

Say or type a sentence that mentions a pane, like "ask backend how many users
signed up?". It uses the same matching as the Claude Code hook (route_hook.py).
If no pane is named, you pick one from a numbered list.
"""
import json
import os
import re
import subprocess
import sys
import time

FILLER = {"the", "a", "an", "my", "in", "to", "for", "of", "and", "with",
          "chat", "pane", "session", "window", "tab"}
NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
           "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}


def herdr(*args):
    """Run a herdr command and return its JSON reply."""
    out = subprocess.run(["herdr", *args], capture_output=True, text=True)
    try:
        reply = json.loads(out.stdout or out.stderr)
    except json.JSONDecodeError:
        raise RuntimeError((out.stderr or out.stdout).strip())
    if "error" in reply:
        raise RuntimeError(reply["error"].get("message", reply["error"]))
    return reply["result"]


def list_panes():
    """Return [(pane_id, name)] for every pane except the router's own."""
    me = os.environ.get("HERDR_PANE_ID")
    panes = []
    for p in herdr("pane", "list")["panes"]:
        name = p.get("label") or p.get("terminal_title_stripped")
        if name and p["pane_id"] != me:
            panes.append((p["pane_id"], name))
    return panes


def words(text):
    """Lowercase words without filler, with plural 's' removed."""
    out = set()
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w not in FILLER:
            out.add(w[:-1] if len(w) > 3 and w.endswith("s") else w)
    return out


def find_panes(panes, spoken):
    """Panes sharing the most words with what you said (several if tied)."""
    said = words(spoken)
    scores = [(len(said & words(name)), (pid, name)) for pid, name in panes]
    best = max((score for score, _ in scores), default=0)
    return [p for score, p in scores if best and score == best]


def choose(panes):
    """Show a numbered list and let you answer with a number or a name."""
    for i, (_, name) in enumerate(panes, 1):
        print(f"  {i}. {name}")
    answer = input("Which one? (number or name) ").strip().lower().rstrip(".")
    n = NUMBERS.get(answer) or (int(answer) if answer.isdigit() else 0)
    if 1 <= n <= len(panes):
        return panes[n - 1]
    matches = find_panes(panes, answer)
    return matches[0] if len(matches) == 1 else None


def countdown(name, seconds=2):
    """Show where it's going; Esc cancels, any other key sends right away."""
    print(f"Sending to: {name}  (Esc to cancel)")
    if not sys.stdin.isatty():
        return True
    import select, termios, tty  # Mac/Linux only; the hooks never call this
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd, termios.TCSANOW)  # keep keys already pressed
        ready, _, _ = select.select([fd], [], [], seconds)
        return not (ready and os.read(fd, 1) == b"\x1b")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def send(pane_id, text):
    herdr("agent", "prompt", pane_id, text)


def ask():
    """Read one sentence, pick the pane(s), and send."""
    from route_hook import find_mentions, split_by_pane, tidy
    panes = list_panes()
    text = input("\nAsk> ").strip()
    if not text:
        return
    mentions = find_mentions(text, panes)
    if mentions:
        jobs = split_by_pane(text, mentions)
    else:
        print("Which pane?")
        pane = choose(panes)
        if not pane:
            print("Didn't catch which pane. Nothing sent.")
            return
        jobs = [(pane, text)]
    for (pane_id, name), question in jobs:
        question = tidy(question)
        if not question:
            continue
        if not countdown(name):
            print(f"Cancelled: {name}")
            continue
        try:
            send(pane_id, question)
            print(f"Sent to {name}: {question}")
        except RuntimeError as e:
            print(f"Could not send to {name}: {e}")


def main():
    once = "--once" in sys.argv  # Herdr popup mode: one question, then close
    print("\033]0;Pane Router\007", end="")  # window title
    try:
        while True:
            ask()
            if once:
                time.sleep(1.5)  # time to read the result before the popup closes
                return
    except (EOFError, KeyboardInterrupt):
        print()


if __name__ == "__main__":
    sys.exit(main())
