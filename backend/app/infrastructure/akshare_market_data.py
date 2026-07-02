from __future__ import annotations

import importlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal, InvalidOperation
from typing import Literal, Protocol, cast
from zoneinfo import ZoneInfo

from app.core.config import Settings, get_settings
from app.core.time import utc_now
from app.domains.market import (
    Bar,
    BarsRequest,
    BarsResult,
    CHINA_A_EXCHANGE_TIMEZONE,
    CHINA_A_MARKET,
    DataSourceHealth,
    DataSourceStatus,
    Instrument,
    MarketDataUnavailable,
    QualityFlag,
    Quote,
    TradingCalendar,
)
from app.infrastructure.cache import RedisCache, RedisKeyDefinition


AKSHARE_PROVIDER = "akshare"
SUPPORTED_DAILY_LOOKBACK_DAYS = 366 * 5
SUPPORTED_RESOLUTIONS = {"daily", "weekly", "monthly"}
SUPPORTED_ADJUSTMENTS = {"none", "qfq", "hfq"}


class TableLike(Protocol):
    def to_dict(self, orient: Literal["records"]) -> list[dict[str, object]]: ...


class AkshareModule(Protocol):
    def stock_zh_a_spot_em(self) -> TableLike: ...

    def stock_zh_a_hist(
        self,
        symbol: str,
        period: str,
        start_date: str,
        end_date: str,
        adjust: str,
        timeout: float | None = None,
    ) -> TableLike: ...

    def tool_trade_date_hist_sina(self) -> TableLike: ...


@dataclass(slots=True)
class _ProviderState:
    consecutive_failures: int = 0
    last_success_at: datetime | None = None
    last_error_code: str | None = None
    last_failure_at: datetime | None = None
    stale_cache_available: bool = False
    stale_age_seconds: int | None = None


