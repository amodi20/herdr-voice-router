# Herdr Voice Router

Talk to any coding-agent session in [Herdr](https://herdr.dev) from whichever pane you're in. Say another pane's name, and your prompt goes there:

```
Ask backend how many users signed up this week.          -> sent to the "backend" pane
How many users signed up this week? Ask backend.         -> sent to the "backend" pane
Ask backend for the signup count, and ask frontend       -> backend and frontend each
  what's left on the login page.                            get their own question
fix this bug please                                      -> stays in this pane
```

It works with typing or any voice dictation tool (Wispr Flow, Apple Dictation, Spokenly, …), because it only looks at the text.

**New here? Start with the [step-by-step tutorial](TUTORIAL.md).**

## Two ways to use it

| | Where you type | Install |
|---|---|---|
| **Claude Code plugin** (main way) | Inside any Claude Code pane: just mention a pane name and press Enter | `/plugin marketplace add amodi20/herdr-voice-router` then `/plugin install herdr-voice-router@herdr-voice-router` |
| **Herdr plugin** | An "Ask a pane" popup, from any pane, including plain terminals | `herdr plugin install amodi20/herdr-voice-router` |

You can install either one or both. Requirements: Herdr 0.9+, Python 3 (`python3` on your PATH), and Claude Code for the Claude Code plugin.

After installing the Claude Code plugin, restart your Claude sessions so they load it.

## The rules

- **Mention a pane's name and the prompt goes there.** Phrasing doesn't matter.
- **The routing words are removed.** The name and words like "ask" or "in the … chat," come out before sending.
- **Several panes at once:** if you *ask* two or more panes ("ask backend …, and ask frontend …"), each gets its own question.
- **Mentioned, not asked:** a name inside a question ("ask backend about the **frontend** migration") stays part of the question.
- **No other pane named:** naming your own pane, or no pane at all, keeps the prompt where it is.
- **Busy panes:** Herdr won't deliver to a Claude that's stuck on a permission prompt. You'll see an error and nothing is sent.

## Naming panes

- **Automatic:** when Claude starts in a pane with no name, the Claude Code plugin names the pane after its project folder. `~/code/billing-api` becomes "billing api".
- **Your own name:** press **Ctrl+B, Shift+P** in Herdr, or run `herdr pane rename <pane-id> backend`. Names you set are never overwritten.
- **Several names for one pane:** separate them with `/`, for example `herdr pane rename w1:p2 "backend / api"`.
- **Choose distinctive names:** any mention forwards the prompt, so pick names you won't say by accident ("billing", "atlas"), not "data" or "code".

## Voice options

Anything that types into the terminal works:

| Platform | Options |
|---|---|
| Any | Claude Code's built-in voice dictation · [Spokenly](https://spokenly.app) (macOS, Windows, Linux; can run Parakeet or Whisper fully offline) |
| macOS | Apple Dictation (press fn twice; much improved lately) · [Wispr Flow](https://wisprflow.ai) |
| Windows | Voice Typing (**Win + H**) · Wispr Flow |
| Linux | [nerd-dictation](https://github.com/ideasman42/nerd-dictation) |

Tested on macOS. Linux should work. The Claude Code hook may work on Windows but hasn't been tested.

## Keybinding for the popup

To open the Herdr plugin's popup with **Ctrl+B, A**, add this to `~/.config/herdr/config.toml`, then run `herdr server reload-config`:

```toml
[[keys.command]]
key = "prefix+a"
type = "plugin_action"
command = "amodi20.voice-router.ask"
description = "Ask a pane"
```

In the popup, type or dictate a sentence that names a pane. If you don't name one, you get a numbered list. You have 2 seconds to press **Esc** before each question is sent.

## How it works

```
Your voice tool  →  text typed into the pane you're in
Claude Code      →  on Enter, the plugin's hook (route_hook.py) reads the text first
Hook             →  finds pane names, runs: herdr agent prompt <pane> "<question>"
Herdr            →  delivers each question to that pane's agent
```

| File | What it does |
|---|---|
| `route_hook.py` | Claude Code `UserPromptSubmit` hook: finds pane names and forwards |
| `auto_label.py` | Claude Code `SessionStart` hook: names an unnamed pane after its folder |
| `pane_router.py` | The "Ask a pane" popup, plus shared Herdr helpers |
| `herdr-plugin.toml` | Herdr plugin manifest |
| `.claude-plugin/`, `hooks/hooks.json` | Claude Code plugin packaging |

Everything runs locally. There are no API keys and no cloud service, and nothing is sent anywhere except to your own Herdr panes.

## Manual install (without the Claude Code plugin)

Clone the repo and add the hooks to `~/.claude/settings.json` yourself. Don't also install the plugin, or prompts get forwarded twice.

```json
"hooks": {
  "UserPromptSubmit": [
    { "hooks": [{ "type": "command", "command": "python3 /path/to/herdr-voice-router/route_hook.py", "timeout": 15 }] }
  ],
  "SessionStart": [
    { "matcher": "startup|resume", "hooks": [{ "type": "command", "command": "python3 /path/to/herdr-voice-router/auto_label.py", "timeout": 10 }] }
  ]
}
```

## Ideas for later

- Answer questions from all sessions' chat history, without naming a pane
- A built-in voice key in Herdr with local speech-to-text
- Bring the answer back to the pane you asked from, or read it aloud
