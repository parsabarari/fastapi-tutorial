class ItemNotFoundError(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id


class DuplicateItemError(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id
