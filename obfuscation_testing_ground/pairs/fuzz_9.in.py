from dataclasses import dataclass, asdict
@dataclass
class P0:
    x: int = 3
    y: int = 4
nm0 = len(asdict(P0())) * 11 + P0().x

from dataclasses import dataclass, asdict
@dataclass
class P1:
    x: int = 3
    y: int = 4
nm1 = len(asdict(P1())) * 11 + P1().x

print(nm0 + nm1)
