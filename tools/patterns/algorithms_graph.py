"""Graph algorithms patterns."""
from ._shared import tcs

PATTERN = {
    "level": "advanced",
    "templates": [
        {
            "title": "BFS Shortest Path",
            "description": (
                "İstanbul metro ağı unweighted graph: A'dan D'ye en kısa kaç "
                "istasyon? BFS ile en kısa path uzunluğunu bul. Path yoksa -1."
            ),
            "starter": (
                "from collections import deque\n\n"
                "def bfs_shortest_path(graph, start, end):\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"graph": {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}, "start": "A", "end": "D"}, "expected": 2},
                    {"input": {"graph": {"A": []}, "start": "A", "end": "A"}, "expected": 0},
                    {"input": {"graph": {str(i): [str(i+1)] for i in range(100)}, "start": "0", "end": "99"}, "expected": 99},
                    {"input": {"graph": {"A": ["B"], "B": ["A"]}, "start": "A", "end": "C"}, "expected": -1},
                    {"input": {"graph": {}, "start": "X", "end": "Y"}, "expected": -1},
                )},
                {"cases": tcs(
                    {"input": {"graph": {"A": ["B"], "B": ["C"], "C": ["A"]}, "start": "A", "end": "C"}, "expected": 2},
                    {"input": {"graph": {"A": []}, "start": "A", "end": "B"}, "expected": -1},
                    {"input": {"graph": {str(i): [str(i+1), str(i+2)] for i in range(50)}, "start": "0", "end": "49"}, "expected": 25},
                    {"input": {"graph": {"A": ["A"]}, "start": "A", "end": "A"}, "expected": 0},
                    {"input": {"graph": {"A": ["B"]}, "start": "A", "end": "B"}, "expected": 1},
                )},
            ],
            "hints": [
                "💡 `collections.deque` ile BFS queue (O(1) popleft)",
                "💡 `visited` set ile cycle önle",
                "💡 Level-order: distance'ı node ile birlikte tut",
            ],
            "explanation": (
                "BFS: queue'ya (start, 0) ekle. Çıkar, eğer end ise distance dön. "
                "Değilse tüm neighbor'ları visited değilse queue'ya (nbr, "
                "distance+1) ekle. Queue boşalırsa -1. start == end → 0 (edge case)."
            ),
            "complexity": "O(V + E) time, O(V) space",
            "concepts": ["BFS", "graph", "shortest-path", "queue", "unweighted"],
            "tags": ["graph", "BFS", "algorithms"],
        },
        {
            "title": "DFS Cycle Detection",
            "description": (
                "DB migration dependency: A → B → C → A ise circular dependency. "
                "Directed graph'ta cycle var mı tespit et (DFS + 3-renk: white/gray/black)."
            ),
            "starter": (
                "def has_cycle(graph):\n"
                "    # DFS 3-renk: white (ziyaret yok), gray (şu anki path'te), \n"
                "    # black (tamamlandı)\n"
                "    pass"
            ),
            "tests_by_seed": [
                {"cases": tcs(
                    {"input": {"graph": {"A": ["B"], "B": ["C"], "C": ["A"]}}, "expected": True},
                    {"input": {"graph": {"A": ["B"], "B": ["C"], "C": []}}, "expected": False},
                    {"input": {"graph": {str(i): [str(i+1)] for i in range(100)} | {"99": ["0"]}}, "expected": True},
                    {"input": {"graph": {"A": ["A"]}}, "expected": True},
                    {"input": {"graph": {}}, "expected": False},
                )},
                {"cases": tcs(
                    {"input": {"graph": {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}}, "expected": False},
                    {"input": {"graph": {"A": ["B"], "B": ["A"]}}, "expected": True},
                    {"input": {"graph": {str(i): [str((i+1) % 50)] for i in range(50)}}, "expected": True},
                    {"input": {"graph": {"X": [], "Y": [], "Z": []}}, "expected": False},
                    {"input": {"graph": {"A": ["B"], "B": ["C"], "C": ["B"]}}, "expected": True},
                )},
            ],
            "hints": [
                "💡 Gray node'a tekrar ulaşırsan cycle var (back edge)",
                "💡 `WHITE=0, GRAY=1, BLACK=2` enum",
                "💡 Recursive DFS veya iterative stack",
            ],
            "explanation": (
                "DFS'te her node white başlar. Ziyaret edince gray, tamamlayınca black. "
                "Eğer gray bir node'a edge varsa → cycle (back edge). Self-loop da "
                "cycle (gray → self edge). O(V+E)."
            ),
            "complexity": "O(V + E) time, O(V) space",
            "concepts": ["DFS", "graph", "cycle-detection", "3-color"],
            "tags": ["graph", "DFS", "algorithms"],
        },
    ],
}