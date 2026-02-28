"""
Data preprocessing module for Af Analyzer.

Handles temperature grouping, outlier detection/removal, and smoothing of high-frequency sampling data.
"""

from typing import Tuple

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter


def remove_outliers(
    temps: np.ndarray,
    values: np.ndarray,
    window: int = 11,
    threshold: float = 5.0,
    max_iterations: int = 3
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Detect and remove outliers using iterative rolling median + MAD threshold method.

    Handles both isolated spikes (1-2 points) and consecutive anomaly blocks
    (e.g., sensor dropout producing 3-5 consecutive zero/abnormal values).

    Algorithm (per iteration):
    1. Compute rolling median of the values (large window resists consecutive outliers)
    2. Calculate deviation of each point from the rolling median
    3. Compute MAD (Median Absolute Deviation) as robust scale estimate
    4. Mark points where deviation > threshold × MAD as outliers
    5. Replace outliers with linear interpolation from neighboring normal points
    6. Repeat until no new outliers found or max_iterations reached

    Args:
        temps: Temperature values (1D array)
        values: Channel values (1D array, same length as temps)
        window: Rolling window size for median calculation (default: 11).
            Must be larger than 2× the widest expected anomaly block.
        threshold: MAD multiplier for outlier detection (default: 5.0)
        max_iterations: Maximum number of detection passes (default: 3)

    Returns:
        Tuple of (temps_clean, values_clean, outlier_mask)
        - temps_clean: Temperature values (unchanged)
        - values_clean: Values with outliers replaced by interpolation
        - outlier_mask: Boolean array (True = outlier detected across all iterations)
    """
    temps = np.asarray(temps, dtype=float)
    values = np.asarray(values, dtype=float)

    if len(temps) != len(values):
        raise ValueError(f"Length mismatch: temps ({len(temps)}) != values ({len(values)})")

    n = len(values)
    if n < window + 2:
        return temps.copy(), values.copy(), np.zeros(n, dtype=bool)

    # Adaptive window: ensure window is large enough relative to data
    window = max(window, 11)
    if window % 2 == 0:
        window += 1

    combined_mask = np.zeros(n, dtype=bool)
    working_values = values.copy()

    for iteration in range(max_iterations):
        s = pd.Series(working_values)
        rolling_med = s.rolling(
            window=window, center=True, min_periods=window // 2 + 1
        ).median().values

        deviations = np.abs(working_values - rolling_med)

        # Compute MAD from non-outlier, non-boundary points
        boundary = max(window // 2, 3)
        inner_mask = np.ones(n, dtype=bool)
        inner_mask[:boundary] = False
        inner_mask[-boundary:] = False
        inner_mask[combined_mask] = False  # exclude already-detected outliers
        valid_devs = deviations[inner_mask & ~np.isnan(deviations)]

        if len(valid_devs) == 0:
            break

        mad = np.median(valid_devs)
        if mad == 0 or np.isnan(mad):
            data_range = np.nanmax(working_values) - np.nanmin(working_values)
            mad = max(data_range * 0.01, 1.0)

        outlier_threshold = threshold * mad
        new_mask = deviations > outlier_threshold
        new_mask[:boundary] = False
        new_mask[-boundary:] = False
        # Don't re-flag already-handled points
        new_mask[combined_mask] = False

        if not np.any(new_mask):
            break

        # Interpolate newly detected outliers from normal neighbors
        combined_mask |= new_mask
        normal_idx = np.where(~combined_mask)[0]
        outlier_idx = np.where(combined_mask)[0]

        if len(normal_idx) >= 2:
            working_values[outlier_idx] = np.interp(
                outlier_idx, normal_idx, values[~combined_mask]
            )

    return temps, working_values, combined_mask


def group_by_temperature(df: pd.DataFrame, channel: str) -> pd.DataFrame:
    """
    Group data by Temperature and calculate mean values for the specified channel.

    Raw data contains many samples at the same temperature (high-frequency sampling).
    This function aggregates them to get one value per temperature.

    Args:
        df: Input DataFrame with Temperature and channel columns
        channel: Channel name (e.g., "Space1", "Space2", ...)

    Returns:
        DataFrame with two columns: [Temperature, channel]
        - Each unique temperature has one row with the mean value
        - Sorted by Temperature in ascending order

    Raises:
        ValueError: If channel is not found in DataFrame

    Examples:
        >>> df = pd.DataFrame({
        ...     "Temperature": [10.0, 10.0, 11.0, 11.0],
        ...     "Space1": [100.0, 101.0, 110.0, 111.0],
        ... })
        >>> result = group_by_temperature(df, "Space1")
        >>> result
           Temperature  Space1
        0         10.0   100.5
        1         11.0   110.5
    """
    if channel not in df.columns:
        raise ValueError(f"Channel '{channel}' not found in DataFrame columns: {df.columns.tolist()}")

    if "Temperature" not in df.columns:
        raise ValueError("DataFrame must contain 'Temperature' column")

    # Group by Temperature and calculate mean
    grouped = df.groupby("Temperature", as_index=False)[channel].mean()

    # Sort by temperature (ascending)
    grouped = grouped.sort_values("Temperature").reset_index(drop=True)

    # Remove rows where channel value is NaN
    grouped = grouped.dropna(subset=[channel])

    return grouped


def smooth_data(
    temps: np.ndarray,
    values: np.ndarray,
    window_length: int = 51,
    polyorder: int = 3
) -> tuple[np.ndarray, np.ndarray]:
    """
    Apply Savitzky-Golay smoothing filter to data.

    The Savitzky-Golay filter smooths data by fitting a polynomial
    to a sliding window of data points. It preserves peak shapes better
    than moving average filters.

    Args:
        temps: Temperature values (1D array)
        values: Channel values to smooth (1D array, same length as temps)
        window_length: Length of the filter window (must be odd, will be corrected if even)
        polyorder: Order of the polynomial used to fit the samples

    Returns:
        Tuple of (temperatures, smoothed_values) - both 1D arrays of same length as input

    Raises:
        ValueError: If window_length <= polyorder after correction
        ValueError: If temps and values have different lengths
        ValueError: If window_length is larger than data length

    Notes:
        - window_length is automatically corrected to odd number (if even, +1)
        - window_length must be greater than polyorder
        - For best results, window_length should be significantly larger than polyorder

    Examples:
        >>> temps = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
        >>> values = np.array([100.0, 102.0, 101.0, 103.0, 102.0])
        >>> temps_smooth, values_smooth = smooth_data(temps, values, window_length=3, polyorder=1)
    """
    temps = np.asarray(temps)
    values = np.asarray(values)

    # Validate inputs
    if len(temps) != len(values):
        raise ValueError(f"Length mismatch: temps ({len(temps)}) != values ({len(values)})")

    if len(temps) == 0:
        return np.array([]), np.array([])

    # Correct window_length to odd number
    if window_length % 2 == 0:
        window_length = window_length + 1

    # Validate window_length vs polyorder
    if window_length <= polyorder:
        raise ValueError(
            f"window_length ({window_length}) must be greater than polyorder ({polyorder})"
        )

    # Validate window_length vs data length
    if window_length > len(values):
        raise ValueError(
            f"window_length ({window_length}) cannot be larger than data length ({len(values)})"
        )

    # Apply Savitzky-Golay filter
    smoothed_values = savgol_filter(values, window_length, polyorder)

    return temps, smoothed_values
