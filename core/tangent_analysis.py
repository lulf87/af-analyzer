"""
Tangent analysis module for Af Analyzer.

Implements the tangent method for determining phase transformation temperatures
according to YY/T 1771-2021 Section 11.
"""

from typing import Optional, Tuple

import numpy as np
from scipy.stats import linregress


def compute_derivative(temps: np.ndarray, values: np.ndarray) -> np.ndarray:
    """
    Compute the derivative of values with respect to temperature.

    Uses numpy.gradient to calculate dValue/dTemperature.
    This represents the slope of the curve at each temperature point.

    Args:
        temps: Temperature values (1D array)
        values: Channel values (1D array, same length as temps)

    Returns:
        Derivative values (1D array, same length as input)
        - dValue/dTemperature at each temperature point

    Raises:
        ValueError: If temps and values have different lengths

    Examples:
        >>> temps = np.array([10.0, 11.0, 12.0, 13.0])
        >>> values = np.array([100.0, 110.0, 125.0, 130.0])
        >>> deriv = compute_derivative(temps, values)
        >>> # deriv will contain dValue/dTemperature at each point
    """
    temps = np.asarray(temps)
    values = np.asarray(values)

    if len(temps) != len(values):
        raise ValueError(f"Length mismatch: temps ({len(temps)}) != values ({len(values)})")

    if len(temps) < 2:
        raise ValueError(f"Need at least 2 points to compute derivative, got {len(temps)}")

    # Compute derivative using gradient
    # np.gradient handles non-uniform spacing correctly
    derivatives = np.gradient(values, temps)

    return derivatives


def find_max_slope_index(derivatives: np.ndarray, offset: int = 0) -> int:
    """
    Find the index of the maximum absolute derivative value.

    This represents the point of steepest slope on the curve,
    which is used as the tangent point in the tangent method.

    Args:
        derivatives: Array of derivative values (dValue/dTemperature)
        offset: Manual adjustment to the found index
            - Positive: shift toward higher temperature (end of array)
            - Negative: shift toward lower temperature (start of array)
            - Default: 0 (no offset)

    Returns:
        Index of the point with maximum absolute derivative, adjusted by offset
        - Index is clipped to valid range [0, len(derivatives) - 1]

    Raises:
        ValueError: If derivatives array is empty

    Examples:
        >>> derivs = np.array([0.1, 0.5, 1.2, 0.8, 0.3])
        >>> idx = find_max_slope_index(derivs)  # Returns 2 (max abs value)
        >>> idx_with_offset = find_max_slope_index(derivs, offset=1)  # Returns 3
    """
    derivatives = np.asarray(derivatives)

    if len(derivatives) == 0:
        raise ValueError("derivatives array cannot be empty")

    # Find index of maximum absolute derivative
    max_abs_idx = int(np.argmax(np.abs(derivatives)))

    # Apply offset
    adjusted_idx = max_abs_idx + offset

    # Clip to valid range
    n = len(derivatives)
    adjusted_idx = max(0, min(adjusted_idx, n - 1))

    return adjusted_idx


def fit_baseline(
    temps: np.ndarray,
    values: np.ndarray,
    t_start: float,
    t_end: float
) -> Tuple[float, float]:
    """
    Fit a linear baseline to data within a specified temperature range.

    Performs linear least squares regression on data points where
    t_start <= temperature <= t_end.

    Args:
        temps: Temperature values (1D array)
        values: Channel values (1D array, same length as temps)
        t_start: Start temperature for baseline fitting
        t_end: End temperature for baseline fitting

    Returns:
        Tuple of (slope, intercept) for the fitted line
        - slope: dValue/dTemperature of the baseline
        - intercept: Value at temperature = 0

    Raises:
        ValueError: If no data points in the specified range
        ValueError: If fewer than 2 points for fitting

    Examples:
        >>> temps = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
        >>> values = np.array([100.0, 101.0, 102.0, 103.0, 104.0])
        >>> slope, intercept = fit_baseline(temps, values, 10.0, 12.0)
    """
    temps = np.asarray(temps)
    values = np.asarray(values)

    # Select data within temperature range
    mask = (temps >= t_start) & (temps <= t_end)
    temps_range = temps[mask]
    values_range = values[mask]

    if len(temps_range) == 0:
        raise ValueError(f"No data points in temperature range [{t_start}, {t_end}]")

    if len(temps_range) < 2:
        raise ValueError(f"Need at least 2 points for baseline fitting, got {len(temps_range)}")

    # Perform linear regression
    result = linregress(temps_range, values_range)

    return result.slope, result.intercept


def compute_tangent_at_point(
    temps: np.ndarray,
    values: np.ndarray,
    derivatives: np.ndarray,
    index: int
) -> Tuple[float, float]:
    """
    Compute the tangent line at a specific point on the curve.

    The tangent line uses the derivative value at the specified index
    as its slope, and passes through the point (temps[index], values[index]).

    Args:
        temps: Temperature values (1D array)
        values: Channel values (1D array)
        derivatives: Derivative values at each point (1D array)
        index: Index of the point where tangent is computed

    Returns:
        Tuple of (slope, intercept) for the tangent line

    Raises:
        ValueError: If index is out of bounds
        ValueError: If arrays have different lengths

    Examples:
        >>> temps = np.array([10.0, 11.0, 12.0])
        >>> values = np.array([100.0, 110.0, 125.0])
        >>> derivs = np.array([10.0, 15.0, 20.0])
        >>> slope, intercept = compute_tangent_at_point(temps, values, derivs, 1)
    """
    temps = np.asarray(temps)
    values = np.asarray(values)
    derivatives = np.asarray(derivatives)

    if not (0 <= index < len(temps)):
        raise ValueError(f"Index {index} out of bounds [0, {len(temps) - 1}]")

    if len(temps) != len(values) or len(temps) != len(derivatives):
        raise ValueError("temps, values, and derivatives must have the same length")

    # Slope is the derivative at the point
    slope = derivatives[index]

    # Line passes through (temps[index], values[index])
    # intercept = y - slope * x
    x0 = temps[index]
    y0 = values[index]
    intercept = y0 - slope * x0

    return slope, intercept


