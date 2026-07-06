# Pattern loader — her pattern dosyasını otomatik yükle.
from . import (
    concurrency,
    oop_advanced,
    algorithms_dp,
    algorithms_graph,
    algorithms_recursion,
    standard_library,
    functional,
    design_patterns,
    performance,
    testing,
    real_world,
    python_3_12,
)

PATTERNS = {
    "concurrency": concurrency.PATTERN,
    "oop-advanced": oop_advanced.PATTERN,
    "algorithms-dp": algorithms_dp.PATTERN,
    "algorithms-graph": algorithms_graph.PATTERN,
    "algorithms-recursion": algorithms_recursion.PATTERN,
    "standard-library": standard_library.PATTERN,
    "functional": functional.PATTERN,
    "design-patterns": design_patterns.PATTERN,
    "performance": performance.PATTERN,
    "testing": testing.PATTERN,
    "real-world": real_world.PATTERN,
    "python-3-12": python_3_12.PATTERN,
}

__all__ = ["PATTERNS"]