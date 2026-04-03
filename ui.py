"""Game Manager — Tkinter UI."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from db import GameDB, Game, STATUSES, SLOTS, PRIORITIES


# ---------------------------------------------------------------------------
# Base dialog
# ---------------------------------------------------------------------------

class _Dialog(tk.Toplevel):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

    def _center(self):
        self.update_idletasks()
        p = self.master
        x = p.winfo_x() + (p.winfo_width() - self.winfo_width()) // 2
        y = p.winfo_y() + (p.winfo_height() - self.winfo_height()) // 2
        self.geometry(f'+{max(0,x)}+{max(0,y)}')

    def _show(self):
        self._center()
        self.wait_window()


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

class AddGameDialog(_Dialog):
    def __init__(self, parent, db, app, default_status='playing'):
        super().__init__(parent, "게임 추가")
        self.db = db
        self.app = app

        f = ttk.Frame(self, padding=20)
        f.pack()

        ttk.Label(f, text="이름:").grid(row=0, column=0, sticky='w', pady=3)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(f, textvariable=self.name_var, width=30)
        name_entry.grid(row=0, column=1, sticky='ew', pady=3)
        name_entry.focus()

        ttk.Label(f, text="상태:").grid(row=1, column=0, sticky='w', pady=3)
        self.status_var = tk.StringVar(value=default_status)
        self.status_combo = ttk.Combobox(
            f, textvariable=self.status_var,
            values=['playing', 'wishlist'], state='readonly', width=15,
        )
        self.status_combo.grid(row=1, column=1, sticky='w', pady=3)

        ttk.Label(f, text="슬롯:").grid(row=2, column=0, sticky='w', pady=3)
        self.slot_var = tk.StringVar(value='A')
        self.slot_combo = ttk.Combobox(
            f, textvariable=self.slot_var,
            values=SLOTS, state='readonly', width=15,
        )
        self.slot_combo.grid(row=2, column=1, sticky='w', pady=3)

        ttk.Label(f, text="장르:").grid(row=3, column=0, sticky='w', pady=3)
        self.genre_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.genre_var, width=30).grid(
            row=3, column=1, sticky='ew', pady=3,
        )

        btn = ttk.Frame(f)
        btn.grid(row=4, column=0, columnspan=2, pady=(15, 0))
        ttk.Button(btn, text="추가", command=self._ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn, text="취소", command=self.destroy).pack(side=tk.LEFT, padx=5)

        self.status_combo.bind('<<ComboboxSelected>>', self._on_status)
        self._on_status()
        name_entry.bind('<Return>', lambda e: self._ok())
        self._show()

    def _on_status(self, _event=None):
        if self.status_var.get() == 'wishlist':
            self.slot_combo.set('-')
            self.slot_combo.configure(state='disabled')
        else:
            self.slot_combo.configure(state='readonly')

    def _ok(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("입력 필요", "게임 이름을 입력해주세요.", parent=self)
            return
        status = self.status_var.get()
        game = Game(
            name=name,
            status=status,
            slot=self.slot_var.get(),
            genre=self.genre_var.get().strip(),
            start_date=datetime.now().strftime('%Y%m%d') if status == 'playing' else '',
        )
        self.db.add(game)
        self.app.refresh_all()
        self.destroy()


class AddHoursDialog(_Dialog):
    def __init__(self, parent, game):
        super().__init__(parent, "시간 추가")
        self.result = None

        f = ttk.Frame(self, padding=20)
        f.pack()

        ttk.Label(f, text=game.name, font=('', 11, 'bold')).pack(anchor='w')
        current = game.hours or 0
        ttk.Label(f, text=f"현재: {current:.0f}h").pack(anchor='w', pady=(0, 10))

        ttk.Label(f, text="추가 시간:").pack(anchor='w')
        self.hours_var = tk.StringVar()
        entry = ttk.Entry(f, textvariable=self.hours_var, width=10)
        entry.pack(anchor='w', pady=3)
        entry.focus()
        entry.bind('<Return>', lambda e: self._ok())

        btn = ttk.Frame(f)
        btn.pack(pady=(10, 0))
        ttk.Button(btn, text="확인", command=self._ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn, text="취소", command=self.destroy).pack(side=tk.LEFT, padx=5)

        self._show()

    def _ok(self):
        try:
            val = float(self.hours_var.get())
            if val <= 0:
                raise ValueError
            self.result = val
            self.destroy()
        except ValueError:
            messagebox.showwarning("입력 오류", "양수를 입력해주세요.", parent=self)


class CompleteDialog(_Dialog):
    def __init__(self, parent, game):
        super().__init__(parent, "게임 완료")
        self.confirmed = False
        self.satisfaction = None
        self.comment = ''
        self.end_date = datetime.now().strftime('%Y%m%d')

        f = ttk.Frame(self, padding=20)
        f.pack()

        ttk.Label(f, text=f"{game.name} 완료!", font=('', 12, 'bold')).pack(
            anchor='w', pady=(0, 10),
        )

        ttk.Label(f, text="만족도 (0.0 ~ 5.0):").pack(anchor='w')
        self.sat_var = tk.StringVar()
        sat_entry = ttk.Entry(f, textvariable=self.sat_var, width=10)
        sat_entry.pack(anchor='w', pady=3)
        sat_entry.focus()

        ttk.Label(f, text="코멘트:").pack(anchor='w', pady=(5, 0))
        self.comment_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.comment_var, width=40).pack(anchor='w', pady=3)

        ttk.Label(f, text="완료일:").pack(anchor='w', pady=(5, 0))
        self.date_var = tk.StringVar(value=self.end_date)
        ttk.Entry(f, textvariable=self.date_var, width=12).pack(anchor='w', pady=3)

        btn = ttk.Frame(f)
        btn.pack(pady=(15, 0))
        ttk.Button(btn, text="확인", command=self._ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn, text="취소", command=self.destroy).pack(side=tk.LEFT, padx=5)

        self._show()

    def _ok(self):
        sat_str = self.sat_var.get().strip()
        if sat_str:
            try:
                sat = float(sat_str)
                if not (0 <= sat <= 5):
                    raise ValueError
                self.satisfaction = sat
            except ValueError:
                messagebox.showwarning(
                    "입력 오류", "만족도는 0.0~5.0 사이 숫자를 입력해주세요.", parent=self,
                )
                return
        self.comment = self.comment_var.get().strip()
        self.end_date = self.date_var.get().strip()
        self.confirmed = True
        self.destroy()


class SlotSelectDialog(_Dialog):
    def __init__(self, parent, game_name):
        super().__init__(parent, "슬롯 선택")
        self.result = None

        f = ttk.Frame(self, padding=20)
        f.pack()

        ttk.Label(f, text=game_name, font=('', 11, 'bold')).pack(anchor='w')
        ttk.Label(f, text="슬롯을 선택해주세요:").pack(anchor='w', pady=(5, 3))
        self.slot_var = tk.StringVar(value='A')
        ttk.Combobox(
            f, textvariable=self.slot_var,
            values=['AAA', 'AA', 'A'], state='readonly', width=10,
        ).pack(anchor='w', pady=3)

        btn = ttk.Frame(f)
        btn.pack(pady=(10, 0))
        ttk.Button(btn, text="확인", command=self._ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn, text="취소", command=self.destroy).pack(side=tk.LEFT, padx=5)

        self._show()

    def _ok(self):
        self.result = self.slot_var.get()
        self.destroy()


class EditGameDialog(_Dialog):
    def __init__(self, parent, game, db, app):
        super().__init__(parent, "게임 편집")
        self.game = game
        self.db = db
        self.app = app

        f = ttk.Frame(self, padding=20)
        f.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("이름:", 'name', game.name, 30, None),
            ("상태:", 'status', game.status, 15, STATUSES),
            ("슬롯:", 'slot', game.slot, 15, SLOTS),
            ("장르:", 'genre', game.genre, 30, None),
            ("시간:", 'hours', _opt_str(game.hours), 10, None),
            ("만족도:", 'satisfaction', _opt_str(game.satisfaction), 10, None),
            ("코멘트:", 'comment', game.comment, 40, None),
            ("시작일:", 'start_date', game.start_date, 12, None),
            ("완료일:", 'end_date', game.end_date, 12, None),
            ("가격:", 'price', _opt_str(game.price), 10, None),
            ("우선순위:", 'priority', game.priority, 15, PRIORITIES),
        ]

        self.vars = {}
        for i, (label, key, value, width, values) in enumerate(fields):
            ttk.Label(f, text=label).grid(row=i, column=0, sticky='w', pady=2, padx=(0, 10))
            var = tk.StringVar(value=value)
            self.vars[key] = var
            if values is not None:
                ttk.Combobox(f, textvariable=var, values=values, state='readonly', width=width).grid(
                    row=i, column=1, sticky='w', pady=2,
                )
            else:
                ttk.Entry(f, textvariable=var, width=width).grid(
                    row=i, column=1, sticky='ew', pady=2,
                )
        f.columnconfigure(1, weight=1)

        btn = ttk.Frame(f)
        btn.grid(row=len(fields), column=0, columnspan=2, pady=(15, 0))
        ttk.Button(btn, text="저장", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn, text="삭제", command=self._delete).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn, text="취소", command=self.destroy).pack(side=tk.LEFT, padx=5)

        self._show()

    def _save(self):
        name = self.vars['name'].get().strip()
        if not name:
            messagebox.showwarning("입력 필요", "게임 이름을 입력해주세요.", parent=self)
            return

        try:
            hours = _safe_float(self.vars['hours'].get())
            sat = _safe_float(self.vars['satisfaction'].get())
            price = _safe_float(self.vars['price'].get())
        except ValueError as e:
            messagebox.showwarning("입력 오류", str(e), parent=self)
            return

        self.game.name = name
        self.game.status = self.vars['status'].get()
        self.game.slot = self.vars['slot'].get() or '-'
        self.game.genre = self.vars['genre'].get().strip()
        self.game.hours = hours
        self.game.satisfaction = sat
        self.game.comment = self.vars['comment'].get().strip()
        self.game.start_date = self.vars['start_date'].get().strip()
        self.game.end_date = self.vars['end_date'].get().strip()
        self.game.price = price
        self.game.priority = self.vars['priority'].get()

        self.db.commit()
        self.app.refresh_all()
        self.destroy()

    def _delete(self):
        if messagebox.askyesno("삭제 확인", f"'{self.game.name}'을(를) 삭제하시겠습니까?", parent=self):
            self.db.remove(self.game)
            self.app.refresh_all()
            self.destroy()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _opt_str(val) -> str:
    if val is None:
        return ''
    if isinstance(val, float) and val == int(val):
        return str(int(val))
    return str(val)


def _safe_float(s: str):
    s = s.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        raise ValueError(f"'{s}'은(는) 올바른 숫자가 아닙니다.")


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class GameManagerApp:
    def __init__(self, db: GameDB):
        self.db = db
        self.root = tk.Tk()
        self.root.title("Game Manager")
        self.root.geometry("1200x750")
        self.root.minsize(1000, 600)

        self._setup_styles()
        self._build_toolbar()
        self._build_tabs()
        self.refresh_all()

        self.root.bind('<Control-s>', lambda _: self._save())
        self.root.bind('<F5>', lambda _: self._reload())

    # ── styles ────────────────────────────────────────────────────────────

    def _setup_styles(self):
        style = ttk.Style()
        style.configure('GameName.TLabel', font=('', 11, 'bold'))
        style.configure('SlotHeader.TLabelframe.Label', font=('', 12, 'bold'))

    # ── toolbar ───────────────────────────────────────────────────────────

    def _build_toolbar(self):
        bar = ttk.Frame(self.root, padding=(10, 5))
        bar.pack(fill=tk.X)
        ttk.Button(bar, text="+ 게임 추가", command=self._add_game).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text="CSV 저장", command=self._save).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text="CSV 다시 불러오기", command=self._reload).pack(side=tk.LEFT, padx=2)
        self.status_var = tk.StringVar()
        ttk.Label(bar, textvariable=self.status_var).pack(side=tk.RIGHT)

    # ── tabs ──────────────────────────────────────────────────────────────

    def _build_tabs(self):
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.tab_playing = ttk.Frame(self.nb)
        self.tab_history = ttk.Frame(self.nb)
        self.tab_wishlist = ttk.Frame(self.nb)
        self.tab_others = ttk.Frame(self.nb)

        self.nb.add(self.tab_playing, text="  현재 플레이  ")
        self.nb.add(self.tab_history, text="  완료 기록  ")
        self.nb.add(self.tab_wishlist, text="  위시리스트  ")
        self.nb.add(self.tab_others, text="  기타  ")

        self._build_playing_tab()
        self._build_history_tab()
        self._build_wishlist_tab()
        self._build_others_tab()

    # ── Playing tab ───────────────────────────────────────────────────────

    def _build_playing_tab(self):
        self.playing_container = ttk.Frame(self.tab_playing, padding=10)
        self.playing_container.pack(fill=tk.BOTH, expand=True)

    def _refresh_playing(self):
        for w in self.playing_container.winfo_children():
            w.destroy()

        playing = self.db.by_status('playing')
        slots = {'AAA': [], 'AA': [], 'A': []}
        unslotted = []
        for g in playing:
            if g.slot in slots:
                slots[g.slot].append(g)
            else:
                unslotted.append(g)

        col = 0
        for slot_name in ['AAA', 'AA', 'A']:
            frame = ttk.LabelFrame(self.playing_container, text=f"  {slot_name}  ", padding=10)
            frame.grid(row=0, column=col, sticky='nsew', padx=5, pady=5)
            self.playing_container.columnconfigure(col, weight=1, uniform='slot')
            col += 1
            if not slots[slot_name]:
                ttk.Label(frame, text="(비어있음)", foreground='gray').pack(pady=20, padx=20)
            else:
                for g in slots[slot_name]:
                    self._make_card(frame, g)

        if unslotted:
            frame = ttk.LabelFrame(self.playing_container, text="  미분류  ", padding=10)
            frame.grid(row=0, column=col, sticky='nsew', padx=5, pady=5)
            self.playing_container.columnconfigure(col, weight=1, uniform='slot')
            for g in unslotted:
                self._make_card(frame, g)

        self.playing_container.rowconfigure(0, weight=1)

    def _make_card(self, parent, game: Game):
        card = ttk.LabelFrame(parent, text=f"  {game.name}  ", padding=8)
        card.pack(fill=tk.X, pady=4)

        if game.genre:
            ttk.Label(card, text=game.genre, foreground='gray').pack(anchor='w')
        hours_text = f"{game.hours:.0f}h" if game.hours else "0h"
        ttk.Label(card, text=hours_text, font=('', 10)).pack(anchor='w', pady=(2, 0))

        btns = ttk.Frame(card)
        btns.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(btns, text="+시간", width=6,
                   command=lambda g=game: self._add_hours(g)).pack(side=tk.LEFT, padx=1)
        ttk.Button(btns, text="완료", width=5,
                   command=lambda g=game: self._complete_game(g)).pack(side=tk.LEFT, padx=1)
        ttk.Button(btns, text="일시정지", width=7,
                   command=lambda g=game: self._pause_game(g)).pack(side=tk.LEFT, padx=1)
        ttk.Button(btns, text="편집", width=5,
                   command=lambda g=game: self._edit_game(g)).pack(side=tk.LEFT, padx=1)

    # ── History tab ───────────────────────────────────────────────────────

    def _build_history_tab(self):
        bar = ttk.Frame(self.tab_history, padding=5)
        bar.pack(fill=tk.X)
        ttk.Label(bar, text="정렬:").pack(side=tk.LEFT)
        for text, key in [("만족도", 'satisfaction'), ("시간", 'hours'),
                          ("완료일", 'end_date'), ("이름", 'name')]:
            ttk.Button(bar, text=text,
                       command=lambda k=key: self._sort_history(k)).pack(side=tk.LEFT, padx=2)

        tree_frame = ttk.Frame(self.tab_history)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        cols = ('name', 'genre', 'hours', 'satisfaction', 'comment', 'start_date', 'end_date')
        self.history_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode='browse')

        heads = {'name': '게임명', 'genre': '장르', 'hours': '시간',
                 'satisfaction': '만족도', 'comment': '코멘트',
                 'start_date': '시작일', 'end_date': '완료일'}
        widths = {'name': 180, 'genre': 150, 'hours': 60, 'satisfaction': 60,
                  'comment': 300, 'start_date': 90, 'end_date': 90}
        anchors = {'hours': 'e', 'satisfaction': 'center',
                   'start_date': 'center', 'end_date': 'center'}

        for c in cols:
            self.history_tree.heading(c, text=heads[c])
            self.history_tree.column(c, width=widths.get(c, 100),
                                     minwidth=50, anchor=anchors.get(c, 'w'))

        sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=sb.set)
        self.history_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        sb.pack(fill=tk.Y, side=tk.RIGHT)

        self.history_tree.bind('<Double-1>', self._on_history_dblclick)
        self._history_map: dict[str, Game] = {}
        self._history_sort_key = 'satisfaction'
        self._history_sort_rev = True

    def _refresh_history(self):
        self.history_tree.delete(*self.history_tree.get_children())
        self._history_map.clear()
        games = self.db.by_status('completed')

        key = self._history_sort_key
        rev = self._history_sort_rev

        def sort_val(g):
            v = getattr(g, key)
            if v is None:
                return -999 if rev else 999
            return v

        if key == 'name':
            games.sort(key=lambda g: g.name, reverse=rev)
        else:
            games.sort(key=sort_val, reverse=rev)

        for i, g in enumerate(games):
            iid = f'h{i}'
            self._history_map[iid] = g
            self.history_tree.insert('', 'end', iid=iid, values=(
                g.name,
                g.genre,
                f"{g.hours:.0f}" if g.hours else '',
                g.satisfaction if g.satisfaction is not None else '',
                g.comment,
                g.start_date,
                g.end_date,
            ))

    def _sort_history(self, key):
        if self._history_sort_key == key:
            self._history_sort_rev = not self._history_sort_rev
        else:
            self._history_sort_key = key
            self._history_sort_rev = (key != 'name')
        self._refresh_history()

    def _on_history_dblclick(self, _event):
        sel = self.history_tree.selection()
        if sel and sel[0] in self._history_map:
            self._edit_game(self._history_map[sel[0]])

    # ── Wishlist tab ──────────────────────────────────────────────────────

    def _build_wishlist_tab(self):
        bar = ttk.Frame(self.tab_wishlist, padding=5)
        bar.pack(fill=tk.X)
        ttk.Button(bar, text="+ 위시리스트 추가",
                   command=self._add_wishlist).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text="플레이 시작",
                   command=self._start_playing_wishlist).pack(side=tk.LEFT, padx=2)
        ttk.Separator(bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)
        ttk.Label(bar, text="정렬:").pack(side=tk.LEFT)
        for text, key in [("이름", 'name'), ("가격", 'price'),
                          ("우선순위", 'priority'), ("장르", 'genre')]:
            ttk.Button(bar, text=text,
                       command=lambda k=key: self._sort_wishlist(k)).pack(side=tk.LEFT, padx=2)

        tree_frame = ttk.Frame(self.tab_wishlist)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        cols = ('name', 'genre', 'price', 'priority')
        self.wishlist_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode='browse')
        heads = {'name': '게임명', 'genre': '장르', 'price': '가격', 'priority': '우선순위'}
        widths = {'name': 280, 'genre': 200, 'price': 100, 'priority': 80}
        anchors = {'price': 'e', 'priority': 'center'}

        for c in cols:
            self.wishlist_tree.heading(c, text=heads[c])
            self.wishlist_tree.column(c, width=widths.get(c, 100),
                                      minwidth=50, anchor=anchors.get(c, 'w'))

        sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.wishlist_tree.yview)
        self.wishlist_tree.configure(yscrollcommand=sb.set)
        self.wishlist_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        sb.pack(fill=tk.Y, side=tk.RIGHT)

        self.wishlist_tree.bind('<Double-1>', self._on_wishlist_dblclick)
        self._wishlist_map: dict[str, Game] = {}
        self._wishlist_sort_key = 'name'
        self._wishlist_sort_rev = False

    def _refresh_wishlist(self):
        self.wishlist_tree.delete(*self.wishlist_tree.get_children())
        self._wishlist_map.clear()
        games = self.db.by_status('wishlist')

        key = self._wishlist_sort_key
        rev = self._wishlist_sort_rev

        def sort_val(g):
            v = getattr(g, key)
            if key == 'price':
                return v if v is not None else (-1 if rev else 999999)
            if key == 'priority':
                order = {'high': 0, 'mid': 1, 'low': 2, '': 3}
                return order.get(v, 3)
            return v or ''

        games.sort(key=sort_val, reverse=rev)

        for i, g in enumerate(games):
            iid = f'w{i}'
            self._wishlist_map[iid] = g
            price_text = f"{g.price:,.0f}" if g.price else ''
            self.wishlist_tree.insert('', 'end', iid=iid, values=(
                g.name, g.genre, price_text, g.priority,
            ))

    def _sort_wishlist(self, key):
        if self._wishlist_sort_key == key:
            self._wishlist_sort_rev = not self._wishlist_sort_rev
        else:
            self._wishlist_sort_key = key
            self._wishlist_sort_rev = (key == 'price')
        self._refresh_wishlist()

    def _on_wishlist_dblclick(self, _event):
        sel = self.wishlist_tree.selection()
        if sel and sel[0] in self._wishlist_map:
            self._edit_game(self._wishlist_map[sel[0]])

    # ── Others tab ────────────────────────────────────────────────────────

    def _build_others_tab(self):
        bar = ttk.Frame(self.tab_others, padding=5)
        bar.pack(fill=tk.X)
        ttk.Button(bar, text="재개 (Playing으로)",
                   command=self._resume_from_others).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text="편집",
                   command=self._edit_from_others).pack(side=tk.LEFT, padx=2)
        ttk.Button(bar, text="삭제",
                   command=self._delete_from_others).pack(side=tk.LEFT, padx=2)

        tree_frame = ttk.Frame(self.tab_others)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        cols = ('name', 'status', 'genre', 'hours', 'satisfaction', 'comment')
        self.others_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode='browse')
        heads = {'name': '게임명', 'status': '상태', 'genre': '장르',
                 'hours': '시간', 'satisfaction': '만족도', 'comment': '코멘트'}
        widths = {'name': 200, 'status': 80, 'genre': 180,
                  'hours': 60, 'satisfaction': 60, 'comment': 300}
        anchors = {'status': 'center', 'hours': 'e', 'satisfaction': 'center'}

        for c in cols:
            self.others_tree.heading(c, text=heads[c])
            self.others_tree.column(c, width=widths.get(c, 100),
                                    minwidth=50, anchor=anchors.get(c, 'w'))

        sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.others_tree.yview)
        self.others_tree.configure(yscrollcommand=sb.set)
        self.others_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        sb.pack(fill=tk.Y, side=tk.RIGHT)

        self.others_tree.bind('<Double-1>', self._on_others_dblclick)
        self._others_map: dict[str, Game] = {}

    def _refresh_others(self):
        self.others_tree.delete(*self.others_tree.get_children())
        self._others_map.clear()
        games = self.db.by_status('paused', 'dropped', 'other')
        games.sort(key=lambda g: (g.status, g.name))

        for i, g in enumerate(games):
            iid = f'o{i}'
            self._others_map[iid] = g
            self.others_tree.insert('', 'end', iid=iid, values=(
                g.name,
                g.status,
                g.genre,
                f"{g.hours:.0f}" if g.hours else '',
                g.satisfaction if g.satisfaction is not None else '',
                g.comment,
            ))

    def _on_others_dblclick(self, _event):
        sel = self.others_tree.selection()
        if sel and sel[0] in self._others_map:
            self._edit_game(self._others_map[sel[0]])

    def _get_selected_other(self):
        sel = self.others_tree.selection()
        if not sel:
            messagebox.showwarning("선택 필요", "게임을 선택해주세요.")
            return None
        return self._others_map.get(sel[0])

    def _resume_from_others(self):
        game = self._get_selected_other()
        if not game:
            return
        dlg = SlotSelectDialog(self.root, game.name)
        if dlg.result:
            game.status = 'playing'
            game.slot = dlg.result
            game.start_date = game.start_date or datetime.now().strftime('%Y%m%d')
            self.db.commit()
            self.refresh_all()

    def _edit_from_others(self):
        game = self._get_selected_other()
        if game:
            self._edit_game(game)

    def _delete_from_others(self):
        game = self._get_selected_other()
        if game and messagebox.askyesno("삭제 확인", f"'{game.name}'을(를) 삭제하시겠습니까?"):
            self.db.remove(game)
            self.refresh_all()

    # ── Refresh all ───────────────────────────────────────────────────────

    def refresh_all(self):
        self._refresh_playing()
        self._refresh_history()
        self._refresh_wishlist()
        self._refresh_others()

        counts = {
            'playing': len(self.db.by_status('playing')),
            'completed': len(self.db.by_status('completed')),
            'wishlist': len(self.db.by_status('wishlist')),
            'others': len(self.db.by_status('paused', 'dropped', 'other')),
        }
        total = len(self.db.games)

        self.nb.tab(0, text=f"  현재 플레이 ({counts['playing']})  ")
        self.nb.tab(1, text=f"  완료 기록 ({counts['completed']})  ")
        self.nb.tab(2, text=f"  위시리스트 ({counts['wishlist']})  ")
        self.nb.tab(3, text=f"  기타 ({counts['others']})  ")

        self.status_var.set(
            f"총 {total}개 | 플레이 중 {counts['playing']} | 완료 {counts['completed']}"
        )

    # ── Actions ───────────────────────────────────────────────────────────

    def _add_game(self):
        AddGameDialog(self.root, self.db, self)

    def _add_wishlist(self):
        AddGameDialog(self.root, self.db, self, default_status='wishlist')

    def _add_hours(self, game: Game):
        dlg = AddHoursDialog(self.root, game)
        if dlg.result is not None:
            game.hours = (game.hours or 0) + dlg.result
            self.db.commit()
            self.refresh_all()

    def _complete_game(self, game: Game):
        dlg = CompleteDialog(self.root, game)
        if dlg.confirmed:
            game.status = 'completed'
            if dlg.satisfaction is not None:
                game.satisfaction = dlg.satisfaction
            if dlg.comment:
                game.comment = dlg.comment
            game.end_date = dlg.end_date
            self.db.commit()
            self.refresh_all()

    def _pause_game(self, game: Game):
        game.status = 'paused'
        self.db.commit()
        self.refresh_all()

    def _start_playing_wishlist(self):
        sel = self.wishlist_tree.selection()
        if not sel:
            messagebox.showwarning("선택 필요", "게임을 선택해주세요.")
            return
        game = self._wishlist_map.get(sel[0])
        if not game:
            return
        dlg = SlotSelectDialog(self.root, game.name)
        if dlg.result:
            game.status = 'playing'
            game.slot = dlg.result
            game.start_date = datetime.now().strftime('%Y%m%d')
            self.db.commit()
            self.refresh_all()

    def _edit_game(self, game: Game):
        EditGameDialog(self.root, game, self.db, self)

    def _save(self):
        self.db.save()
        messagebox.showinfo("저장 완료", f"CSV 파일이 저장되었습니다.\n{self.db.path}")

    def _reload(self):
        self.db.load()
        self.refresh_all()
        messagebox.showinfo("불러오기 완료", "CSV 파일을 다시 불러왔습니다.")

    # ── Run ───────────────────────────────────────────────────────────────

    def run(self):
        self.root.mainloop()
