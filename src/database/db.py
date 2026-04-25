import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore_async
import os

db = None

def init_db(key_path):
    global db
    if not os.path.exists(key_path):
        print(f"ВНИМАНИЕ: Файл ключа Firebase {key_path} не найден!")
        print("Бот будет работать в режиме мок-базы, или упадет при запросах.")
        class MockDB:
            def __init__(self):
                self.data = {}
                self.current_collection = None
                self.current_doc = None

            def collection(self, name):
                if name not in self.data:
                    self.data[name] = {}
                self.current_collection = self.data[name]
                return self

            def document(self, name):
                self.current_doc = str(name)
                return self

            async def get(self):
                class MockDoc:
                    def __init__(self, exists, data=None):
                        self.exists = exists
                        self._data = data or {}
                    def to_dict(self): return self._data

                if self.current_doc in self.current_collection:
                    return MockDoc(True, self.current_collection[self.current_doc])
                return MockDoc(False)

            async def set(self, data, merge=False):
                if merge and self.current_doc in self.current_collection:
                    self.current_collection[self.current_doc].update(data)
                else:
                    self.current_collection[self.current_doc] = data

            async def update(self, data):
                if self.current_doc in self.current_collection:
                    self.current_collection[self.current_doc].update(data)

            async def stream(self):
                class MockDoc:
                    def __init__(self, data):
                        self._data = data
                    def to_dict(self): return self._data

                for doc_id, data in self.current_collection.items():
                    yield MockDoc(data)
        db = MockDB()
        return db

    cred = credentials.Certificate(key_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore_async.client()
    return db

def get_db():
    return db
