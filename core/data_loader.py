"""
Data loader module for Af Analyzer.

Supports loading JSON, Excel, and CSV files exported from the testing equipment.
"""

import json
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd


# Channel columns in the data
CHANNEL_COLUMNS = ["Space1", "Space2", "Space3", "Space4", "Space5", "Space6"]

# Supported file extensions for auto-detection
SUPPORTED_EXTENSIONS = {
    ".json": "json",
    ".xlsx": "excel",
    ".xls": "excel",
    ".csv": "csv",
}


def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize DataFrame to ensure consistent column types.

    Converts Space columns to numeric, handling string "NaN" values.

    Args:
        df: Input DataFrame

    Returns:
        Normalized DataFrame with Space columns as numeric
    """
    df = df.copy()
    for col in CHANNEL_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_json(file_or_path: Union[str, Path, bytes]) -> pd.DataFrame:
    """
    Load JSON data exported from testing equipment.

    The input should be a JSON array of objects with fields:
    - DateTimeStr: timestamp string
    - Temperature: temperature value in Celsius
    - Space1~Space6: displacement/deformation values (may be "NaN" strings)

    Args:
        file_or_path: Path to JSON file, or file-like object, or JSON string/bytes

    Returns:
        DataFrame with columns [DateTimeStr, Temperature, Space1, Space2, ..., Space6]
        - "NaN" strings are converted to np.nan
        - Temperature is kept as-is

    Raises:
        ValueError: If the JSON format is invalid or empty
        FileNotFoundError: If the file path does not exist
    """
    # Handle different input types
    if isinstance(file_or_path, bytes):
        data = json.loads(file_or_path.decode("utf-8"))
    elif isinstance(file_or_path, (str, Path)):
        # Try to parse as JSON string first, then as file path
        try:
            if isinstance(file_or_path, str):
                data = json.loads(file_or_path)
            else:
                # Path object - treat as file path
                raise ValueError("Not a JSON string")
        except (json.JSONDecodeError, ValueError):
            # Not a valid JSON string, treat as file path
            path = Path(file_or_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            content = path.read_text(encoding="utf-8")
            data = json.loads(content)
    else:
        # Assume it's a file-like object with read() method
        data = json.load(file_or_path)

    # Validate data format
    if not isinstance(data, list):
        raise ValueError("JSON data must be an array of objects")

    if len(data) == 0:
        raise ValueError("JSON data is empty")

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Normalize DataFrame (convert Space columns to numeric)
    df = _normalize_dataframe(df)

    return df


def load_excel(file_or_path: Union[str, Path]) -> pd.DataFrame:
    """
    Load Excel data exported from testing equipment.

    The Excel file should have columns matching the JSON format:
    - DateTimeStr: timestamp string
    - Temperature: temperature value in Celsius
    - Space1~Space6: displacement/deformation values

    Args:
        file_or_path: Path to Excel file (.xlsx or .xls)

    Returns:
        DataFrame with columns [DateTimeStr, Temperature, Space1, Space2, ..., Space6]
        - Space columns are converted to numeric type
        - Missing/invalid values become np.nan

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file is empty or has invalid format
    """
    path = Path(file_or_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Read Excel file (first sheet)
    df = pd.read_excel(path, engine="openpyxl" if path.suffix == ".xlsx" else "xlrd")

    if df.empty:
        raise ValueError("Excel file is empty")

    # Normalize DataFrame
    df = _normalize_dataframe(df)

    return df


def load_csv(file_or_path: Union[str, Path], encoding: str = "utf-8") -> pd.DataFrame:
    """
    Load CSV data exported from testing equipment.

    The CSV file should have columns matching the JSON format:
    - DateTimeStr: timestamp string
    - Temperature: temperature value in Celsius
    - Space1~Space6: displacement/deformation values

    Args:
        file_or_path: Path to CSV file
        encoding: File encoding (default: utf-8)

    Returns:
        DataFrame with columns [DateTimeStr, Temperature, Space1, Space2, ..., Space6]
        - Space columns are converted to numeric type
        - Missing/invalid values become np.nan

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file is empty
    """
    path = Path(file_or_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Read CSV file
    df = pd.read_csv(path, encoding=encoding)

    if df.empty:
        raise ValueError("CSV file is empty")

    # Normalize DataFrame
    df = _normalize_dataframe(df)

    return df


def load_file(
    file_or_path: Union[str, Path, bytes],
    file_name: Union[str, Path, None] = None
) -> pd.DataFrame:
    """
    Load data from a file, auto-detecting format by extension.

    Supported formats:
    - .json: JSON file (array of objects)
    - .xlsx, .xls: Excel file
    - .csv: CSV file

    Args:
        file_or_path: Path to file, or bytes for file content
        file_name: Optional file name/path to determine format when file_or_path is bytes.
                   Required when file_or_path is bytes for non-JSON formats.

    Returns:
        DataFrame with consistent column structure across all formats

    Raises:
        ValueError: If file format is not supported or file_name is missing for bytes input
        FileNotFoundError: If the file does not exist

    Examples:
        >>> df = load_file("data.json")
        >>> df = load_file("data.xlsx")
        >>> df = load_file("data.csv")
        >>> # For bytes input (e.g., from Streamlit file uploader):
        >>> df = load_file(uploaded_file.read(), file_name=uploaded_file.name)
    """
    import tempfile

    # Handle bytes input
    if isinstance(file_or_path, bytes):
        # Determine format from file_name
        if file_name is None:
            # Default to JSON for backwards compatibility
            return load_json(file_or_path)

        ext = Path(file_name).suffix.lower()

        if ext == ".json":
            return load_json(file_or_path)
        elif ext in (".xlsx", ".xls"):
            # Write bytes to temp file and load
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(file_or_path)
                tmp_path = Path(tmp.name)
            try:
                return load_excel(tmp_path)
            finally:
                tmp_path.unlink(missing_ok=True)
        elif ext == ".csv":
            # Write bytes to temp file and load
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(file_or_path)
                tmp_path = Path(tmp.name)
            try:
                return load_csv(tmp_path)
            finally:
                tmp_path.unlink(missing_ok=True)
        else:
            supported = ", ".join(SUPPORTED_EXTENSIONS.keys())
            raise ValueError(
                f"Unsupported file extension: {ext}. "
                f"Supported formats: {supported}"
            )

    path = Path(file_or_path)
    ext = path.suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(SUPPORTED_EXTENSIONS.keys())
        raise ValueError(
            f"Unsupported file extension: {ext}. "
            f"Supported formats: {supported}"
        )

    file_type = SUPPORTED_EXTENSIONS[ext]

    if file_type == "json":
        return load_json(path)
    elif file_type == "excel":
        return load_excel(path)
    elif file_type == "csv":
        return load_csv(path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def detect_valid_channels(df: pd.DataFrame) -> list[str]:
    """
    Detect which channels have valid (non-NaN) data.

    A channel is considered valid if it has at least one non-NaN value.

    Args:
        df: DataFrame with Space1~Space6 columns

    Returns:
        List of channel names that have valid data (e.g., ["Space1", "Space2"])

    Raises:
        ValueError: If DataFrame doesn't contain any Space columns
    """
    if df.empty:
        return []

    # Find Space columns that exist in the DataFrame
    space_cols = [col for col in CHANNEL_COLUMNS if col in df.columns]

    if not space_cols:
        raise ValueError("DataFrame must contain at least one Space column")

    # A channel is valid if it has at least one non-NaN value
    valid_channels = []
    for col in space_cols:
        if df[col].notna().any():
            valid_channels.append(col)

    return valid_channels
