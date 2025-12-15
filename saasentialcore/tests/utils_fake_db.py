from __future__ import annotations

from typing import Any, Dict, List, Optional


class FakeInsertResult:
    def __init__(self, inserted_id: Any) -> None:
        self.inserted_id = inserted_id


class FakeUpdateResult:
    def __init__(self, modified_count: int) -> None:
        self.modified_count = modified_count


class FakeCursor:
    def __init__(self, docs: List[Dict[str, Any]]) -> None:
        self._docs = docs
        self._limit: Optional[int] = None

    def sort(self, field: str, direction: int) -> "FakeCursor":
        # On peut ignorer direction pour les tests
        self._docs = sorted(
            self._docs,
            key=lambda d: d.get(field),
        )
        return self

    def limit(self, n: int) -> "FakeCursor":
        self._limit = n
        return self

    async def to_list(self, length: Optional[int] = None) -> List[Dict[str, Any]]:
        if self._limit is not None:
            return self._docs[: self._limit]
        return list(self._docs)


class FakeCollection:
    def __init__(self) -> None:
        self._docs: List[Dict[str, Any]] = []

    async def insert_one(self, doc: Dict[str, Any]) -> FakeInsertResult:
        from bson import ObjectId

        # Si pas d'_id, on en crée un
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        self._docs.append(doc)
        return FakeInsertResult(inserted_id=doc["_id"])

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for doc in self._docs:
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return dict(doc)
        return None

    def find(self, query: Dict[str, Any]) -> FakeCursor:
        matched: List[Dict[str, Any]] = []
        for doc in self._docs:
            ok = True
            for k, v in query.items():
                if isinstance(v, dict) and "$lte" in v and "$gte" in v:
                    # gestion simple de range
                    val = doc.get(k)
                    if not (v["$gte"] <= val <= v["$lte"]):
                        ok = False
                        break
                else:
                    if doc.get(k) != v:
                        ok = False
                        break
            if ok:
                matched.append(dict(doc))
        return FakeCursor(matched)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any]) -> FakeUpdateResult:
        modified = 0
        for i, doc in enumerate(self._docs):
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                if "$set" in update:
                    for fk, fv in update["$set"].items():
                        self._docs[i][fk] = fv
                if "$inc" in update:
                    for fk, fv in update["$inc"].items():
                        self._docs[i][fk] = self._docs[i].get(fk, 0) + fv
                modified += 1
                break
        return FakeUpdateResult(modified_count=modified)

    async def delete_many(self, query: Dict[str, Any]) -> FakeUpdateResult:
        """Supprime tous les documents correspondant à la query."""
        deleted = 0
        indices_to_remove = []
        for i, doc in enumerate(self._docs):
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                indices_to_remove.append(i)
                deleted += 1
        # Supprimer en ordre inverse pour ne pas décaler les indices
        for i in reversed(indices_to_remove):
            self._docs.pop(i)
        return FakeUpdateResult(modified_count=deleted)


class FakeDB:
    def __init__(self) -> None:
        self._collections: Dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection()
        return self._collections[name]
