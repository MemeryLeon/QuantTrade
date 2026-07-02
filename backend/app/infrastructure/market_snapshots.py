from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO
from uuid import uuid4

import pyarrow as pa
import pyarrow.parquet as pq

from app.core.time import utc_now
from app.domains.artifacts import ArtifactPayload, IArtifactStore
from app.domains.data_snapshots import AdjustmentFactor, CompanyAction, DataSnapshot
from app.domains.market import Bar


OHLCV_SCHEMA_VERSION = "ohlcv-parquet-v1"
ADJUSTMENT_FACTOR_SCHEMA_VERSION = "adjustment-factors-parquet-v1"
COMPANY_ACTION_SCHEMA_VERSION = "company-actions-parquet-v1"


class MarketSnapshotStore:
    def __init__(self, artifact_store: IArtifactStore) -> None:
        self._artifact_store = artifact_store

    async def create_ohlcv_snapshot(
        self,
        *,
        source_id: str,
        market: str,
        instrument_scope: str,
        resolution: str,
        adjustment: str,
        timezone_name: str,
        calendar_version: str,
        bars: Sequence[Bar],
    ) -> DataSnapshot:
        if not bars:
            raise ValueError("ohlcv snapshot requires at least one bar")
        table = _ohlcv_table(bars)
        return await self._put_snapshot(
            namespace=f"market-data/{source_id}/{instrument_scope}",
            name="ohlcv.parquet",
            source_id=source_id,
            market=market,
            instrument_scope=instrument_scope,
            resolution=resolution,
            adjustment=adjustment,
            start_time=bars[0].observed_at,
            end_time=bars[-1].observed_at,
            timezone_name=timezone_name,
            calendar_version=calendar_version,
            schema_version=OHLCV_SCHEMA_VERSION,
            row_count=len(bars),
            table=table,
        )

    async def create_adjustment_factor_snapshot(
        self,
        *,
        source_id: str,
        market: str,
        instrument_scope: str,
        timezone_name: str,
        calendar_version: str,
        factors: Sequence[AdjustmentFactor],
    ) -> DataSnapshot:
        if not factors:
            raise ValueError("adjustment factor snapshot requires at least one factor")
        table = _adjustment_factor_table(factors)
        return await self._put_snapshot(
            namespace=f"market-data/{source_id}/{instrument_scope}",
            name="adjustment-factors.parquet",
            source_id=source_id,
            market=market,
            instrument_scope=instrument_scope,
            resolution="daily",
            adjustment="factor",
            start_time=factors[0].effective_date,
            end_time=factors[-1].effective_date,
            timezone_name=timezone_name,
            calendar_version=calendar_version,
            schema_version=ADJUSTMENT_FACTOR_SCHEMA_VERSION,
            row_count=len(factors),
            table=table,
        )

    async def create_company_action_snapshot(
        self,
        *,
        source_id: str,
        market: str,
        instrument_scope: str,
        timezone_name: str,
        calendar_version: str,
        actions: Sequence[CompanyAction],
    ) -> DataSnapshot:
        if not actions:
            raise ValueError("company action snapshot requires at least one action")
        table = _company_action_table(actions)
        return await self._put_snapshot(
            namespace=f"market-data/{source_id}/{instrument_scope}",
            name="company-actions.parquet",
            source_id=source_id,
            market=market,
            instrument_scope=instrument_scope,
            resolution="event",
            adjustment="none",
            start_time=actions[0].effective_date,
            end_time=actions[-1].effective_date,
            timezone_name=timezone_name,
            calendar_version=calendar_version,
            schema_version=COMPANY_ACTION_SCHEMA_VERSION,
            row_count=len(actions),
            table=table,
        )

    async def _put_snapshot(
        self,
        *,
        namespace: str,
        name: str,
        source_id: str,
        market: str,
        instrument_scope: str,
        resolution: str,
        adjustment: str,
        start_time: datetime,
        end_time: datetime,
        timezone_name: str,
        calendar_version: str,
        schema_version: str,
        row_count: int,
        table: pa.Table,
    ) -> DataSnapshot:
        payload = ArtifactPayload(content=_parquet_bytes(table), content_type="application/parquet")
        reference = await self._artifact_store.put(namespace, name, payload)
        return DataSnapshot(
            id=str(uuid4()),
            source_id=source_id,
            market=market,
            instrument_scope=instrument_scope,
            resolution=resolution,
            adjustment=adjustment,
            start_time=_utc(start_time),
            end_time=_utc(end_time),
            timezone=timezone_name,
            calendar_version=calendar_version,
            schema_version=schema_version,
            object_uri=reference.object_uri,
            checksum=reference.checksum,
            row_count=row_count,
            created_at=utc_now(),
        )


