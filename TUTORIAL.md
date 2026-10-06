# Herdr Voice Router: Tutorial

This guide takes you from nothing to talking to your Claude sessions by voice, in about 10 minutes.

## What it does

If you run several Claude Code sessions in Herdr, you normally have to click into the right pane before asking it something. With this tool you stay where you are and just **say the pane's name**:

> "How many users signed up this week? Ask **backend**."

The question goes to the pane named "backend", and the answer appears there. Prompts that don't mention another pane's name work as normal.

---

## Step 1: Check you have the basics

| What | How to check |
|---|---|
| Herdr 0.9 or newer | `herdr --version` |
| Claude Code | `claude --version` |
| Python 3 | `python3 --version` |

## Step 2: Install the Claude Code plugin

Open Claude Code (in any folder) and run:

```
/plugin marketplace add amodi20/herdr-voice-router
/plugin install herdr-voice-router@herdr-voice-router
```

The first command tells Claude Code where the plugin lives. `amodi20/herdr-voice-router` is the repo's address on GitHub: the account, then the repo name. The second command installs it.

Then **restart your Claude sessions inside Herdr**: exit each one and start `claude` again. Sessions that were already open won't load the plugin until you do.

## Step 3 (optional): Install the Herdr plugin

This adds an **"Ask a pane"** popup you can open from any pane, including plain terminals where Claude isn't running:

```bash
herdr plugin install amodi20/herdr-voice-router
```

To open the popup with **Ctrl+B, Shift+A**, add this to `~/.config/herdr/config.toml` and run `herdr server reload-config`:

```toml
[[keys.command]]
key = "prefix+shift+a"
type = "plugin_action"
command = "amodi20.voice-router.ask"
description = "Ask a pane"
```

If that key is already taken in your config, use any free one, such as `prefix+i`. To check the popup works without any key, run `herdr plugin action invoke amodi20.voice-router.ask`.

## Step 4: Name your panes

The tool finds panes by name, so short, distinctive names work best.

- **Automatic:** when Claude starts in a pane that has no name, the pane is named after its project folder. `~/code/billing-api` becomes "billing api".
- **Your own name:** in Herdr, click into the pane and press **Ctrl+B**, then **Shift+P**, and type a name. You can also run:
  ```bash
  herdr pane list                       # find the pane ID, like w1:p3
  herdr pane rename w1:p3 backend
  ```
- **Several names for one pane:** separate them with `/`:
  ```bash
  herdr pane rename w1:p3 "backend / api"
  ```

Names you set yourself are never overwritten.

**Choosing good names:** any mention of a name forwards your prompt. So pick names you won't say by accident: "billing" or "atlas", not "data" or "code".

## Step 5: Try it by typing

1. Click into any Claude pane.
2. Type a prompt that mentions another pane, for example: `What's 2 + 2? Ask backend.`
3. Press Enter.

You should see:

```
Sent to backend: What's 2 + 2?
```

Look at the "backend" pane, where Claude is answering. The pane you typed in doesn't answer.

## Step 6: Add your voice

Any tool that types into the terminal works. Speak, then press Enter:

| Platform | Option |
|---|---|
| Any | Claude Code's built-in voice dictation |
| macOS, Windows, Linux | [Spokenly](https://spokenly.app), which can run Parakeet or Whisper fully offline |
| macOS | Apple Dictation (press **fn** twice) or [Wispr Flow](https://wisprflow.ai) |
| Windows | Voice Typing (**Win + H**) |
| Linux | [nerd-dictation](https://github.com/ideasman42/nerd-dictation) |

---

## Examples

Say these from any Claude pane. Phrasing doesn't matter:

| You say | Goes to | That pane receives |
|---|---|---|
| Ask backend how many users signed up this week. | backend | How many users signed up this week. |
| How many users signed up this week? Ask backend. | backend | How many users signed up this week? |
| In the billing chat, which invoices failed today? | billing | Which invoices failed today? |
| What's the build status in frontend? | frontend | What's the build status? |
| Hey api, what changed today? (pane named "backend / api") | backend | What changed today? |
| Ask backend about the frontend migration | backend only (frontend is mentioned, not asked) | About the frontend migration |
| Ask backend for the signup count, and ask frontend what's left on login | **both** | backend: For the signup count · frontend: What's left on login |
| How many signups? Ask backend. Any failed invoices? Ask billing. | **both** | backend: How many signups? · billing: Any failed invoices? |
| fix this bug please | stays in this pane | |

## The rules in short

- **Say a name and it's forwarded.** It works anywhere in the sentence.
- **Several panes at once:** if you *ask* two or more panes ("ask backend …, and ask frontend …"), each one gets its own question.
- **Mentioned, not asked:** a name inside a question ("ask backend about the **frontend** migration") stays part of the question.
- **Your own pane's name, or no name:** the prompt stays where you are.
- **Clean questions:** the name and words like "ask" or "in the … chat," are removed before sending.
- **Busy Claude:** Herdr won't send to a pane whose Claude is stuck on a permission question. You'll see an error and nothing is sent.

---

## Troubleshooting

**My prompt stayed in the current pane.**
- Run `herdr pane list` and check the target pane's name. You have to say a name exactly (a plural "s" is fine).
- Did you restart your Claude sessions after installing? Type `/hooks` in the pane to see whether the plugin's hooks are loaded.
- The hook only runs in **Claude Code** panes. From a plain terminal, use the Herdr plugin's "Ask a pane" popup.

**It went to the wrong pane.**
You probably said another pane's name by accident, maybe as part of your question. Rename that pane to something more distinctive.

**Every prompt is forwarded twice.**
You have the plugin installed **and** the hooks added by hand in `~/.claude/settings.json`. Remove the hand-added `route_hook.py` and `auto_label.py` entries.

**"Could not send to …"**
The target Claude is busy with a question or permission prompt, or the pane was closed. Go answer it, or check `herdr pane list`.

**Two panes have the same name.**
Panes opened in the same project folder get the same automatic name. Rename one with **Ctrl+B, Shift+P**.

## Update or remove

```
/plugin marketplace update herdr-voice-router                   # fetch the latest version
/plugin update herdr-voice-router@herdr-voice-router            # install it
/plugin uninstall herdr-voice-router@herdr-voice-router         # remove it
```

For the Herdr plugin: `herdr plugin uninstall amodi20.voice-router`.

## How it works (for the curious)

```
Your voice tool  →  text typed into the Claude pane you're in
Claude Code      →  on Enter, the plugin's hook reads the text first
Hook             →  finds pane names, runs: herdr agent prompt <pane> "<question>"
Herdr            →  delivers each question to that pane's Claude
```

Everything runs on your machine. There are no API keys and no cloud service, and nothing is sent anywhere except to your own Herdr panes.
