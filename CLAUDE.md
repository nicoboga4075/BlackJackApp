# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A full-screen Python/Tkinter BlackJack desktop game. All the code lives in `BlackJack.py`; the other files at the root are assets: cards `<value>_<suit>.gif` (values `2`–`10`, `J`, `Q`, `K`, `A`; suits `diamonds`, `hearts`, `spades`, `clubs`), animations (`hit.gif`, `bust.gif`…), `.wav` sounds and `blackjack.ico`. The order of `values` and `suits` determines which cards the fixed-seed shuffle deals: reordering them changes every deal.

## Running the game

```
python BlackJack.py
```

- **Windows only**: sound goes through `winsound` (`PlaySound`, blocking calls).
- Third-party dependency: `matplotlib` (imported on line 1 but unused; launching fails without it). There is no `requirements.txt`, tests, linter or build configured.
- **Launch from the repository root**: `resource_path()` targets PyInstaller's `sys._MEIPASS`, but `sys` is never imported, so the `NameError` is swallowed and assets are resolved from the current directory.
- The game starts when the module loads (`BlackJack(1500, 100, 10)` at the bottom of the file: dealer's money, player's money, minimum bet), so importing the file opens the window.
- To launch and drive the game programmatically (screenshots, scripted rounds), use the `run-blackjackapp` skill in `.claude/skills/`. Its driver matches dialog titles and messages from `BlackJack.py` (constants at the top of `driver.py`): keep them in sync when changing UI text.

## Architecture

- **Model**: `Card`, `Deck` (52 cards; `draw()` and `shuffle()` also play a sound), `Dealer` and `Player` (the ace-aware point calculation is duplicated between the two: any fix must be made on both sides), `Counter` (Hi-Lo counting, shown as "RC indicator").
- **Deterministic shuffle**: `Generator()` is a fixed-seed LCG, instantiated as the global `generator`. `shuffle_cards` and `get_py_iid` (which gives a unique name to the canvas attributes keeping the `PhotoImage`s alive) consume the same stream, so the card order is reproducible from one launch to the next. The deck is never rebuilt between rounds (`resetDeck()` is never called): only the remaining cards are reshuffled.
- **`BlackJack`**: controller and view at once. `__init__` builds the window and starts `mainloop()`. A whole round runs inside a single synchronous call to `play()` (the "Play" button), which chains betting, dealing, the player's choices (`askinteger` with actions 1 to 5), `dealerTurn()` (draws up to 17), then settlement through `winPlayer` / `losePlayer` / `tiePlayer`.
- **UI**: everything is drawn on a single `Canvas`. The displayed texts (money, bet, score, remaining cards, RC) are canvas item IDs, passed to the `update*` methods and `updateAfterHit`. Animations go through `showGIF(..., autoDestruction=True)`, which calls `time.sleep` on the UI thread; the game flow relies on these blocking calls and on modal dialogs.
- **Betting**: the round is settled on `stake` (`initialBet`, doubled by a double down, allowed on the first two cards only). Insurance (`insuranceBet`, half the bet) is debited when taken and settled with the round, since the dealer's second card is only drawn in `dealerTurn()`: paid 2:1 on a dealer BlackJack, lost otherwise or on surrender.
- **Split**: a pair (same rank) on the first two cards can be split once if the player can match the bet. `play()` keeps the two hands in `hands` and swaps each into `Player.hand` in turn: `playSplitHand()` plays one (Hit, Stand, Double down), and `settleHand()` settles each against the dealer with its own entry in `stakes`. Split aces get one card each, and a two-card 21 after a split pays 1:1, not 3:2. The second hand is drawn one row lower (`row=1`), indented by `SPLIT_INDENT`.
- Beware, `showGIF(image, tag, autoDestruction=False, seconds=1)` is sometimes called with its positional arguments swapped (`hitChoice` passes `2, True`).

## Commits

Start every commit message with the emoji from [gitmoji.dev](https://gitmoji.dev) that matches the change, as the character itself (not the `:code:`), followed by a space and the subject line, as in the Portfolio repository. For example:

- `🐛 Fix ...` for a bug fix
- `✨ Add ...` for a new feature
- `💄 Update ...` for UI and style changes
- `♻️ Refactor ...` for a refactor
- `🌐 Translate ...` for translation and localization
- `📝 Document ...` for documentation
- `🔧 Configure ...` for configuration files

One emoji per commit: pick the one for the main intent of the change. Commit only when asked, and never push until asked.

## Incomplete features

Re-splitting is not supported, and both the end of the file and `play()` contain `TODO`s about the remaining rules (re-splitting, burnt cards, empty deck, etc.).
