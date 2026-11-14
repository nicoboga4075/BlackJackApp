---
name: run-blackjackapp
description: Run, play and screenshot the BlackJack game (Tkinter, Windows). Use when asked to run, start, launch, play, screenshot or drive BlackJack.py, or to check a change in the real game window rather than by reading code.
---

A full-screen Tkinter game, Windows only. An agent drives it with
`.claude/skills/run-blackjackapp/driver.py`: the driver launches the game,
plays one round through Win32 messages sent to the game's windows, and saves
PNG screenshots. It never touches the keyboard or mouse, so the game can stay
behind the terminal. All paths are relative to the repository root.

## Prerequisites

Windows, with Python 3 (checked with 3.14.7) and a desktop session. `winsound`
only exists on Windows, and the game plays real sounds during the round.

## Setup

```bash
python -m venv .venv
.venv/Scripts/python -m pip install matplotlib
```

`matplotlib` is unused, but `BlackJack.py` imports it on line 1: without it the
game does not start. It also installs Pillow, which the driver needs. `.venv/`
is ignored by git.

## Run (agent)

```bash
PYTHONIOENCODING=utf-8 .venv/Scripts/python .claude/skills/run-blackjackapp/driver.py --launch-only
PYTHONIOENCODING=utf-8 .venv/Scripts/python .claude/skills/run-blackjackapp/driver.py --bet 30 --actions 3 --out "$TEMP/blackjack-double"
```

- `--launch-only`: captures the welcome screen, then clicks "Quit".
- Without it, the driver plays one round: it clicks "Play", bets `--bet`
  (20 by default; the game accepts 10 up to the player's money, 100 at
  start), then plays one digit of `--actions` at each "Choose an action"
  prompt: 1 Hit, 2 Stand, 3 Double, 4 Split, 5 Surrender. After a split,
  each hand asks again with only 1 to 3, so `--actions 432` splits, doubles
  hand 1 and stands on hand 2. Once the list runs out, it plays 2. It declines insurance (`--insurance` takes it)
  and answers "OK" to every message until "Round over", then quits.
- The driver prints every game message to stdout (`Message [title]: …`).
  Screenshots go to `--out` (`%TEMP%\blackjack-run` by default), numbered
  `01_welcome.png`, `02_bet.png`… up to `NN_end.png`, with open dialogs
  pasted in. **Look at the screenshots**: scores, money and cards are only
  visible there.
- A round takes about 30 to 60 s, because animations and sounds block the game.
- On any error the game process is killed (`finally`).

For another scenario, `Game` provides `shot`, `press_main`, `answer`,
`msgbox`, `dialog` and `quit`: write a variant of `play_round`. If you change a
dialog title or message in `BlackJack.py`, update the strings the driver
matches (`ACTION_PROMPT`, `INSURANCE`, `ROUND_OVER`) at the top of `driver.py`.

### Forcing a deal (insurance, dealer BlackJack, small cards…)

The shuffle always deals the same cards, and the dealer never shows an ace.
To test another deal, run the driver on a throwaway copy of the game whose
`Deck.shuffle()` puts chosen cards on top (draw order: player, dealer, player,
then the player's hits, then the dealer's second card; after a split: hand 1's
second card and hits, then hand 2's):

```bash
T="$TEMP/bjcopy"; rm -rf "$T"; mkdir -p "$T"
cp -r BlackJack.py *.gif *.wav *.ico .claude "$T"/
.venv/Scripts/python - "$T/BlackJack.py" <<'PY'
import sys; p = sys.argv[1]; s = open(p, encoding='utf-8').read()
a = "        self.cards = shuffle_cards(generator,self.cards) # rd.shuffle(self.cards)\n"
b = a + "        top = [c for n in os.environ.get('BJ_FORCE_TOP', '').split(',') for c in self.cards if c.value+'_'+c.suit == n]\n        self.cards = top + [c for c in self.cards if not any(c is t for t in top)]\n"
assert a in s; open(p, 'w', encoding='utf-8').write(s.replace(a, b))
PY
BJ_FORCE_TOP=10_hearts,A_spades,9_clubs,K_hearts PYTHONIOENCODING=utf-8 .venv/Scripts/python "$T/.claude/skills/run-blackjackapp/driver.py" --bet 20 --actions 2 --insurance --out "$TEMP/bj-ins-bj"
BJ_FORCE_TOP=8_hearts,6_spades,8_clubs,3_hearts,10_spades,10_hearts,10_clubs,7_diamonds PYTHONIOENCODING=utf-8 .venv/Scripts/python "$T/.claude/skills/run-blackjackapp/driver.py" --bet 20 --actions 432 --out "$TEMP/bj-split8"
```

The driver computes the game folder from its own path, so the copy's driver
plays the copy. The patch compares cards by identity (`c is t`): `Card.__eq__`
compares values only, so `in` would drop every card of the same value.

## Run (human)

```bash
.venv/Scripts/python BlackJack.py
```

A full-screen window opens. Click "Quit" to exit, and launch it from the
repository root.

## Gotchas

- **Do not use pyautogui or SendInput.** The game does not get the foreground
  when it launches, and Windows refuses to give it ("Access denied"). Simulated
  keystrokes then go to the Claude Code terminal: a "20" bet typed that way
  arrived as a user message.
- **Tk buttons** are real Win32 controls of class `Button`, but `BM_CLICK`,
  `WM_COMMAND` sent to the parent and mouse messages are ignored while the game
  is not active. Only `PostMessage(button, WM_NULL, 0, hwnd)` works: Tk treats
  it as `BN_CLICKED`, which equals 0 (`tk_invoke`).
- **Invisible labels**: Tk buttons do not expose their text to Win32,
  `GetWindowText` returns `''`. Buttons are told apart by position: in
  `askinteger`, OK is the leftmost; on the main window, "Play" is bottom-left
  and "Quit" bottom-right.
  The `showinfo`, `askyesno` and `showerror` boxes, on the other hand, are
  native `#32770` dialogs: their text is readable and `WM_COMMAND(id)` closes
  them.
- **Typing**: without a `WM_SETFOCUS` sent first, Tk drops the `WM_CHAR`s.
- **Scaling**: at 125 %, the game (not DPI-aware) measures 1536x864. The
  driver must not declare itself DPI-aware, or the window rectangles it uses
  to paste dialogs into screenshots stop matching the game's.
- **Venv launcher**: a Windows venv's `python.exe` starts a second process. The
  driver therefore launches `sys._base_executable` with the venv's
  `site-packages` in `PYTHONPATH`, so the tracked PID is the one owning the
  windows.
- **Dialogs**: wait for a dialog to close (`wait_closed`) before looking for
  the next one, or you find the same one again.
- **Deterministic shuffle**: every launch deals the same cards (Jack ♦,
  King ♠ / 10 ♦, then Ace ♦ on a hit). Handy to reproduce a round, but a
  single round does not explore rare cases: force a deal instead (see above).
- **First launch**: with a fresh `matplotlib`, the game prints "Matplotlib is
  building the font cache" and takes several seconds longer.

## Troubleshooting

- `ModuleNotFoundError: No module named 'matplotlib'`: you are using the
  system Python instead of `.venv/Scripts/python`.
- `TimeoutError: expected window not found` right after `Clicking "Play"`:
  the click did not go through. Check that `tk_invoke` (the `WM_NULL` post)
  is used, not `BM_CLICK` or mouse messages.
- The "Initial bet" screenshot shows the canvas without the dialog, then
  `unexpected dialog`: the input was submitted but the driver did not wait
  for the dialog to close (`wait_closed`).
