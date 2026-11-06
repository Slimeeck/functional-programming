from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from core import (
    add_tag,
    apply_clearance_discount,
    by_tag,
    change_price,
    create_example_stock,
    freeze,
    index_by_record,
    records_to_reorder,
    remove_tag,
    restock,
    ship,
    supplier_name,
    top_by_value,
    total_inventory_value,
    update_supplier,
)
from model import Movement, Product, StockRecord, make_meta


def make_record() -> StockRecord:
    """Щоразу будує НОВИЙ, але рівний (==) запис.

    deepcopy тут не використовується: MappingProxyType не копіюється pickle-ом,
    а для незмінних об'єктів «захисні копії» і не потрібні.
    """
    return StockRecord(
        Product("EL-002", "Клавіатура", 1000.0, "electronics"),
        quantity=5,
        tags=frozenset({"clearance"}),
        supplier=make_meta(name="ТОВ Техно", country="UA"),
    )


@pytest.fixture
def record() -> StockRecord:
    return make_record()


# --- незмінність моделі --------------------------------------------------
def test_frozen_fields_cannot_be_assigned(record: StockRecord) -> None:
    with pytest.raises(FrozenInstanceError):
        record.quantity = 100  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        record.product.price = 1.0  # type: ignore[misc]


def test_collection_types_are_immutable(record: StockRecord) -> None:
    assert isinstance(record.tags, frozenset)
    assert isinstance(record.history, tuple)
    assert isinstance(record.supplier, MappingProxyType)


def test_slots_no_dict(record: StockRecord) -> None:
    assert not hasattr(record, "__dict__")


def test_mappingproxy_is_read_only(record: StockRecord) -> None:
    with pytest.raises(TypeError):
        record.supplier["name"] = "changed"  # type: ignore[index]


def test_make_meta_copies_source() -> None:
    source = {"name": "A"}
    meta = make_meta(**source)
    source["name"] = "B"  # зміна джерела не видна через proxy
    assert meta["name"] == "A"


def test_validation() -> None:
    with pytest.raises(ValueError):
        Product("X", "x", -1.0, "c")
    with pytest.raises(ValueError):
        StockRecord(Product("X", "x", 1.0, "c"), quantity=-1)


# --- pure updates --------------------------------------------------------
def test_restock_returns_new_copy(record: StockRecord) -> None:
    snapshot = make_record()
    new = restock(record, 10, "поставка")
    assert new is not record
    assert record == snapshot  # оригінал без змін
    assert new.quantity == 15
    assert new.history == (Movement("in", 10, "поставка"),)
    assert new.value() == record.value() + 10 * 1000.0


def test_ship(record: StockRecord) -> None:
    assert ship(record, 2).quantity == 3
    with pytest.raises(ValueError):
        ship(record, 99)
    with pytest.raises(ValueError):
        restock(record, 0)


def test_change_price_creates_new_product(record: StockRecord) -> None:
    new = change_price(record, 1200.0)
    assert new.product is not record.product
    assert new.product.price == 1200.0
    assert record.product.price == 1000.0
    assert new.history[-1].kind == "price"


def test_add_and_remove_tag(record: StockRecord) -> None:
    tagged = add_tag(record, "  Promo ")
    assert tagged.tags == frozenset({"clearance", "promo"})
    assert record.tags == frozenset({"clearance"})
    assert remove_tag(tagged, "promo").tags == record.tags
    with pytest.raises(ValueError):
        add_tag(record, "   ")


def test_update_supplier(record: StockRecord) -> None:
    new = update_supplier(record, phone="+380")
    assert dict(new.supplier) == {"name": "ТОВ Техно", "country": "UA", "phone": "+380"}
    assert "phone" not in record.supplier
    assert isinstance(new.supplier, MappingProxyType)


def test_clearance_discount_rule(record: StockRecord) -> None:
    assert apply_clearance_discount(record, 0.25).product.price == 750.0
    plain = remove_tag(record, "clearance")
    assert apply_clearance_discount(plain, 0.25) is plain  # правило не діє
    with pytest.raises(ValueError):
        apply_clearance_discount(record, 1.5)


def test_chain_of_updates_keeps_every_version(record: StockRecord) -> None:
    v1 = restock(record, 1)
    v2 = add_tag(v1, "new")
    v3 = change_price(v2, 10.0)
    assert [v.quantity for v in (record, v1, v2, v3)] == [5, 6, 6, 6]
    assert len({id(v) for v in (record, v1, v2, v3)}) == 4


# --- хешованість ---------------------------------------------------------
def test_hashability(record: StockRecord) -> None:
    records = {record, restock(record, 1), make_record()}
    assert len(records) == 2  # копія з тим самим вмістом == оригінал
    assert record is not make_record()
    assert hash(record) == hash(make_record())
    assert index_by_record([record])[record] == "EL-002"


def test_mappingproxy_itself_is_not_hashable(record: StockRecord) -> None:
    # саме тому поле supplier виключене з hash (field(hash=False))
    with pytest.raises(TypeError):
        hash(record.supplier)


# --- запити та кешування -------------------------------------------------
def test_queries() -> None:
    stock = create_example_stock()
    assert [r.product.sku for r in records_to_reorder(stock, 5)] == ["EL-002", "OF-011"]
    assert [r.product.sku for r in by_tag(stock, "bulk")] == ["OF-010"]
    assert top_by_value(stock, 1)[0].product.sku == "EL-001"
    assert supplier_name(stock[2].supplier) == "Office Group"
    assert supplier_name(make_meta()) == "unknown"


def test_lru_cache_on_pure_function() -> None:
    stock = create_example_stock()
    total_inventory_value.cache_clear()
    first = total_inventory_value(stock)
    second = total_inventory_value(stock)
    info = total_inventory_value.cache_info()
    assert first == second == 98400 + 4050 + 36400 + 360
    assert info.hits == 1 and info.misses == 1


# --- глибоке заморожування -----------------------------------------------
def test_freeze_deep() -> None:
    raw = {"tags": {"a", "b"}, "items": [1, [2, 3]], "meta": {"k": ["v"]}}
    frozen = freeze(raw)
    assert isinstance(frozen, MappingProxyType)
    assert frozen["tags"] == frozenset({"a", "b"})
    assert frozen["items"] == (1, (2, 3))
    assert frozen["meta"]["k"] == ("v",)
    raw["items"].append(99)  # type: ignore[attr-defined]
    assert frozen["items"] == (1, (2, 3))  # копія не залежить від оригіналу
