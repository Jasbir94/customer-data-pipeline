import os
import pathlib
import pandas as pd
import pytest

from clean_data import parse_order_date, validate_email, clean_customers


def test_parse_order_date_formats():
    """Test that the date parser correctly handles all three required formats and invalid cases."""
    # YYYY-MM-DD
    assert parse_order_date("2024-05-15") == pd.Timestamp("2024-05-15")
    # DD/MM/YYYY
    assert parse_order_date("15/05/2024") == pd.Timestamp("2024-05-15")
    # MM-DD-YYYY
    assert parse_order_date("05-15-2024") == pd.Timestamp("2024-05-15")
    
    # Invalid strings should return NaT
    assert pd.isna(parse_order_date("invalid-date"))
    assert pd.isna(parse_order_date(None))
    assert pd.isna(parse_order_date(pd.NA))


def test_validate_email():
    """Test that the email validator correctly flags malformed emails."""
    # Valid
    assert validate_email("user@example.com") is True
    assert validate_email("first.last@company.org") is True
    
    # Missing @
    assert validate_email("userexample.com") is False
    # Missing domain dot
    assert validate_email("user@examplecom") is False
    # Empty / null
    assert validate_email("") is False
    assert validate_email(None) is False
    assert validate_email(pd.NA) is False


def test_clean_customers_dedup_and_email_flag(tmp_path: pathlib.Path):
    """Test the end-to-end customer cleaning logic on a mocked dataframe."""
    
    # Create mock raw csv
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    
    mock_data = pd.DataFrame({
        "customer_id": ["C1", "C2", "C1", "C3"],
        "name": ["Alice", "Bob ", " Alice", "Carol"],
        "email": ["alice@gmail.com", "bobgmail.com", "alice@gmail.com", None],
        "region": ["North", "South", "North", ""],
        "signup_date": ["2023-01-01", "2023-02-01", "2024-01-01", "2023-03-01"]
    })
    
    mock_data.to_csv(raw_dir / "customers.csv", index=False)
    
    # Run the cleaning function on the mock dir
    cleaned = clean_customers(raw_dir)
    
    # Assertions
    assert len(cleaned) == 3  # 1 duplicate removed (C1)
    
    # C1 should keep the latest date (2024-01-01)
    c1 = cleaned[cleaned["customer_id"] == "C1"].iloc[0]
    assert c1["signup_date"] == "2024-01-01"
    
    # Email flags
    assert c1["is_valid_email"] == True
    
    c2 = cleaned[cleaned["customer_id"] == "C2"].iloc[0]
    assert c2["is_valid_email"] == False  # bobgmail.com
    
    c3 = cleaned[cleaned["customer_id"] == "C3"].iloc[0]
    assert c3["is_valid_email"] == False  # None email
    
    # Region filling
    assert c3["region"] == "Unknown"
    
    # Whitespace stripping
    assert c1["name"] == "Alice"
    assert c2["name"] == "Bob"
