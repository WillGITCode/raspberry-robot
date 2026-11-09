from dataclasses import dataclass


@dataclass(frozen=True)
class DriveCommand:
    left: float  # -1..1
    right: float  # -1..1
    source: str
    time: float  # clock time the command was issued

    def __post_init__(self):
        for v in (self.left, self.right):
            if not -1.0 <= v <= 1.0:
                raise ValueError(f"speed out of range: {v}")
