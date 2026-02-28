"""
Tests for data_loader module.
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core.data_loader import (
    load_json, load_excel, load_csv, load_file,
    detect_valid_channels, CHANNEL_COLUMNS, SUPPORTED_EXTENSIONS
)


# Test data directory
TEST_DATA_DIR = Path(__file__).parent.parent / "原始数据" / "2026.2.26"


class TestLoadJson:
    """Tests for load_json function."""

    def test_load_json_from_path(self):
        """Test loading JSON from file path."""
        json_path = TEST_DATA_DIR / "AFReport_SP_20250507_102452.json"
        df = load_json(json_path)

        # Check basic structure
        assert isinstance(df, pd.DataFrame)
        assert "Temperature" in df.columns
        assert "Space1" in df.columns
        assert "Space2" in df.columns
        assert "DateTimeStr" in df.columns

        # Check data is loaded
        assert len(df) > 0
        assert df["Temperature"].notna().all()

    def test_load_json_with_nan_string(self):
        """Test that 'NaN' strings are converted to np.nan."""
        json_path = TEST_DATA_DIR / "AFReport_SP_20250519_171458.json"
        df = load_json(json_path)

        # Space2~Space6 should have NaN values (converted from "NaN" strings)
        for col in ["Space2", "Space3", "Space4", "Space5", "Space6"]:
            if col in df.columns:
                # Should have at least some NaN values
                assert df[col].isna().sum() > 0, f"{col} should have NaN values"
                # NaN values should be actual np.nan, not strings
                non_null_values = df[col].dropna()
                if len(non_null_values) > 0:
                    assert all(isinstance(v, (float, int)) for v in non_null_values)

    def test_load_json_from_string(self):
        """Test loading JSON from JSON string."""
        json_str = json.dumps([
            {"DateTimeStr": "2025-01-01", "Temperature": 10.0, "Space1": 100.0, "Space2": "NaN"},
            {"DateTimeStr": "2025-01-02", "Temperature": 11.0, "Space1": 101.0, "Space2": 200.0},
        ])
        df = load_json(json_str)

        assert len(df) == 2
        assert df["Temperature"].tolist() == [10.0, 11.0]
        assert df["Space1"].tolist() == [100.0, 101.0]
        assert pd.isna(df["Space2"].iloc[0])
        assert df["Space2"].iloc[1] == 200.0

    def test_load_json_empty_array_raises_error(self):
        """Test that empty JSON array raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            load_json("[]")

    def test_load_json_invalid_format_raises_error(self):
        """Test that invalid JSON format raises ValueError."""
        with pytest.raises(ValueError, match="array"):
            load_json('{"key": "value"}')  # Not an array

    def test_load_json_file_not_found(self):
        """Test that non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_json("/nonexistent/path/file.json")


class TestDetectValidChannels:
    """Tests for detect_valid_channels function."""

    def test_detect_valid_channels_all_valid(self):
        """Test with all channels having valid data."""
        json_path = TEST_DATA_DIR / "AFReport_SP_20250507_102452.json"
        df = load_json(json_path)

        valid = detect_valid_channels(df)

        # All 6 channels should be valid in this file
        assert len(valid) == 6
        assert "Space1" in valid
        assert "Space6" in valid

    def test_detect_valid_channels_partial_valid(self):
        """Test with only some channels having valid data."""
        json_path = TEST_DATA_DIR / "AFReport_SP_20250519_171458.json"
        df = load_json(json_path)

        valid = detect_valid_channels(df)

        # Only Space1 should be valid in this file
        assert valid == ["Space1"]

    def test_detect_valid_channels_all_nan(self):
        """Test with channels that are all NaN."""
        df = pd.DataFrame({
            "Temperature": [10.0, 11.0],
            "Space1": [np.nan, np.nan],
            "Space2": [np.nan, np.nan],
        })

        valid = detect_valid_channels(df)

        # No valid channels
        assert valid == []

    def test_detect_valid_channels_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame(columns=["Temperature", "Space1", "Space2"])

        valid = detect_valid_channels(df)

        # Should return empty list for empty DataFrame
        assert valid == []

    def test_detect_valid_channels_no_space_columns_raises_error(self):
        """Test that DataFrame without Space columns raises ValueError."""
        df = pd.DataFrame({"Temperature": [10.0, 11.0]})

        with pytest.raises(ValueError, match="Space"):
            detect_valid_channels(df)

    def test_detect_valid_channels_single_non_nan(self):
        """Test that a channel with at least one non-NaN value is considered valid."""
        df = pd.DataFrame({
            "Temperature": [10.0, 11.0, 12.0],
            "Space1": [np.nan, 100.0, np.nan],  # One valid value
            "Space2": [np.nan, np.nan, np.nan],  # All NaN
        })

        valid = detect_valid_channels(df)

        assert valid == ["Space1"]


class TestLoadExcel:
    """Tests for load_excel function."""

    def test_load_excel_basic(self):
        """Test loading Excel from file path."""
        # Create a temporary Excel file with test data
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Create test DataFrame
            test_df = pd.DataFrame({
                "DateTimeStr": ["2025-01-01 10:00:00", "2025-01-01 10:00:01"],
                "Temperature": [10.0, 11.0],
                "Space1": [100.0, 101.0],
                "Space2": [200.0, 201.0],
                "Space3": [300.0, 301.0],
            })
            test_df.to_excel(temp_path, index=False, engine="openpyxl")

            # Load the file
            df = load_excel(temp_path)

            # Check structure
            assert isinstance(df, pd.DataFrame)
            assert "Temperature" in df.columns
            assert "Space1" in df.columns
            assert len(df) == 2
            assert df["Temperature"].tolist() == [10.0, 11.0]
            assert df["Space1"].tolist() == [100.0, 101.0]
        finally:
            temp_path.unlink(missing_ok=True)

    def test_load_excel_with_nan(self):
        """Test that Excel handles missing values correctly."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Create test DataFrame with NaN
            test_df = pd.DataFrame({
                "DateTimeStr": ["2025-01-01 10:00:00", "2025-01-01 10:00:01"],
                "Temperature": [10.0, 11.0],
                "Space1": [100.0, np.nan],
                "Space2": [200.0, 201.0],
            })
            test_df.to_excel(temp_path, index=False, engine="openpyxl")

            # Load the file
            df = load_excel(temp_path)

            assert pd.isna(df["Space1"].iloc[1])
            assert df["Space2"].iloc[1] == 201.0
        finally:
            temp_path.unlink(missing_ok=True)

    def test_load_excel_file_not_found(self):
        """Test that non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_excel("/nonexistent/path/file.xlsx")


class TestLoadCsv:
    """Tests for load_csv function."""

    def test_load_csv_basic(self):
        """Test loading CSV from file path."""
        # Create a temporary CSV file with test data
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            temp_path = Path(f.name)
            f.write("DateTimeStr,Temperature,Space1,Space2,Space3\n")
            f.write("2025-01-01 10:00:00,10.0,100.0,200.0,300.0\n")
            f.write("2025-01-01 10:00:01,11.0,101.0,201.0,301.0\n")

        try:
            # Load the file
            df = load_csv(temp_path)

            # Check structure
            assert isinstance(df, pd.DataFrame)
            assert "Temperature" in df.columns
            assert "Space1" in df.columns
            assert len(df) == 2
            assert df["Temperature"].tolist() == [10.0, 11.0]
            assert df["Space1"].tolist() == [100.0, 101.0]
        finally:
            temp_path.unlink(missing_ok=True)

    def test_load_csv_with_missing_values(self):
        """Test that CSV handles missing values correctly."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            temp_path = Path(f.name)
            f.write("DateTimeStr,Temperature,Space1,Space2\n")
            f.write("2025-01-01 10:00:00,10.0,100.0,200.0\n")
            f.write("2025-01-01 10:00:01,11.0,,201.0\n")  # Empty Space1

        try:
            # Load the file
            df = load_csv(temp_path)

            assert pd.isna(df["Space1"].iloc[1])
            assert df["Space2"].iloc[1] == 201.0
        finally:
            temp_path.unlink(missing_ok=True)

    def test_load_csv_file_not_found(self):
        """Test that non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_csv("/nonexistent/path/file.csv")


class TestLoadFile:
    """Tests for load_file unified interface."""

    def test_load_file_json(self):
        """Test load_file with JSON extension."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            temp_path = Path(f.name)
            json.dump([
                {"DateTimeStr": "2025-01-01", "Temperature": 10.0, "Space1": 100.0},
                {"DateTimeStr": "2025-01-02", "Temperature": 11.0, "Space1": 101.0},
            ], f)

        try:
            df = load_file(temp_path)
            assert len(df) == 2
            assert df["Temperature"].tolist() == [10.0, 11.0]
        finally:
            temp_path.unlink(missing_ok=True)

    def test_load_file_excel(self):
        """Test load_file with Excel extension."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            temp_path = Path(f.name)

        try:
            test_df = pd.DataFrame({
                "DateTimeStr": ["2025-01-01"],
                "Temperature": [10.0],
                "Space1": [100.0],
            })
            test_df.to_excel(temp_path, index=False, engine="openpyxl")

            df = load_file(temp_path)
            assert len(df) == 1
            assert df["Temperature"].iloc[0] == 10.0
        finally:
            temp_path.unlink(missing_ok=True)

    def test_load_file_csv(self):
        """Test load_file with CSV extension."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            temp_path = Path(f.name)
            f.write("DateTimeStr,Temperature,Space1\n")
            f.write("2025-01-01,10.0,100.0\n")

        try:
            df = load_file(temp_path)
            assert len(df) == 1
            assert df["Temperature"].iloc[0] == 10.0
        finally:
            temp_path.unlink(missing_ok=True)

    def test_load_file_unsupported_extension(self):
        """Test that unsupported extension raises ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Unsupported"):
                load_file(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_load_file_bytes_json(self):
        """Test load_file with bytes input (JSON)."""
        json_bytes = json.dumps([
            {"DateTimeStr": "2025-01-01", "Temperature": 10.0, "Space1": 100.0}
        ]).encode("utf-8")

        df = load_file(json_bytes)
        assert len(df) == 1
        assert df["Temperature"].iloc[0] == 10.0

    def test_load_file_bytes_json_with_filename(self):
        """Test load_file with bytes input and explicit JSON filename."""
        json_bytes = json.dumps([
            {"DateTimeStr": "2025-01-01", "Temperature": 10.0, "Space1": 100.0}
        ]).encode("utf-8")

        df = load_file(json_bytes, file_name="data.json")
        assert len(df) == 1
        assert df["Temperature"].iloc[0] == 10.0

    def test_load_file_bytes_excel(self):
        """Test load_file with bytes input for Excel file."""
        # Create a temporary Excel file and read its bytes
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            temp_path = Path(f.name)

        try:
            test_df = pd.DataFrame({
                "DateTimeStr": ["2025-01-01 10:00:00"],
                "Temperature": [15.0],
                "Space1": [150.0],
                "Space2": [250.0],
            })
            test_df.to_excel(temp_path, index=False, engine="openpyxl")

            # Read the file as bytes
            with open(temp_path, "rb") as f:
                excel_bytes = f.read()

            # Load using bytes + filename
            df = load_file(excel_bytes, file_name="test.xlsx")

            assert len(df) == 1
            assert df["Temperature"].iloc[0] == 15.0
            assert df["Space1"].iloc[0] == 150.0
        finally:
            temp_path.unlink(missing_ok=True)

    def test_load_file_bytes_csv(self):
        """Test load_file with bytes input for CSV file."""
        # Create CSV content as bytes
        csv_content = "DateTimeStr,Temperature,Space1,Space2\n2025-01-01 10:00:00,20.0,200.0,300.0\n"
        csv_bytes = csv_content.encode("utf-8")

        # Load using bytes + filename
        df = load_file(csv_bytes, file_name="test.csv")

        assert len(df) == 1
        assert df["Temperature"].iloc[0] == 20.0
        assert df["Space1"].iloc[0] == 200.0

    def test_load_file_bytes_unsupported_extension(self):
        """Test load_file with bytes and unsupported extension raises ValueError."""
        test_bytes = b"some content"

        with pytest.raises(ValueError, match="Unsupported"):
            load_file(test_bytes, file_name="test.txt")

    def test_load_file_consistent_structure(self):
        """Test that all formats return consistent DataFrame structure."""
        test_data = pd.DataFrame({
            "DateTimeStr": ["2025-01-01", "2025-01-02"],
            "Temperature": [10.0, 11.0],
            "Space1": [100.0, 101.0],
            "Space2": [200.0, 201.0],
        })

        # Create files in all formats
        temp_files = []

        try:
            # JSON
            json_path = Path(tempfile.mktemp(suffix=".json"))
            with open(json_path, "w") as f:
                json.dump(test_data.to_dict(orient="records"), f)
            temp_files.append(json_path)

            # Excel
            excel_path = Path(tempfile.mktemp(suffix=".xlsx"))
            test_data.to_excel(excel_path, index=False, engine="openpyxl")
            temp_files.append(excel_path)

            # CSV
            csv_path = Path(tempfile.mktemp(suffix=".csv"))
            test_data.to_csv(csv_path, index=False)
            temp_files.append(csv_path)

            # Load and compare
            df_json = load_file(json_path)
            df_excel = load_file(excel_path)
            df_csv = load_file(csv_path)

            # All should have same columns
            assert set(df_json.columns) == set(df_excel.columns) == set(df_csv.columns)

            # All should have same length
            assert len(df_json) == len(df_excel) == len(df_csv) == 2

            # Temperature values should be identical
            assert df_json["Temperature"].tolist() == df_excel["Temperature"].tolist() == df_csv["Temperature"].tolist()

        finally:
            for path in temp_files:
                path.unlink(missing_ok=True)