def find_intersection(
    slope1: float,
    intercept1: float,
    slope2: float,
    intercept2: float
) -> Optional[float]:
    """
    Find the temperature at which two lines intersect.

    Lines are defined as: y = slope * x + intercept

    Args:
        slope1, intercept1: First line parameters
        slope2, intercept2: Second line parameters

    Returns:
        Temperature (x-coordinate) of intersection, or np.nan if lines are parallel

    Examples:
        >>> # Line 1: y = 2x + 10
        >>> # Line 2: y = -x + 25
        >>> # Intersection at x = 5
        >>> find_intersection(2, 10, -1, 25)
        5.0
    """
    # Check for parallel lines
    if np.isclose(slope1, slope2):
        return np.nan

    # Solve: slope1 * x + intercept1 = slope2 * x + intercept2
    # x = (intercept2 - intercept1) / (slope1 - slope2)
    x = (intercept2 - intercept1) / (slope1 - slope2)

    return x


def analyze_channel(
    temps: np.ndarray,
    values: np.ndarray,
    low_range: Tuple[float, float],
    high_range: Tuple[float, float],
    smooth_params: Tuple[int, int] = (51, 3),
    slope_offset: int = 0,
    outlier_params: Tuple[int, float] = (5, 5.0)
) -> dict:
    """
    Perform complete tangent analysis on a channel.

    This is the high-level interface that computes:
    1. Outlier detection and removal (rolling median + MAD threshold)
    2. Low-temperature baseline (martensite phase)
    3. High-temperature baseline (austenite phase)
    4. Middle tangent line (at maximum slope point)
    5. Intersection temperatures: As (tangent ∩ low baseline) and Af-tan (tangent ∩ high baseline)

    Args:
        temps: Temperature values (1D array)
        values: Channel values (1D array)
        low_range: (t_start, t_end) for low-temperature baseline fitting
        high_range: (t_start, t_end) for high-temperature baseline fitting
        smooth_params: (window_length, polyorder) for Savitzky-Golay smoothing
        slope_offset: Manual adjustment for max slope point index
        outlier_params: (window, threshold) for outlier detection
            - window: Rolling window size for median (default: 5)
            - threshold: MAD multiplier (default: 5.0)

    Returns:
        Dictionary containing:
            - As: Austenite start temperature (tangent ∩ low baseline)
            - Af_tan: Austenite finish temperature by tangent method (tangent ∩ high baseline)
            - max_slope_temp: Temperature at maximum slope point
            - low_baseline: (slope, intercept) of low-temperature baseline
            - high_baseline: (slope, intercept) of high-temperature baseline
            - tangent: (slope, intercept) of middle tangent line
            - outlier_count: Number of outliers detected and removed

    Raises:
        ValueError: If analysis fails due to invalid parameters or data

    Examples:
        >>> temps = np.linspace(0, 30, 100)
        >>> values = np.tanh((temps - 15) / 2) * 50 + 100
        >>> result = analyze_channel(temps, values, (0, 5), (25, 30))
        >>> print(f"As = {result['As']:.2f}, Af-tan = {result['Af_tan']:.2f}")
    """
    from core.preprocessing import smooth_data, remove_outliers

    temps = np.asarray(temps)
    values = np.asarray(values)

    if len(temps) != len(values):
        raise ValueError("temps and values must have the same length")

    if len(temps) < 10:
        raise ValueError(f"Need at least 10 points for analysis, got {len(temps)}")

    # Step 1: Remove outliers (rolling median + MAD threshold)
    outlier_window, outlier_threshold = outlier_params
    temps_clean, values_clean, outlier_mask = remove_outliers(
        temps, values, window=outlier_window, threshold=outlier_threshold
    )
    outlier_count = int(np.sum(outlier_mask))

    # Step 2: Smooth the data
    window_length, polyorder = smooth_params
    temps_smooth, values_smooth = smooth_data(temps_clean, values_clean, window_length, polyorder)

    # Step 3: Compute derivatives
    derivatives = compute_derivative(temps_smooth, values_smooth)

    # Step 4: Find maximum slope point
    max_slope_idx = find_max_slope_index(derivatives, offset=slope_offset)
    max_slope_temp = temps_smooth[max_slope_idx]

    # Step 5: Compute tangent line at max slope point
    tangent_slope, tangent_intercept = compute_tangent_at_point(
        temps_smooth, values_smooth, derivatives, max_slope_idx
    )

    # Step 6: Fit low-temperature baseline
    low_t_start, low_t_end = low_range
    low_slope, low_intercept = fit_baseline(temps_smooth, values_smooth, low_t_start, low_t_end)

    # Step 7: Fit high-temperature baseline
    high_t_start, high_t_end = high_range
    high_slope, high_intercept = fit_baseline(temps_smooth, values_smooth, high_t_start, high_t_end)

    # Step 8: Compute intersections
    As = find_intersection(tangent_slope, tangent_intercept, low_slope, low_intercept)
    Af_tan = find_intersection(tangent_slope, tangent_intercept, high_slope, high_intercept)

    return {
        "As": As,
        "Af_tan": Af_tan,
        "max_slope_temp": max_slope_temp,
        "low_baseline": (low_slope, low_intercept),
        "high_baseline": (high_slope, high_intercept),
        "tangent": (tangent_slope, tangent_intercept),
        "outlier_count": outlier_count,
    }
