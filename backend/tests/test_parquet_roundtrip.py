from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pyarrow as pa
import pyarrow.parquet as pq


def test_parquet_roundtrip_preserves_schema_and_core_types(tmp_path):
    schema = pa.schema(
        [
            pa.field("observed_at", pa.timestamp("us", tz="Asia/Shanghai")),
            pa.field("close_price", pa.decimal128(18, 4)),
            pa.field("volume", pa.int64()),
            pa.field("quality_note", pa.string()),
        ]
    )
    table = pa.Table.from_arrays(
        [
            pa.array(
                [
                    datetime(2026, 7, 1, 9, 30, tzinfo=ZoneInfo("Asia/Shanghai")),
                    datetime(2026, 7, 1, 9, 31, tzinfo=ZoneInfo("Asia/Shanghai")),
                ],
                type=schema.field("observed_at").type,
            ),
            pa.array(
                [Decimal("12.3400"), Decimal("12.3500")],
                type=schema.field("close_price").type,
            ),
            pa.array([1000, 2000], type=schema.field("volume").type),
            pa.array(["ok", None], type=schema.field("quality_note").type),
        ],
        schema=schema,
    )

    parquet_path = tmp_path / "bars.parquet"
    pq.write_table(table, parquet_path)

    restored = pq.read_table(parquet_path)

    assert restored.schema == schema
    assert restored.column("observed_at").type.tz == "Asia/Shanghai"
    assert restored.column("close_price").type == pa.decimal128(18, 4)
    assert restored.column("volume").type == pa.int64()
    assert restored.column("quality_note").to_pylist() == ["ok", None]
