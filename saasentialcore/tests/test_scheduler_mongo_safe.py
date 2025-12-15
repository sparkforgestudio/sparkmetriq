from __future__ import annotations

import pytest
from datetime import datetime

from enum import Enum
from pydantic import BaseModel

from saasentialcore.services.scheduler_service import SchedulerService


class MyEnum(Enum):
    A = "A"
    B = "B"


class MyModel(BaseModel):
    x: int
    y: str


def test_to_mongo_safe_converts_enum_and_basemodel_and_collections():
    naive_dt = datetime(2024, 1, 1, 12, 0, 0)
    model = MyModel(x=1, y="test")

    value = {
        "enum": MyEnum.A,
        "model": model,
        "list": [MyEnum.B, model],
        "set": {MyEnum.A, MyEnum.B},
        "tuple": (model, MyEnum.B),
        "dt": naive_dt,
    }

    safe = SchedulerService._to_mongo_safe(value)

    assert safe["enum"] == "A"
    assert safe["model"]["x"] == 1
    assert safe["model"]["y"] == "test"
    assert safe["list"][0] == "B" or safe["list"][1] == "B"
    assert isinstance(safe["dt"], datetime)
    assert safe["dt"].tzinfo is not None  # converti en UTC


def test_to_mongo_safe_converts_exception_to_string():
    exc = RuntimeError("boom")
    safe = SchedulerService._to_mongo_safe(exc)
    assert safe == "boom"
