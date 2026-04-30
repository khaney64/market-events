import importlib.util
import pathlib
import unittest
from datetime import datetime
from unittest.mock import patch


MODULE_PATH = pathlib.Path(__file__).with_name("market-events.py")
SPEC = importlib.util.spec_from_file_location("market_events", MODULE_PATH)
market_events = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(market_events)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


class MarketEventsTests(unittest.TestCase):
    def test_fetch_events_paginates_until_short_page(self):
        unpaged = [{"symbol": f"U{i}", "date": "2026-04-30"} for i in range(4000)]
        first_page = [{"symbol": f"T{i}", "date": "2026-04-30"} for i in range(4000)]
        second_page = [{"symbol": "AAPL", "date": "2026-04-30"}]
        calls = []

        def fake_get(url, params, timeout):
            calls.append(params.copy())
            if "page" not in params:
                return FakeResponse(unpaged)
            return FakeResponse(first_page if params["page"] == 0 else second_page)

        with patch.object(market_events.requests, "get", side_effect=fake_get):
            events = market_events.fetch_events(
                "earnings",
                datetime(2026, 4, 30),
                datetime(2026, 5, 14),
                "test-key",
            )

        self.assertEqual(len(events), 8001)
        self.assertEqual([call.get("page", "none") for call in calls], ["none", 0, 1])

    def test_fetch_events_stops_after_short_first_page(self):
        calls = []

        def fake_get(url, params, timeout):
            calls.append(params.copy())
            return FakeResponse([{"symbol": "AAPL", "date": "2026-04-30"}])

        with patch.object(market_events.requests, "get", side_effect=fake_get):
            events = market_events.fetch_events(
                "earnings",
                datetime(2026, 4, 30),
                datetime(2026, 5, 14),
                "test-key",
            )

        self.assertEqual(len(events), 1)
        self.assertEqual([call.get("page", "none") for call in calls], ["none"])

    def test_fetch_events_uses_paginated_dividends_calendar(self):
        calls = []

        def fake_get(url, params, timeout):
            calls.append((url, params.copy()))
            return FakeResponse([{"symbol": "AAPL", "date": "2026-04-30"}])

        with patch.object(market_events.requests, "get", side_effect=fake_get):
            events = market_events.fetch_events(
                "dividends",
                datetime(2026, 4, 30),
                datetime(2026, 5, 14),
                "test-key",
            )

        self.assertEqual(len(events), 1)
        self.assertTrue(calls[0][0].endswith("/dividends-calendar"))
        self.assertNotIn("page", calls[0][1])

    def test_fetch_events_deduplicates_unpaged_and_explicit_pages(self):
        duplicate = {"symbol": "AAPL", "date": "2026-04-30"}
        full_page = [duplicate] + [{"symbol": f"T{i}", "date": "2026-04-30"} for i in range(3999)]
        calls = []

        def fake_get(url, params, timeout):
            calls.append(params.copy())
            if "page" not in params:
                return FakeResponse(full_page)
            if params["page"] == 0:
                return FakeResponse(full_page)
            return FakeResponse([])

        with patch.object(market_events.requests, "get", side_effect=fake_get):
            events = market_events.fetch_events(
                "earnings",
                datetime(2026, 4, 30),
                datetime(2026, 5, 14),
                "test-key",
            )

        self.assertEqual(len(events), 4000)
        self.assertEqual([call.get("page", "none") for call in calls], ["none", 0, 1])

    def test_filter_events_normalizes_symbol_and_filters_date(self):
        rows = market_events.filter_events(
            [
                {"symbol": " AAPL ", "date": "2026-04-30"},
                {"symbol": "AAPL", "date": "2026-05-15"},
                {"symbol": "MSFT", "date": "2026-04-30"},
            ],
            {"AAPL"},
            "earnings",
            datetime(2026, 4, 30),
            datetime(2026, 5, 14),
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["ticker"], "AAPL")
        self.assertEqual(rows[0]["date"], "2026-04-30")


if __name__ == "__main__":
    unittest.main()