class AkshareDataProvider:
    def __init__(
        self,
        akshare_factory: Callable[[], AkshareModule],
        cache: RedisCache,
        settings: Settings,
    ) -> None:
        self._akshare_factory = akshare_factory
        self._cache = cache
        self._settings = settings
        self._state = _ProviderState()
        self._bars_cache_key = RedisKeyDefinition(
            namespace="market",
            name="bars",
            ttl_seconds=settings.market_cache_ttl_seconds,
            max_value_bytes=settings.market_cache_max_value_bytes,
            freshness_seconds=settings.market_cache_freshness_seconds,
        )

    @classmethod
    def from_settings(cls) -> AkshareDataProvider:
        return cls(
            akshare_factory=_load_akshare,
            cache=RedisCache.from_settings(),
            settings=get_settings(),
        )

    async def search_instruments(self, query: str) -> tuple[Instrument, ...]:
        try:
            records = self._records(self._akshare_factory().stock_zh_a_spot_em())
        except Exception as exc:
            self._record_failure(type(exc).__name__, None)
            raise MarketDataUnavailable(AKSHARE_PROVIDER, type(exc).__name__) from exc
        normalized_query = query.strip().lower()
        instruments: list[Instrument] = []
        for record in records:
            symbol = _required_text(record, "代码")
            name = _required_text(record, "名称")
            if normalized_query not in symbol.lower() and normalized_query not in name.lower():
                continue
            instruments.append(
                Instrument(
                    instrument_id=f"{CHINA_A_MARKET}:{symbol}",
                    symbol=symbol,
                    name=name,
                    market=CHINA_A_MARKET,
                    exchange_timezone=CHINA_A_EXCHANGE_TIMEZONE,
                )
            )
            if len(instruments) >= 20:
                break
        self._record_success()
        return tuple(instruments)

    async def get_bars(self, request: BarsRequest) -> BarsResult:
        _validate_bars_request(request)
        identity = _bars_cache_identity(request)
        cached = self._cache.get_bytes(self._bars_cache_key, identity)
        if cached is not None and cached.is_fresh:
            return _decode_bars(cached.value)

        try:
            result = self._fetch_bars(request)
        except Exception as exc:
            stale = self._delayed_from_cache(identity)
            self._record_failure(type(exc).__name__, stale)
            if stale is not None:
                return stale
            raise MarketDataUnavailable(AKSHARE_PROVIDER, type(exc).__name__) from exc

        self._cache.set_bytes(self._bars_cache_key, identity, _encode_bars(result))
        self._record_success()
        return result

    async def get_quote(self, instrument_id: str) -> Quote:
        symbol = _instrument_symbol(instrument_id)
        try:
            records = self._records(self._akshare_factory().stock_zh_a_spot_em())
        except Exception as exc:
            self._record_failure(type(exc).__name__, None)
            raise MarketDataUnavailable(AKSHARE_PROVIDER, type(exc).__name__) from exc
        for record in records:
            if _required_text(record, "代码") != symbol:
                continue
            now = utc_now()
            self._record_success()
            return Quote(
                instrument_id=instrument_id,
                bid_price=None,
                ask_price=None,
                last_price=_decimal(record["最新价"]),
                as_of=now,
                is_delayed=False,
                quality_flags=(),
            )
        self._record_failure("DATA_NOT_FOUND", None)
        raise KeyError(instrument_id)

    async def get_calendar(self, market: str, start: date, end: date) -> TradingCalendar:
        if market != CHINA_A_MARKET:
            raise ValueError("unsupported market")
        try:
            records = self._records(self._akshare_factory().tool_trade_date_hist_sina())
        except Exception as exc:
            self._record_failure(type(exc).__name__, None)
            raise MarketDataUnavailable(AKSHARE_PROVIDER, type(exc).__name__) from exc
        days = tuple(
            day
            for day in (_record_date(record) for record in records)
            if start <= day <= end
        )
        self._record_success()
        return TradingCalendar(
            market=market,
            version="akshare-sina-trade-date-v1",
            timezone=CHINA_A_EXCHANGE_TIMEZONE,
            trading_days=days,
        )

    async def get_health(self, provider: str) -> DataSourceHealth:
        if provider != AKSHARE_PROVIDER:
            raise ValueError("unsupported provider")
        return DataSourceHealth(
            provider=AKSHARE_PROVIDER,
            status=self._status(),
            checked_at=utc_now(),
            consecutive_failures=self._state.consecutive_failures,
            last_success_at=self._state.last_success_at,
            last_error_code=self._state.last_error_code,
            stale_cache_available=self._state.stale_cache_available,
            stale_age_seconds=self._state.stale_age_seconds,
        )

    def _fetch_bars(self, request: BarsRequest) -> BarsResult:
        symbol = _instrument_symbol(request.instrument_id)
        ak_adjust = "" if request.adjustment == "none" else request.adjustment
        records = self._records(
            self._akshare_factory().stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=request.start.strftime("%Y%m%d"),
                end_date=request.end.strftime("%Y%m%d"),
                adjust=ak_adjust,
                timeout=10,
            )
        )
        daily_bars = tuple(_bar_from_record(record) for record in records)
        daily_flags = _bars_quality_flags(daily_bars)
        bars = _bars_for_resolution(daily_bars, request.resolution)
        flags = tuple(dict.fromkeys((*daily_flags, *_bars_quality_flags(bars))))
        return BarsResult(
            instrument_id=request.instrument_id,
            bars=bars,
            as_of=bars[-1].observed_at if bars else utc_now(),
            is_delayed=False,
            stale_age_seconds=None,
            quality_flags=flags,
        )

    def _records(self, table: TableLike) -> list[dict[str, object]]:
        return table.to_dict("records")

    def _delayed_from_cache(self, identity: str) -> BarsResult | None:
        cached = self._cache.get_bytes(self._bars_cache_key, identity)
        if cached is None:
            self._state.stale_cache_available = False
            self._state.stale_age_seconds = None
            return None
        age_seconds = int((utc_now() - cached.stored_at).total_seconds())
        if age_seconds > self._settings.market_max_stale_cache_age_seconds:
            self._state.stale_cache_available = False
            self._state.stale_age_seconds = age_seconds
            return None
        result = _decode_bars(cached.value)
        flags = tuple(dict.fromkeys((*result.quality_flags, QualityFlag.STALE_CACHE, QualityFlag.PROVIDER_DEGRADED)))
        delayed = BarsResult(
            instrument_id=result.instrument_id,
            bars=result.bars,
            as_of=result.as_of,
            is_delayed=True,
            stale_age_seconds=age_seconds,
            quality_flags=flags,
        )
        self._state.stale_cache_available = True
        self._state.stale_age_seconds = age_seconds
        return delayed

    def _record_success(self) -> None:
        self._state.consecutive_failures = 0
        self._state.last_success_at = utc_now()
        self._state.last_error_code = None
        self._state.last_failure_at = None
        self._state.stale_cache_available = False
        self._state.stale_age_seconds = None

    def _record_failure(self, error_code: str, stale: BarsResult | None) -> None:
        self._state.consecutive_failures += 1
        self._state.last_error_code = error_code
        self._state.last_failure_at = utc_now()
        if stale is not None:
            self._state.stale_cache_available = True
            self._state.stale_age_seconds = stale.stale_age_seconds

    def _status(self) -> DataSourceStatus:
        if self._state.consecutive_failures == 0:
            return DataSourceStatus.HEALTHY
        if self._state.stale_cache_available:
            return DataSourceStatus.DEGRADED
        if self._state.consecutive_failures < self._settings.market_failure_threshold:
            return DataSourceStatus.DEGRADED
        if self._state.last_failure_at is None:
            return DataSourceStatus.UNAVAILABLE
        elapsed = (utc_now() - self._state.last_failure_at).total_seconds()
        if elapsed >= self._settings.market_recovery_cooldown_seconds:
            return DataSourceStatus.RECOVERING
        return DataSourceStatus.UNAVAILABLE


