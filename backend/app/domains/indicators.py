from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domains.market import BarsRequest, QualityFlag


IndicatorSeries = tuple[Decimal | None, ...]


@dataclass(frozen=True, slots=True)
class IndicatorRequest:
    bars_request: BarsRequest
    sma_period: int = 20
    ema_period: int = 20
    macd_fast_period: int = 12
    macd_slow_period: int = 26
    macd_signal_period: int = 9
    rsi_period: int = 14
    bollinger_period: int = 20
    bollinger_multiplier: Decimal = Decimal("2")
    adx_period: int = 14

    def __post_init__(self) -> None:
        for period in (
            self.sma_period,
            self.ema_period,
            self.macd_fast_period,
            self.macd_slow_period,
            self.macd_signal_period,
            self.rsi_period,
            self.bollinger_period,
            self.adx_period,
        ):
            _require_period(period)
        if self.macd_fast_period >= self.macd_slow_period:
            raise ValueError("macd_fast_period must be smaller than macd_slow_period")
        if self.bollinger_multiplier <= 0:
            raise ValueError("bollinger_multiplier must be positive")


@dataclass(frozen=True, slots=True)
class IndicatorPoint:
    observed_at: datetime
    sma: Decimal | None
    ema: Decimal | None
    macd: Decimal | None
    macd_signal: Decimal | None
    macd_histogram: Decimal | None
    rsi: Decimal | None
    bollinger_middle: Decimal | None
    bollinger_upper: Decimal | None
    bollinger_lower: Decimal | None
    adx: Decimal | None


@dataclass(frozen=True, slots=True)
class IndicatorResult:
    instrument_id: str
    points: tuple[IndicatorPoint, ...]
    as_of: datetime
    is_delayed: bool
    stale_age_seconds: int | None
    quality_flags: tuple[QualityFlag, ...]


@dataclass(frozen=True, slots=True)
class MacdResult:
    macd: IndicatorSeries
    signal: IndicatorSeries
    histogram: IndicatorSeries


@dataclass(frozen=True, slots=True)
class BollingerBandsResult:
    middle: IndicatorSeries
    upper: IndicatorSeries
    lower: IndicatorSeries


def sma(values: Sequence[Decimal], period: int) -> IndicatorSeries:
    _require_period(period)
    result: list[Decimal | None] = []
    for index in range(len(values)):
        if index + 1 < period:
            result.append(None)
            continue
        window = values[index + 1 - period : index + 1]
        result.append(sum(window, Decimal("0")) / Decimal(period))
    return tuple(result)


def ema(values: Sequence[Decimal], period: int) -> IndicatorSeries:
    _require_period(period)
    return _ema_required(values, period)


