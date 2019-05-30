# Auto save/load dicts. Not exactly optimal, but good enough
import asyncio
import shelve

SHELF_NAME = "stored_data"
SHELF_LOCK = asyncio.Lock()

# Auto opens shelves when needed
class PersistentObject:
    def __init__(self, name):
        self.name = name

    def get(self, key, default):
        async with SHELF_LOCK:
            with shelve.open(SHELF_NAME) as db:
                return db.get(self.name, default)

    def set(self, key, val):
        async with self.lock:
            with shelve.open(self.name) as db:
                return db.set(key, val)


already_open = {}


def get_persistent(name):
    if name in already_open:
        return already_open[name]
    else:
        return _PersistentDict(name)