def _load_akshare() -> AkshareModule:
    return cast(AkshareModule, importlib.import_module("akshare"))


def _validate_bars_request(request: BarsRequest) -> None:
    if request.resolution not in SUPPORTED_RESOLUTIONS:
        raise ValueError("unsupported bars resolution")
    if (request.end - request.start).days > SUPPORTED_DAILY_LOOKBACK_DAYS:
        raise ValueError("daily bars request exceeds supported 5-year range")
    if request.adjustment not in SUPPORTED_ADJUSTMENTS:
        raise ValueError("unsupported adjustment")


def _instrument_symbol(instrument_id: str) -> str:
    prefix = f"{CHINA_A_MARKET}:"
    if not instrument_id.startswith(prefix):
        raise ValueError("unsupported instrument_id")
    return instrument_id.removeprefix(prefix)


def _bar_from_record(record: Mapping[str, object]) -> Bar:
    observed_date = _date_from_value(record["日期"])
    observed_at = datetime.combine(
        observed_date,
        time(hour=15),
        tzinfo=ZoneInfo(CHINA_A_EXCHANGE_TIMEZONE),
    ).astimezone(timezone.utc)
    return Bar(
        observed_at=observed_at,
        open_price=_decimal(record["开盘"]),
        high_price=_decimal(record["最高"]),
        low_price=_decimal(record["最低"]),
        close_price=_decimal(record["收盘"]),
        volume=int(_decimal(record["成交量"])),
        quality_flags=(),
    )


def _bars_quality_flags(bars: tuple[Bar, ...]) -> tuple[QualityFlag, ...]:
    flags: list[QualityFlag] = []
    if not bars:
        flags.append(QualityFlag.MISSING_BARS)
    observed = [bar.observed_at for bar in bars]
    if len(set(observed)) != len(observed):
        flags.append(QualityFlag.DUPLICATE_BARS)
    if observed != sorted(observed):
        flags.append(QualityFlag.OUT_OF_ORDER)
    return tuple(flags)


