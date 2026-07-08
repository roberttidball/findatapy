import pandas as pd

from findatapy.market.datavendorfxmacrodata import DataVendorFXMacroData
from findatapy.market.marketdatarequest import MarketDataRequest


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_fxmacrodata_vendor_builds_daily_fx_dataframe(monkeypatch):
    calls = {}

    def fake_get(url, params=None, timeout=None):
        calls["url"] = url
        calls["params"] = params
        calls["timeout"] = timeout

        return _FakeResponse({
            "data": [
                {"date": "2026-01-02", "val": 1.10},
                {"date": "2026-01-03", "val": 1.11},
            ]
        })

    monkeypatch.setattr(
        "findatapy.market.datavendorfxmacrodata.requests.get", fake_get)

    md_request = MarketDataRequest(
        data_source="fxmacrodata",
        category="fx",
        start_date="2026-01-01",
        finish_date="2026-01-04",
        tickers=["EURUSD"],
        fields=["open", "high", "low", "close"],
        fxmacrodata_api_key="test-key",
    )

    data_frame = DataVendorFXMacroData().load_ticker(md_request)

    assert isinstance(data_frame, pd.DataFrame)
    assert list(data_frame.columns) == [
        "EURUSD.open", "EURUSD.high", "EURUSD.low", "EURUSD.close"]
    assert data_frame.loc[pd.Timestamp("2026-01-02"), "EURUSD.close"] == 1.10
    assert calls["url"] == "https://fxmacrodata.com/api/v1/forex/eur/usd"
    assert calls["params"]["api_key"] == "test-key"
    assert calls["params"]["start_date"] == "2026-01-01"
    assert calls["params"]["end_date"] == "2026-01-04"