def macd(
    values: Sequence[Decimal],
    *,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> MacdResult:
    _require_period(fast_period)
    _require_period(slow_period)
    _require_period(signal_period)
    if fast_period >= slow_period:
        raise ValueError("fast_period must be smaller than slow_period")

    fast = ema(values, fast_period)
    slow = ema(values, slow_period)
    line = tuple(
        fast_value - slow_value if fast_value is not None and slow_value is not None else None
        for fast_value, slow_value in zip(fast, slow, strict=True)
    )
    signal = _ema_optional(line, signal_period)
    histogram = tuple(
        value - signal_value if value is not None and signal_value is not None else None
        for value, signal_value in zip(line, signal, strict=True)
    )
    return MacdResult(macd=line, signal=signal, histogram=histogram)


def rsi(values: Sequence[Decimal], period: int = 14) -> IndicatorSeries:
    _require_period(period)
    if len(values) <= period:
        return tuple(None for _ in values)

    result: list[Decimal | None] = [None] * len(values)
    gains: list[Decimal] = []
    losses: list[Decimal] = []
    for index in range(1, period + 1):
        change = values[index] - values[index - 1]
        gains.append(max(change, Decimal("0")))
        losses.append(max(-change, Decimal("0")))

    average_gain = sum(gains, Decimal("0")) / Decimal(period)
    average_loss = sum(losses, Decimal("0")) / Decimal(period)
    result[period] = _rsi_value(average_gain, average_loss)

    for index in range(period + 1, len(values)):
        change = values[index] - values[index - 1]
        gain = max(change, Decimal("0"))
        loss = max(-change, Decimal("0"))
        average_gain = ((average_gain * Decimal(period - 1)) + gain) / Decimal(period)
        average_loss = ((average_loss * Decimal(period - 1)) + loss) / Decimal(period)
        result[index] = _rsi_value(average_gain, average_loss)

    return tuple(result)


def bollinger_bands(
    values: Sequence[Decimal],
    period: int = 20,
    multiplier: Decimal = Decimal("2"),
) -> BollingerBandsResult:
    _require_period(period)
    middle = sma(values, period)
    upper: list[Decimal | None] = []
    lower: list[Decimal | None] = []
    for index, mean in enumerate(middle):
        if mean is None:
            upper.append(None)
            lower.append(None)
            continue
        window = values[index + 1 - period : index + 1]
        variance = sum((value - mean) ** 2 for value in window) / Decimal(period)
        deviation = variance.sqrt()
        upper.append(mean + (multiplier * deviation))
        lower.append(mean - (multiplier * deviation))
    return BollingerBandsResult(middle=middle, upper=tuple(upper), lower=tuple(lower))


def adx(
    highs: Sequence[Decimal],
    lows: Sequence[Decimal],
    closes: Sequence[Decimal],
    period: int = 14,
) -> IndicatorSeries:
    _require_period(period)
    if len(highs) != len(lows) or len(highs) != len(closes):
        raise ValueError("high, low and close series must have the same length")
    if len(closes) <= period * 2 - 1:
        return tuple(None for _ in closes)

    true_ranges: list[Decimal] = []
    plus_dm: list[Decimal] = []
    minus_dm: list[Decimal] = []
    for index in range(1, len(closes)):
        high_diff = highs[index] - highs[index - 1]
        low_diff = lows[index - 1] - lows[index]
        plus_dm.append(high_diff if high_diff > low_diff and high_diff > 0 else Decimal("0"))
        minus_dm.append(low_diff if low_diff > high_diff and low_diff > 0 else Decimal("0"))
        true_ranges.append(
            max(
                highs[index] - lows[index],
                abs(highs[index] - closes[index - 1]),
                abs(lows[index] - closes[index - 1]),
            )
        )

    smoothed_tr = sum(true_ranges[:period], Decimal("0"))
    smoothed_plus = sum(plus_dm[:period], Decimal("0"))
    smoothed_minus = sum(minus_dm[:period], Decimal("0"))
    dx_values: list[Decimal] = [_dx(smoothed_plus, smoothed_minus, smoothed_tr)]

    for index in range(period, len(true_ranges)):
        smoothed_tr = smoothed_tr - (smoothed_tr / Decimal(period)) + true_ranges[index]
        smoothed_plus = smoothed_plus - (smoothed_plus / Decimal(period)) + plus_dm[index]
        smoothed_minus = smoothed_minus - (smoothed_minus / Decimal(period)) + minus_dm[index]
        dx_values.append(_dx(smoothed_plus, smoothed_minus, smoothed_tr))

    result: list[Decimal | None] = [None] * len(closes)
    first_adx = sum(dx_values[:period], Decimal("0")) / Decimal(period)
    first_index = period * 2 - 1
    result[first_index] = first_adx
    previous_adx = first_adx
    for offset, dx_value in enumerate(dx_values[period:], start=first_index + 1):
        previous_adx = ((previous_adx * Decimal(period - 1)) + dx_value) / Decimal(period)
        result[offset] = previous_adx
    return tuple(result)


def _ema_required(values: Sequence[Decimal], period: int) -> IndicatorSeries:
    result: list[Decimal | None] = []
    multiplier = Decimal("2") / Decimal(period + 1)
    previous: Decimal | None = None
    for index, value in enumerate(values):
        if index + 1 < period:
            result.append(None)
            continue
        if previous is None:
            previous = sum(values[index + 1 - period : index + 1], Decimal("0")) / Decimal(period)
        else:
            previous = ((value - previous) * multiplier) + previous
        result.append(previous)
    return tuple(result)


def _ema_optional(values: Sequence[Decimal | None], period: int) -> IndicatorSeries:
    result: list[Decimal | None] = [None] * len(values)
    seed: list[Decimal] = []
    previous: Decimal | None = None
    multiplier = Decimal("2") / Decimal(period + 1)
    for index, value in enumerate(values):
        if value is None:
            continue
        if previous is None:
            seed.append(value)
            if len(seed) == period:
                previous = sum(seed, Decimal("0")) / Decimal(period)
                result[index] = previous
            continue
        previous = ((value - previous) * multiplier) + previous
        result[index] = previous
    return tuple(result)


def _rsi_value(average_gain: Decimal, average_loss: Decimal) -> Decimal:
    if average_loss == 0:
        return Decimal("100")
    relative_strength = average_gain / average_loss
    return Decimal("100") - (Decimal("100") / (Decimal("1") + relative_strength))


def _dx(plus_dm: Decimal, minus_dm: Decimal, true_range: Decimal) -> Decimal:
    if true_range == 0:
        return Decimal("0")
    plus_di = Decimal("100") * plus_dm / true_range
    minus_di = Decimal("100") * minus_dm / true_range
    denominator = plus_di + minus_di
    if denominator == 0:
        return Decimal("0")
    return Decimal("100") * abs(plus_di - minus_di) / denominator


def _require_period(period: int) -> None:
    if period <= 0:
        raise ValueError("period must be positive")
