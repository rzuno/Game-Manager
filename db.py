"""Game database — CSV CRUD operations."""

import csv
import os
from dataclasses import dataclass
from typing import List, Optional

COLUMNS = [
    'name', 'status', 'slot', 'genre', 'hours', 'satisfaction',
    'comment', 'start_date', 'end_date', 'price', 'priority',
]

STATUSES = ['playing', 'completed', 'paused', 'dropped', 'wishlist', 'other']
SLOTS = ['AAA', 'AA', 'A', '-']
PRIORITIES = ['high', 'mid', 'low', '']

# Marker rows from the original Excel (not real games)
_MARKER_NAMES = frozenset({'구매완료', '확정', '다음 기회에', '보류', '노고'})


def _parse_float(s: str) -> Optional[float]:
    s = (s or '').strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _fmt(val: Optional[float]) -> str:
    if val is None:
        return ''
    return str(int(val)) if val == int(val) else str(val)


@dataclass
class Game:
    name: str = ''
    status: str = ''
    slot: str = '-'
    genre: str = ''
    hours: Optional[float] = None
    satisfaction: Optional[float] = None
    comment: str = ''
    start_date: str = ''
    end_date: str = ''
    price: Optional[float] = None
    priority: str = ''

    def to_row(self) -> dict:
        return {
            'name': self.name,
            'status': self.status,
            'slot': self.slot,
            'genre': self.genre,
            'hours': _fmt(self.hours),
            'satisfaction': _fmt(self.satisfaction),
            'comment': self.comment,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'price': _fmt(self.price),
            'priority': self.priority,
        }


class GameDB:
    def __init__(self, path: str):
        self.path = path
        self.games: List[Game] = []
        self._markers: List[dict] = []

    def load(self):
        self.games.clear()
        self._markers.clear()
        if not os.path.exists(self.path):
            return
        with open(self.path, encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                name = (row.get('name') or '').strip()
                if not name:
                    continue
                if name in _MARKER_NAMES:
                    self._markers.append(row)
                    continue
                self.games.append(Game(
                    name=name,
                    status=(row.get('status') or '').strip(),
                    slot=(row.get('slot') or '-').strip() or '-',
                    genre=(row.get('genre') or '').strip(),
                    hours=_parse_float(row.get('hours', '')),
                    satisfaction=_parse_float(row.get('satisfaction', '')),
                    comment=(row.get('comment') or '').strip(),
                    start_date=(row.get('start_date') or '').strip(),
                    end_date=(row.get('end_date') or '').strip(),
                    price=_parse_float(row.get('price', '')),
                    priority=(row.get('priority') or '').strip(),
                ))

    def save(self):
        with open(self.path, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            for g in self.games:
                w.writerow(g.to_row())
            for m in self._markers:
                w.writerow(m)

    def add(self, game: Game):
        self.games.append(game)
        self.save()

    def remove(self, game: Game):
        if game in self.games:
            self.games.remove(game)
            self.save()

    def commit(self):
        self.save()

    def by_status(self, *statuses: str) -> List[Game]:
        return [g for g in self.games if g.status in statuses]
