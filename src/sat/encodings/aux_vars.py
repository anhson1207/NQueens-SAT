

class AuxiliaryVariableAllocator:

    def __init__(self, start_id: int):
        if not isinstance(start_id, int) or isinstance(start_id, bool) or start_id < 1:
            raise ValueError("start_id must be a positive integer")
        self._start_id = start_id
        self._next_id = start_id

    def new_var(self) -> int:
        variable = self._next_id
        self._next_id += 1
        return variable

    @property
    def allocated_count(self) -> int:
        return self._next_id - self._start_id

    @property
    def next_id(self) -> int:
        return self._next_id
