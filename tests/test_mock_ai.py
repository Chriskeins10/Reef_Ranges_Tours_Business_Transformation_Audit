"""
Basic tests for the mock AI qualification engine.
Run with: pytest tests/
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mock_ai import (
    extract_party_size, extract_tour_id, extract_date,
    extract_special_needs, qualify_enquiry, check_availability
)


def test_extract_party_size():
    assert extract_party_size("We are 4 people") == 4
    assert extract_party_size("party of 2") == 2
    assert extract_party_size("for 6 guests please") == 6
    assert extract_party_size("just me") is None


def test_extract_tour_id():
    assert extract_tour_id("I'd like the full day reef trip") == "GBR-FULL"
    assert extract_tour_id("half day snorkel please") == "GBR-HALF"
    assert extract_tour_id("Daintree rainforest tour") == "DAINTREE"
    assert extract_tour_id("Kuranda skyrail") == "KURANDA"
    assert extract_tour_id("waterfalls on the tablelands") == "WATERFALLS"


def test_extract_date():
    assert extract_date("tomorrow") == "2026-10-21"
    assert extract_date("22/10/2026") == "2026-10-22"
    assert extract_date("25 October") == "2026-10-25"
    assert extract_date("next weekend") is not None


def test_extract_special_needs():
    assert "Dietary" in extract_special_needs("We need vegetarian options")
    assert "Accessibility" in extract_special_needs("wheelchair access required")
    assert extract_special_needs("just a normal booking") == "None stated"


def test_qualify_complete_enquiry():
    result = qualify_enquiry(
        "Hi, we are 3 people wanting the full day Great Barrier Reef tour on 23/10/2026"
    )
    assert result["tour_id"] == "GBR-FULL"
    assert result["date"] == "2026-10-23"
    assert result["party_size"] == 3
    assert result["confidence"] == "high"
    assert "availability" in result


def test_qualify_incomplete():
    result = qualify_enquiry("I want to go to the reef")
    assert result["tour_id"] in ("GBR-FULL", "GBR-HALF")
    assert len(result["missing_fields"]) >= 1
    assert result["confidence"] in ("medium", "low")


def test_check_availability_existing():
    # We know BK-1001 and BK-1002 already take 10 places on GBR-FULL 2026-10-22
    # max_capacity = 40, so plenty left
    avail = check_availability("GBR-FULL", "2026-10-22", 5)
    assert avail["available"] is True
    assert avail["remaining"] >= 5
