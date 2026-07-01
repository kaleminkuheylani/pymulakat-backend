# services/skills.py
# Topic tree — hard-coded skill graph for Python mülakat hazırlığı.
# Her question `topics: List[str]` ile bu node'lardan birine bağlanır.
# Lint: services/skills_lint.py — orphan / duplicate / missing mapping.

from typing import Dict, List, Set

# ═══════════════════════════════════════════════════════════
# Topic graph
# categories ↔ topics ↔ subskills (3 katman)
# ═══════════════════════════════════════════════════════════

SKILL_GRAPH: Dict[str, Dict[str, List[str]]] = {
    "python-basics": {
        "variables": ["assignment", "naming", "scope"],
        "control_flow": ["if_else", "loops", "comprehensions"],
        "functions": ["definition", "args_kwargs", "lambdas", "closures"],
        "data_types": ["int_float", "str_bool", "type_hints"],
        "operators": ["arithmetic", "comparison", "logical", "membership"],
    },
    "strings": {
        "slicing": ["basic_slice", "stride", "reverse"],
        "methods": ["split_join", "replace", "strip_lower_upper"],
        "formatting": ["fstring", "format_method", "percent"],
        "regex": ["pattern_match", "groups", "sub"],
    },
    "list-dict": {
        "lists": ["append_extend", "list_comp", "sorting"],
        "tuples": ["packing", "unpacking", "immutable"],
        "sets": ["unique", "set_ops"],
        "dicts": ["get_setdefault", "dict_comp", "iteration"],
    },
    "oop": {
        "classes": ["init_self", "attributes_methods", "classmethods"],
        "inheritance": ["single", "multiple", "mro"],
        "magic_methods": ["__str__", "__repr__", "__eq__", "__iter__"],
        "encapsulation": ["public_private", "properties"],
    },
    "algorithms": {
        "sorting": ["bubble", "selection", "merge", "quick"],
        "searching": ["linear", "binary"],
        "recursion": ["base_case", "recursive_case", "memoization"],
        "complexity": ["big_o", "space_complexity"],
    },
    "pandas": {
        "dataframe": ["creation", "selection", "filtering"],
        "io": ["csv", "json", "excel"],
        "transform": ["groupby", "merge", "pivot"],
        "viz": ["plot", "histogram"],
    },
    "numpy": {
        "arrays": ["creation", "reshaping", "slicing"],
        "ufuncs": ["broadcasting", "reduction"],
    },
    "sqlite3": {
        "queries": ["select", "insert_update_delete", "joins"],
        "schema": ["create_table", "indexes"],
    },
    "data-types": {
        "collections": ["counter", "defaultdict", "namedtuple", "deque"],
    },
    "beyin-firtinasi": {
        "logic": ["puzzles", "patterns"],
    },
    "simple-apps": {
        "cli": ["argparse", "input_loop"],
    },
}


def all_topics() -> List[str]:
    """Tüm topic'leri düz liste olarak döndür."""
    out: List[str] = []
    for cat, topics in SKILL_GRAPH.items():
        for topic in topics.keys():
            out.append(f"{cat}.{topic}")
    return out


def all_subskills() -> List[str]:
    """Tüm subskill'leri düz liste olarak döndür."""
    out: List[str] = []
    for cat, topics in SKILL_GRAPH.items():
        for topic, subs in topics.items():
            for sub in subs:
                out.append(f"{cat}.{topic}.{sub}")
    return out


def parse_topic(path: str) -> tuple:
    """'oop.inheritance.single' → ('oop', 'inheritance', 'single')."""
    parts = path.split(".")
    if len(parts) == 2:
        return parts[0], parts[1], None
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    return None, None, None


def is_valid_topic(path: str) -> bool:
    """Verilen topic yolu SKILL_GRAPH'te tanımlı mı?"""
    cat, topic, sub = parse_topic(path)
    if cat not in SKILL_GRAPH:
        return False
    if topic not in SKILL_GRAPH[cat]:
        return False
    if sub is not None and sub not in SKILL_GRAPH[cat][topic]:
        return False
    return True


def is_valid_topic_set(topics: List[str]) -> tuple:
    """Bir question'ın topics listesi geçerli mi?
    Döner: (ok: bool, invalid: List[str], orphans: List[str])"""
    invalid = [t for t in topics if not is_valid_topic(t)]
    return (len(invalid) == 0, invalid, [])


# ═══════════════════════════════════════════════════════════
# User progress (Supabase'den aggregate)
# ═══════════════════════════════════════════════════════════

def aggregate_user_progress(attempts: List[dict]) -> Dict[str, Dict[str, int]]:
    """
    Kullanıcının attempts listesinden topic bazlı progress hesapla.
    Döner: {'oop.inheritance': {'attempted': 3, 'solved': 2, 'failed': 1}, ...}
    """
    sb = _supabase()
    cache: Dict[int, dict] = {}

    progress: Dict[str, Dict[str, int]] = {}
    for a in attempts:
        qid = a.get("question_id")
        if qid not in cache:
            res = sb.table("interwiews").select("topics").eq("id", qid).execute()
            cache[qid] = (res.data[0].get("topics") or []) if res.data else []
        topics = cache[qid]
        success = a.get("success", False)
        for t in topics:
            d = progress.setdefault(t, {"attempted": 0, "solved": 0, "failed": 0})
            d["attempted"] += 1
            if success:
                d["solved"] += 1
            else:
                d["failed"] += 1
    return progress


def _supabase():
    from supabase_client import get_supabase_admin
    return get_supabase_admin()