"""Allocate consecutive SAT auxiliary IDs above the reserved primary range."""


class AuxiliaryVariableAllocator:
    """Issue unique IDs from start_id; reserve all original IDs below start_id."""

    def __init__(self, start_id: int):
        """Start an empty allocation range at a positive integer ID."""
        if not isinstance(start_id, int) or isinstance(start_id, bool) or start_id < 1:
            raise ValueError("start_id must be a positive integer")
        self._start_id = start_id
        self._next_id = start_id

    def new_var(self) -> int:
        """Return the next unused auxiliary ID and advance the counter."""
        variable = self._next_id
        self._next_id += 1
        return variable

    @property
    def allocated_count(self) -> int:
        """Return how many auxiliary IDs this allocator has issued."""
        return self._next_id - self._start_id

    @property
    def next_id(self) -> int:
        """Return the next available ID without allocating it."""
        return self._next_id