def _bars_for_resolution(bars: tuple[Bar, ...], resolution: str) -> tuple[Bar, ...]:
    ordered_bars = tuple(sorted(bars, key=lambda bar: bar.observed_at))
    if resolution == "daily":
        return ordered_bars
    if resolution not in {"weekly", "monthly"}:
        raise ValueError("unsupported bars resolution")
    return _aggregate_bars(ordered_bars, resolution)


def _aggregate_bars(bars: tuple[Bar, ...], resolution: str) -> tuple[Bar, ...]:
    grouped: dict[tuple[int, int], list[Bar]] = {}
    for bar in bars:
        local_day = bar.observed_at.astimezone(ZoneInfo(CHINA_A_EXCHANGE_TIMEZONE)).date()
        if resolution == "weekly":
            iso_year, iso_week, _ = local_day.isocalendar()
            key = (iso_year, iso_week)
        else:
            key = (local_day.year, local_day.month)
        grouped.setdefault(key, []).append(bar)

    aggregated: list[Bar] = []
    for key in sorted(grouped):
        bucket = grouped[key]
        quality_flags = tuple(
            dict.fromkeys(flag for bar in bucket for flag in bar.quality_flags)
        )
        aggregated.append(
            Bar(
                observed_at=bucket[-1].observed_at,
                open_price=bucket[0].open_price,
                high_price=max(bar.high_price for bar in bucket),
                low_price=min(bar.low_price for bar in bucket),
                close_price=bucket[-1].close_price,
                volume=sum(bar.volume for bar in bucket),
                quality_flags=quality_flags,
            )
        )
    return tuple(aggregated)


def _record_date(record: Mapping[str, object]) -> date:
    if "trade_date" in record:
        return _date_from_value(record["trade_date"])
    if "日期" in record:
        return _date_from_value(record["日期"])
    raise ValueError("calendar record missing trade date")


def _date_from_value(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    raise ValueError("invalid date value")


def _required_text(record: Mapping[str, object], key: str) -> str:
    value = record[key]
    if value is None:
        raise ValueError(f"missing {key}")
    return str(value).strip()


def _decimal(value: object) -> Decimal:
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("invalid decimal value") from exc
    if not result.is_finite():
        raise ValueError("invalid decimal value")
    return result


def _bars_cache_identity(request: BarsRequest) -> str:
    return "|".join(
        [
            request.instrument_id,
            request.start.isoformat(),
            request.end.isoformat(),
            request.resolution,
            request.adjustment,
        ]
    )


def _encode_bars(result: BarsResult) -> bytes:
    payload = {
        "instrument_id": result.instrument_id,
        "bars": [
            {
                "observed_at": bar.observed_at.isoformat(),
                "open_price": str(bar.open_price),
                "high_price": str(bar.high_price),
                "low_price": str(bar.low_price),
                "close_price": str(bar.close_price),
                "volume": bar.volume,
                "quality_flags": [flag.value for flag in bar.quality_flags],
            }
            for bar in result.bars
        ],
        "as_of": result.as_of.isoformat(),
        "is_delayed": result.is_delayed,
        "stale_age_seconds": result.stale_age_seconds,
        "quality_flags": [flag.value for flag in result.quality_flags],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _decode_bars(value: bytes) -> BarsResult:
    payload = json.loads(value.decode("utf-8"))
    bars = tuple(
        Bar(
            observed_at=datetime.fromisoformat(record["observed_at"]),
            open_price=Decimal(record["open_price"]),
            high_price=Decimal(record["high_price"]),
            low_price=Decimal(record["low_price"]),
            close_price=Decimal(record["close_price"]),
            volume=int(record["volume"]),
            quality_flags=tuple(QualityFlag(flag) for flag in record["quality_flags"]),
        )
        for record in payload["bars"]
    )
    return BarsResult(
        instrument_id=payload["instrument_id"],
        bars=bars,
        as_of=datetime.fromisoformat(payload["as_of"]),
        is_delayed=bool(payload["is_delayed"]),
        stale_age_seconds=payload["stale_age_seconds"],
        quality_flags=tuple(QualityFlag(flag) for flag in payload["quality_flags"]),
    )
