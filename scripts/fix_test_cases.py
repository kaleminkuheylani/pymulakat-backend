#!/usr/bin/env python3
"""CSV test_cases düzeltme - 23 pending soru için input formatı imzaya uygun."""
import csv
import json

FIXES = {
    "34": [
        {"input": {"muz": 3, "elma": 5, "armut": 8}, "expected": {"avg": 5.33, "max": 8, "min": 3}, "description": "3 urun"},
        {"input": {"tek": 10}, "expected": {"avg": 10, "max": 10, "min": 10}, "description": "tek urun"},
        {"input": {}, "expected": None, "description": "bos sozluk"},
    ],
    "39": [
        {"input": {"d1": 10, "d2": 20, "d3": 30, "d4": 40, "d5": 50, "d6": 60, "d7": 70, "d8": 80}, "expected": [40.0, 80.0], "description": "8 gun 2 hafta"},
        {"input": {"d1": 7, "d2": 7, "d3": 7, "d4": 7, "d5": 7, "d6": 7, "d7": 7}, "expected": [7.0], "description": "tam 1 hafta"},
        {"input": {}, "expected": [], "description": "bos veri"},
    ],
    "68": [
        {"input": [{"ali": 80000, "ayse": 75000}, {"ayse": 72000, "mehmet": 70000}], "expected": {"ali": 80000, "ayse": 72000, "mehmet": 70000}, "description": "catisma ikinci kazanir"},
        {"input": [{"a": 1}, {"b": 2}], "expected": {"a": 1, "b": 2}, "description": "ayrik alanlar"},
    ],
    "70": [
        {"input": [8, [1, 2, 3, 4, 5]], "expected": [3, 5], "description": "target 8"},
        {"input": [10, [1, 2, 3, 4]], "expected": [3, 4] if abs(3+4-10)==3 else [4, 4], "description": "target 10"},
    ],
    "71": [
        {"input": "aabbbcccddaaa", "expected": ["b", 3], "description": "aabbbcccddaaa"},
        {"input": "abcdef", "expected": ["a", 1], "description": "unique chars"},
        {"input": "aaaaa", "expected": ["a", 5], "description": "5 a"},
        {"input": "", "expected": ["", 0], "description": "bos string"},
    ],
    "85": [
        {"input": ["Merhaba", "Araba"], "expected": ["a", "r"], "description": "2 string"},
        {"input": ["Python", "Java"], "expected": ["a"], "description": "2 string"},
    ],
    "88": [
        {"input": [[2, 7, 11, 15], 9], "expected": [[2, 7]], "description": "target 9"},
        {"input": [[1, 5, 3, 7, 9], 12], "expected": [[3, 9], [5, 7]], "description": "target 12"},
        {"input": [[1, 2, 3], 10], "expected": [], "description": "hedef yok"},
    ],
    "114": [
        {"input": [["A", "elma"], ["A", "armut"], ["B", "muz"]], "expected": {"A": ["elma", "armut"], "B": ["muz"]}, "description": "tipik"},
    ],
    "116": [
        {"input": 5, "expected": [0, 1, 2, 3, 4], "description": "n=5"},
        {"input": 0, "expected": [], "description": "n=0"},
    ],
    "127": [
        {"input": [{"a": 1, "b": 3}, {"a": 2, "b": 4}], "expected": [{"a": 0.25, "b": 0.75}, {"a": 0.333, "b": 0.667}], "description": "2 satir normalize"},
    ],
    "130": [
        {"input": [{"name": "Ali", "category": "A"}, {"name": "Veli", "category": None}, {"name": "Ayse", "category": "A"}], "expected": [{"name": "Ali", "category": "A"}, {"name": "Veli", "category": "A"}, {"name": "Ayse", "category": "A"}], "description": "3 kayit 1 null"},
    ],
    "133": [
        {"input": [[1, 2, 3, 4, 5], [3, 4, 5, 6]], "expected": [3, 4, 5], "description": "kesisim sirayla"},
    ],
    "134": [
        {"input": {"a": 1, "b": 2, "c": 3}, "expected": {"1": "a", "2": "b", "3": "c"}, "description": "3 anahtar"},
        {"input": {"x": "y"}, "expected": {"y": "x"}, "description": "tek anahtar"},
    ],
    "136": [
        {"input": [[3, 2, 0, -4], 1], "expected": True, "description": "pos 1 cycle"},
        {"input": [[1, 2], 0], "expected": True, "description": "pos 0 cycle"},
        {"input": [[1], -1], "expected": False, "description": "no cycle"},
    ],
    "139": [
        {"input": [{"a": 1, "b": None}, {"a": None, "b": 2}, {"a": 3, "b": 4}], "expected": {"a": 1, "b": 1}, "description": "NaN sayimi"},
    ],
    "141": [
        {"input": [["LRUCache", 2], ["put", 1, 1], ["put", 2, 2], ["get", 1], ["put", 3, 3], ["get", 2], ["put", 4, 4], ["get", 1]], "expected": [None, None, None, 1, None, -1, None, -1], "description": "klasik LRU"},
    ],
    "157": [
        {"input": [["MedianFinder"], ["addNum", 1], ["addNum", 2], ["findMedian"], ["addNum", 3], ["findMedian"]], "expected": [None, None, None, 1.5, None, 2.0], "description": "medyan"},
    ],
    "161": [
        {"input": [[4, 10, 15, 24, 26], [0, 9, 12, 20], [5, 18, 22, 30]], "expected": [20, 24], "description": "3 liste kesisim"},
    ],
    "163": [
        {"input": [["MinStack"], ["push", -2], ["push", 0], ["push", -3], ["getMin"], ["pop"], ["top"], ["getMin"]], "expected": [None, None, None, -3, None, 0, -2], "description": "min stack"},
    ],
    "167": [
        {"input": [["MyQueue"], ["push", 1], ["push", 2], ["peek"], ["pop"], ["empty"]], "expected": [None, None, None, 1, 1, False], "description": "queue stack ile"},
    ],
    "169": [
        {"input": [["CircularQueue", 3], ["enQueue", 1], ["enQueue", 2], ["enQueue", 3], ["enQueue", 4], ["Rear"], ["isFull"], ["deQueue"], ["enQueue", 4], ["Front"]], "expected": [None, True, True, True, False, 3, True, None, True, 4], "description": "circular queue"},
    ],
    "170": [
        {"input": [["RecentCounter"], ["ping", 1], ["ping", 100], ["ping", 3001], ["ping", 3002]], "expected": [None, 1, 2, 3, 3], "description": "son 3000ms"},
    ],
    "171": [
        {"input": [["MovingAverage", 3], ["next", 1], ["next", 10], ["next", 3], ["next", 5]], "expected": [None, 1.0, 5.5, 4.6667, 6.0], "description": "k=3 moving avg"},
    ],
}


def main():
    with open("data/QUESTIONS-v3.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

    header = rows[0]
    id_idx = header.index("id")
    tc_idx = header.index("test_cases")

    changes = 0
    for row in rows[1:]:
        if len(row) > id_idx and row[id_idx].strip() in FIXES:
            sid = row[id_idx].strip()
            new_tc = json.dumps(FIXES[sid], ensure_ascii=False)
            new_tc_q = new_tc.replace('"', '""')
            if row[tc_idx] != new_tc_q:
                row[tc_idx] = new_tc_q
                changes += 1
                print(f"  ok id={sid}: test_cases guncellendi ({len(FIXES[sid])} test)")

    print(f"\nToplam: {changes} degisiklik")

    with open("data/QUESTIONS-v3.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerows(rows)
    print("ok CSV guncellendi")


if __name__ == "__main__":
    main()
