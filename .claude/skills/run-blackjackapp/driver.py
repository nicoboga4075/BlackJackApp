"""Drive BlackJack.py through Win32 window handles (PostMessage + PrintWindow).

No global input (SendInput, pyautogui): nothing can land in another window, and
the game can stay behind the terminal for the whole round.

Usage (from the repository root, with the venv's python):
    .venv\\Scripts\\python.exe .claude\\skills\\run-blackjackapp\\driver.py [--bet 20] [--actions 1] [--insurance] [--rounds 1] [--out DIR] [--launch-only]

Actions (one digit each, consumed at every "Choose an action" prompt):
    1 Hit, 2 Stand, 3 Double, 4 Split, 5 Surrender. Once the list runs out -> 2.
"""
import argparse, ctypes, ctypes.wintypes as wt, os, subprocess, sys, tempfile, time
from pathlib import Path
from PIL import Image

# No SetProcessDpiAwareness: the game is not DPI-aware, so the driver shares its
# logical coordinates (a 125 % display => a 1536x864 window) when pasting dialogs.
u32, g32 = ctypes.windll.user32, ctypes.windll.gdi32
WM_NULL, WM_SETFOCUS, WM_CHAR, WM_COMMAND = 0x0000, 0x0007, 0x0102, 0x0111

EnumProc = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
u32.PostMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
u32.GetDlgCtrlID.argtypes = [wt.HWND]
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]

REPO = Path(__file__).resolve().parents[3]

# Strings from the game's UI, matched against its dialogs.
ACTION_PROMPT = 'Choose an action'
INSURANCE = 'Insurance?'
ROUND_OVER = ('Round over', 'You have spent', 'Your money is', 'The casino')


def text(h):
    n = u32.GetWindowTextLengthW(h)
    b = ctypes.create_unicode_buffer(n + 1)
    u32.GetWindowTextW(h, b, n + 1)
    return b.value


def cls(h):
    b = ctypes.create_unicode_buffer(256)
    u32.GetClassNameW(h, b, 256)
    return b.value