def read_parquet_payload(payload: ArtifactPayload) -> pa.Table:
    return pq.read_table(BytesIO(payload.content))  # type: ignore[no-untyped-call]


def _ohlcv_table(bars: Sequence[Bar]) -> pa.Table:
    schema = pa.schema(
        [
            pa.field("observed_at", pa.timestamp("us", tz="UTC")),
            pa.field("open_price", pa.decimal128(18, 4)),
            pa.field("high_price", pa.decimal128(18, 4)),
            pa.field("low_price", pa.decimal128(18, 4)),
            pa.field("close_price", pa.decimal128(18, 4)),
            pa.field("volume", pa.int64()),
            pa.field("quality_flags", pa.list_(pa.string())),
        ]
    )
    return pa.Table.from_arrays(
        [
            pa.array([_utc(bar.observed_at) for bar in bars], type=schema.field("observed_at").type),
            pa.array([_money(bar.open_price) for bar in bars], type=schema.field("open_price").type),
            pa.array([_money(bar.high_price) for bar in bars], type=schema.field("high_price").type),
            pa.array([_money(bar.low_price) for bar in bars], type=schema.field("low_price").type),
            pa.array([_money(bar.close_price) for bar in bars], type=schema.field("close_price").type),
            pa.array([bar.volume for bar in bars], type=schema.field("volume").type),
            pa.array(
                [[flag.value for flag in bar.quality_flags] for bar in bars],
                type=schema.field("quality_flags").type,
            ),
        ],
        schema=schema,
    )


def _adjustment_factor_table(factors: Sequence[AdjustmentFactor]) -> pa.Table:
    schema = pa.schema(
        [
            pa.field("effective_date", pa.timestamp("us", tz="UTC")),
            pa.field("factor", pa.decimal128(18, 8)),
        ]
    )
    return pa.Table.from_arrays(
        [
            pa.array(
                [_utc(factor.effective_date) for factor in factors],
                type=schema.field("effective_date").type,
            ),
            pa.array(
                [Decimal(factor.factor) for factor in factors],
                type=schema.field("factor").type,
            ),
        ],
        schema=schema,
    )


def _company_action_table(actions: Sequence[CompanyAction]) -> pa.Table:
    schema = pa.schema(
        [
            pa.field("effective_date", pa.timestamp("us", tz="UTC")),
            pa.field("action_type", pa.string()),
            pa.field("description", pa.string()),
        ]
    )
    return pa.Table.from_arrays(
        [
            pa.array(
                [_utc(action.effective_date) for action in actions],
                type=schema.field("effective_date").type,
            ),
            pa.array([action.action_type for action in actions], type=schema.field("action_type").type),
            pa.array([action.description for action in actions], type=schema.field("description").type),
        ],
        schema=schema,
    )


def _parquet_bytes(table: pa.Table) -> bytes:
    sink = BytesIO()
    pq.write_table(table, sink)  # type: ignore[no-untyped-call]
    return sink.getvalue()


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("snapshot datetime must be timezone-aware")
    return value.astimezone(timezone.utc)


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"))