def rect(h):
    r = wt.RECT()
    u32.GetWindowRect(h, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def pid_of(h):
    p = wt.DWORD()
    u32.GetWindowThreadProcessId(h, ctypes.byref(p))
    return p.value


def toplevels(pid):
    out = []
    u32.EnumWindows(EnumProc(lambda h, _: (pid_of(h) == pid and u32.IsWindowVisible(h) and out.append(h)) or True), 0)
    return out


def children(h):
    out = []
    u32.EnumChildWindows(h, EnumProc(lambda c, _: out.append(c) or True), 0)
    return out


def capture(h):
    l, t, r, b = rect(h)
    w, hh = r - l, b - t
    hdc = u32.GetWindowDC(h)
    mdc = g32.CreateCompatibleDC(hdc)
    bmp = g32.CreateCompatibleBitmap(hdc, w, hh)
    g32.SelectObject(mdc, bmp)
    u32.PrintWindow(h, mdc, 2)  # PW_RENDERFULLCONTENT: works on a covered window
    buf = ctypes.create_string_buffer(w * hh * 4)
    bi = (ctypes.c_uint32 * 10)(40, w, (-hh) & 0xFFFFFFFF, 1 | (32 << 16), 0, 0, 0, 0, 0, 0)
    g32.GetDIBits(mdc, bmp, 0, hh, buf, bi, 0)
    g32.DeleteObject(bmp); g32.DeleteDC(mdc); u32.ReleaseDC(h, hdc)
    return Image.frombuffer('RGB', (w, hh), buf, 'raw', 'BGRX', 0, 1)


def tk_invoke(h):
    """Click a tk.Button (a native Win32 button) without foreground focus.

    BM_CLICK, WM_COMMAND and mouse messages are ignored while the game is not
    active. tkWinButton.c treats BN_CLICKED (== 0 == WM_NULL) received with a
    non-zero wParam or lParam as a click and calls invoke directly.
    """
    u32.PostMessageW(h, WM_NULL, 0, h)


class Game:
    def __init__(self, outdir):
        self.out = Path(outdir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.n = 0
        # A Windows venv's python.exe is a launcher that spawns a child process:
        # start the base interpreter so our PID is the one owning the windows,
        # with the venv's packages passed through PYTHONPATH.
        site = [p for p in sys.path if p.endswith('site-packages')]
        env = dict(os.environ, PYTHONPATH=os.pathsep.join(site))
        self.proc = subprocess.Popen([sys._base_executable, 'BlackJack.py'], cwd=REPO, env=env)
        self.main = self.wait(lambda h: text(h) == 'BlackJack' and cls(h) == 'TkTopLevel', 60)
        time.sleep(2)  # let the welcome animation draw
        x0, y0, x1, y1 = rect(self.main)
        log(f'Main window {x1 - x0}x{y1 - y0}')

    def windows(self):
        return toplevels(self.proc.pid)

    def wait(self, pred, timeout=30):
        t = time.time()
        while time.time() - t < timeout:
            if self.proc.poll() is not None:
                raise SystemExit(f'The game exited (code {self.proc.returncode})')
            for h in self.windows():
                if pred(h):
                    return h
            time.sleep(0.2)
        raise TimeoutError('expected window not found')

    def dialog(self, timeout=90):
        return self.wait(lambda h: h != self.main, timeout)

    def wait_closed(self, h, timeout=15):
        t = time.time()
        while u32.IsWindow(h) and u32.IsWindowVisible(h):
            if time.time() - t > timeout:
                raise TimeoutError(f'dialog {text(h)!r} does not close')
            time.sleep(0.2)

    def shot(self, name):
        """Capture the main window with any open dialogs pasted in."""
        x0, y0, _, _ = rect(self.main)
        img = capture(self.main)
        for h in self.windows():
            if h != self.main:
                l, t, _, _ = rect(h)
                img.paste(capture(h), (l - x0, t - y0))
        self.n += 1
        path = self.out / f'{self.n:02d}_{name}.png'
        img.save(path)
        log(f'  [screenshot] {path}')

    def press_main(self, side):
        """Click "Play" (side='left') or "Quit" (side='right') on the main window.

        tk.Button labels are not exposed to Win32, so the two buttons are told
        apart by position: Play sits bottom-left, Quit bottom-right.
        """
        buttons = [c for c in children(self.main) if cls(c) == 'Button' and u32.IsWindowVisible(c)]
        assert buttons, 'no button on the main window'
        tk_invoke((min if side == 'left' else max)(buttons, key=lambda c: rect(c)[0]))

    def answer(self, dlg, value):
        """Fill a tkinter.simpledialog.askinteger, then click OK."""
        for h in [dlg] + children(dlg):
            u32.PostMessageW(h, WM_SETFOCUS, 0, 0)  # otherwise Tk drops WM_CHAR
        time.sleep(0.2)
        entry = children(dlg)[0]
        for ch in value:
            u32.PostMessageW(entry, WM_CHAR, ord(ch), 1)
            time.sleep(0.05)
        time.sleep(0.3)
        self.shot('input')
        # tk.Button labels are not exposed to Win32: OK is the leftmost button.
        ok = min((c for c in children(dlg) if cls(c) == 'Button'), key=lambda c: rect(c)[0])
        tk_invoke(ok)
        self.wait_closed(dlg)

    def msgbox(self, dlg, labels):
        """Native message box (#32770): WM_COMMAND(id) works even when inactive."""
        wanted = {l.lower() for l in labels}
        for c in children(dlg):
            if cls(c) == 'Button' and text(c).replace('&', '').lower() in wanted:
                u32.PostMessageW(dlg, WM_COMMAND, u32.GetDlgCtrlID(c) & 0xFFFF, c)
                self.wait_closed(dlg)
                return
        raise RuntimeError(f'none of {labels} in {text(dlg)!r}')

    def quit(self):
        log('Clicking "Quit"')
        self.press_main('right')
        try:
            self.proc.wait(10)
            log(f'Game closed (code {self.proc.returncode})')
        except subprocess.TimeoutExpired:
            log('The game did not close: killing it')
            self.proc.kill()


def log(msg):
    print(msg, flush=True)


def play_round(g, bet, actions, insurance=False):
    log('Clicking "Play"')
    g.press_main('left')
    d = g.dialog(30)
    while cls(d) == '#32770':  # e.g. "Only N cards left: the dealer takes a new deck." before the bet
        log(f'Message [{text(d)}]: ' + ' '.join(text(c) for c in children(d) if cls(c) == 'Static' and text(c)).strip())
        g.shot('message')
        g.msgbox(d, ('OK',))
        d = g.dialog(30)
    g.shot('bet')
    log(f'Bet: {bet}')
    g.answer(d, bet)
    while True:
        d = g.dialog()
        title = text(d)
        if cls(d) == '#32770':
            msg = ' '.join(text(c) for c in children(d) if cls(c) == 'Static' and text(c)).strip()
            log(f'Message [{title}]: {msg}')
            g.shot('message')
            # Native box buttons follow the Windows language: "Oui"/"Yes", "Non"/"No".
            if msg == INSURANCE:
                g.msgbox(d, ('Oui', 'Yes') if insurance else ('Non', 'No'))
            else:  # OK for information; Yes for any other question (such as splitting tens)
                g.msgbox(d, ('OK', 'Oui', 'Yes'))
            if msg.startswith(ROUND_OVER):
                break
        elif title == ACTION_PROMPT:
            a = actions.pop(0) if actions else '2'
            log(f'Action: {a}')
            g.shot('action')
            g.answer(d, a)
        else:
            g.shot('unexpected')
            raise RuntimeError(f'unexpected dialog: {title!r}')
    time.sleep(1)
    g.shot('end')


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--bet', default='20', help='initial bet (10 up to the player\'s money, 100 at start)')
    p.add_argument('--actions', default='1', help='digits 1-5 played in order, then 2 (Stand)')
    p.add_argument('--out', default=os.path.join(tempfile.gettempdir(), 'blackjack-run'), help='screenshot folder')
    p.add_argument('--insurance', action='store_true', help='take insurance when the dealer shows an ace (declined by default)')
    p.add_argument('--rounds', type=int, default=1, help='rounds to play in a row, each with the same bet and actions')
    p.add_argument('--launch-only', action='store_true', help='capture the welcome screen, then quit')
    a = p.parse_args()

    g = Game(a.out)
    try:
        g.shot('welcome')
        if not a.launch_only:
            for r in range(a.rounds):
                if a.rounds > 1:
                    log(f'Round {r + 1}')
                play_round(g, a.bet, list(a.actions), a.insurance)
        g.quit()
    finally:
        if g.proc.poll() is None:
            log('Killing the game')
            g.proc.kill()


if __name__ == '__main__':
    main()
