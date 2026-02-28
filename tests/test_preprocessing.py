"""
Tests for preprocessing module.
"""

import numpy as np
import pandas as pd
import pytest

from core.preprocessing import group_by_temperature, smooth_data, remove_outliers


class TestGroupByTemperature:
    """Tests for group_by_temperature function."""

    def test_group_by_temperature_basic(self):
        """Test basic grouping functionality."""
        df = pd.DataFrame({
            "Temperature": [10.0, 10.0, 11.0, 11.0, 12.0],
            "Space1": [100.0, 102.0, 110.0, 112.0, 120.0],
        })

        result = group_by_temperature(df, "Space1")

        # Should have 3 rows (one per unique temperature)
        assert len(result) == 3
        assert list(result.columns) == ["Temperature", "Space1"]

        # Check means are calculated correctly
        assert result["Temperature"].tolist() == [10.0, 11.0, 12.0]
        assert result["Space1"].tolist() == [101.0, 111.0, 120.0]

    def test_group_by_temperature_sorted(self):
        """Test that results are sorted by temperature."""
        df = pd.DataFrame({
            "Temperature": [12.0, 10.0, 11.0],
            "Space1": [120.0, 100.0, 110.0],
        })

        result = group_by_temperature(df, "Space1")

        # Should be sorted ascending
        assert result["Temperature"].tolist() == [10.0, 11.0, 12.0]

    def test_group_by_temperature_with_nan(self):
        """Test handling of NaN values in channel."""
        df = pd.DataFrame({
            "Temperature": [10.0, 10.0, 11.0, 11.0],
            "Space1": [100.0, np.nan, 110.0, 112.0],
        })

        result = group_by_temperature(df, "Space1")

        # Temperature 10.0 should have mean of non-NaN values
        # Temperature 11.0 should have mean 111.0
        assert len(result) == 2
        assert result["Temperature"].tolist() == [10.0, 11.0]
        # Mean at 10.0 is 100.0 (only one non-NaN value)
        assert result["Space1"].iloc[0] == 100.0
        # Mean at 11.0 is 111.0
        assert result["Space1"].iloc[1] == 111.0

    def test_group_by_temperature_channel_not_found(self):
        """Test error when channel is not in DataFrame."""
        df = pd.DataFrame({
            "Temperature": [10.0, 11.0],
            "Space1": [100.0, 110.0],
        })

        with pytest.raises(ValueError, match="Channel.*not found"):
            group_by_temperature(df, "Space99")

    def test_group_by_temperature_no_temperature_column(self):
        """Test error when Temperature column is missing."""
        df = pd.DataFrame({
            "Temp": [10.0, 11.0],
            "Space1": [100.0, 110.0],
        })

        with pytest.raises(ValueError, match="Temperature"):
            group_by_temperature(df, "Space1")

    def test_group_by_temperature_all_nan_channel(self):
        """Test when all channel values are NaN."""
        df = pd.DataFrame({
            "Temperature": [10.0, 11.0, 12.0],
            "Space1": [np.nan, np.nan, np.nan],
        })

        result = group_by_temperature(df, "Space1")

        # All NaN rows should be dropped
        assert len(result) == 0

    def test_group_by_temperature_single_value_per_temp(self):
        """Test when each temperature has only one value."""
        df = pd.DataFrame({
            "Temperature": [10.0, 11.0, 12.0],
            "Space1": [100.0, 110.0, 120.0],
        })

        result = group_by_temperature(df, "Space1")

        # Should return same values
        assert len(result) == 3
        assert result["Space1"].tolist() == [100.0, 110.0, 120.0]


class TestSmoothData:
    """Tests for smooth_data function."""

    def test_smooth_data_basic(self):
        """Test basic smoothing functionality."""
        temps = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
        values = np.array([100.0, 102.0, 101.0, 103.0, 102.0])

        temps_smooth, values_smooth = smooth_data(temps, values, window_length=3, polyorder=1)

        # Check output shape matches input
        assert len(temps_smooth) == len(temps)
        assert len(values_smooth) == len(values)

        # Check temperatures are unchanged
        np.testing.assert_array_equal(temps_smooth, temps)

        # Smoothed values should be different (smoother) than input
        # For a window of 3, the middle values should be smoothed
        assert not np.array_equal(values_smooth, values)

    def test_smooth_data_even_window_correction(self):
        """Test that even window_length is corrected to odd."""
        temps = np.linspace(0, 10, 50)
        values = np.sin(temps) + np.random.randn(50) * 0.1

        # Use even window_length
        temps_smooth, values_smooth = smooth_data(temps, values, window_length=10, polyorder=2)

        # Should succeed (window corrected to 11)
        assert len(values_smooth) == len(values)

    def test_smooth_data_window_equals_polyorder_raises_error(self):
        """Test that window_length <= polyorder raises ValueError."""
        temps = np.array([10.0, 11.0, 12.0])
        values = np.array([100.0, 110.0, 120.0])

        with pytest.raises(ValueError, match="window_length.*must be greater than polyorder"):
            smooth_data(temps, values, window_length=3, polyorder=3)

    def test_smooth_data_window_larger_than_data_raises_error(self):
        """Test that window_length > data length raises ValueError."""
        temps = np.array([10.0, 11.0, 12.0])
        values = np.array([100.0, 110.0, 120.0])

        with pytest.raises(ValueError, match="window_length.*cannot be larger than data length"):
            smooth_data(temps, values, window_length=10, polyorder=2)

    def test_smooth_data_length_mismatch_raises_error(self):
        """Test that mismatched input lengths raise ValueError."""
        temps = np.array([10.0, 11.0, 12.0])
        values = np.array([100.0, 110.0])  # Different length

        with pytest.raises(ValueError, match="Length mismatch"):
            smooth_data(temps, values)

    def test_smooth_data_empty_arrays(self):
        """Test with empty input arrays."""
        temps = np.array([])
        values = np.array([])

        temps_smooth, values_smooth = smooth_data(temps, values)

        assert len(temps_smooth) == 0
        assert len(values_smooth) == 0

    def test_smooth_data_preserves_peaks(self):
        """Test that Savitzky-Golay preserves peak shapes better than moving average."""
        # Create a signal with a peak
        temps = np.linspace(0, 10, 100)
        values = np.exp(-(temps - 5)**2)  # Gaussian peak

        # Add some noise
        np.random.seed(42)
        values_noisy = values + np.random.randn(100) * 0.01

        # Smooth the noisy data
        temps_smooth, values_smooth = smooth_data(temps, values_noisy, window_length=11, polyorder=2)

        # Smoothed data should be closer to original than noisy data
        error_noisy = np.mean((values_noisy - values)**2)
        error_smooth = np.mean((values_smooth - values)**2)

        assert error_smooth < error_noisy

    def test_smooth_data_large_window(self):
        """Test with larger window size."""
        temps = np.linspace(0, 100, 200)
        values = np.sin(temps / 10) + np.random.randn(200) * 0.1

        temps_smooth, values_smooth = smooth_data(temps, values, window_length=51, polyorder=3)

        assert len(values_smooth) == len(values)
        # Larger window should produce smoother results
        assert np.std(np.diff(values_smooth)) < np.std(np.diff(values))

    def test_smooth_data_single_point(self):
        """Test with single data point."""
        temps = np.array([10.0])
        values = np.array([100.0])

        # With single point, window_length cannot be > data length
        # This should raise an error
        with pytest.raises(ValueError, match="window_length.*cannot be larger"):
            smooth_data(temps, values, window_length=3, polyorder=1)


class TestRemoveOutliers:
    """Tests for remove_outliers function."""

    def test_remove_outliers_normal_data(self):
        """Test that normal data without outliers is not modified."""
        # Create smooth linear data without spikes
        np.random.seed(42)
        temps = np.linspace(0, 30, 100)
        # Linear trend with small noise - no spikes
        values = 100 + 5 * temps + np.random.randn(100) * 0.5

        temps_clean, values_clean, mask = remove_outliers(temps, values, window=5, threshold=5.0)

        # No outliers should be detected (excluding boundary points)
        outlier_count = np.sum(mask)
        assert outlier_count == 0, f"False positives detected: {outlier_count} outliers in smooth data"

    def test_remove_outliers_with_spike(self):
        """Test that clear spikes are detected and removed."""
        # Create data with a clear spike
        temps = np.linspace(0, 30, 100)
        values = 100 + 5 * temps  # Linear trend

        # Add a spike at index 50
        values[50] = 500  # Much higher than surrounding values

        temps_clean, values_clean, mask = remove_outliers(temps, values, window=5, threshold=3.0)

        # Spike should be detected
        assert mask[50] == True
        # Cleaned value should be different (interpolated)
        assert values_clean[50] != 500
        # Interpolated value should be close to expected linear value
        expected_value = 100 + 5 * temps[50]
        assert abs(values_clean[50] - expected_value) < 20

    def test_remove_outliers_multiple_spikes(self):
        """Test detection of multiple spikes."""
        temps = np.linspace(0, 30, 100)
        values = 100 + 5 * temps  # Linear trend

        # Add multiple spikes (away from boundaries)
        values[20] = 400
        values[50] = 500
        values[70] = 600

        temps_clean, values_clean, mask = remove_outliers(temps, values, window=5, threshold=3.0)

        # All spikes should be detected
        assert mask[20] == True
        assert mask[50] == True
        assert mask[70] == True

    def test_remove_outliers_length_mismatch_raises_error(self):
        """Test that mismatched input lengths raise ValueError."""
        temps = np.array([10.0, 11.0, 12.0])
        values = np.array([100.0, 110.0])  # Different length

        with pytest.raises(ValueError, match="Length mismatch"):
            remove_outliers(temps, values)

    def test_remove_outliers_small_data(self):
        """Test with data smaller than window size."""
        temps = np.array([10.0, 11.0])
        values = np.array([100.0, 110.0])

        temps_clean, values_clean, mask = remove_outliers(temps, values, window=5, threshold=5.0)

        # Should return as-is (not enough data for rolling window)
        np.testing.assert_array_equal(temps_clean, temps)
        np.testing.assert_array_equal(values_clean, values)
        assert np.sum(mask) == 0

    def test_remove_outliers_real_data_no_false_positives(self):
        """Test that real smooth data (from AFReport) produces no false positives."""
        # Load real test data
        import json
        from pathlib import Path

        data_path = Path("原始数据/2026.2.26/AFReport_SP_20250507_102452.json")
        if not data_path.exists():
            pytest.skip("Test data file not found")

        with open(data_path) as f:
            data = json.load(f)

        df = pd.DataFrame(data)
        df = df.replace("NaN", np.nan)
        df["Space1"] = pd.to_numeric(df["Space1"], errors="coerce")

        # Group by temperature
        grouped = group_by_temperature(df, "Space1")
        temps = grouped["Temperature"].values
        values = grouped["Space1"].values

        # Remove outliers with default threshold
        temps_clean, values_clean, mask = remove_outliers(temps, values, window=5, threshold=5.0)

        # Should have very few outliers in clean data
        # Allow up to 5% of points as outliers (some edge effects are acceptable)
        outlier_count = np.sum(mask)
        max_allowed = len(values) * 0.05
        assert outlier_count <= max_allowed, f"Too many false positives: {outlier_count} outliers in clean data"

    def test_remove_outliers_real_data_with_spikes(self):
        """Test detection of real sensor spikes from data2.xlsx."""
        from pathlib import Path

        data_path = Path("原始数据/2026.2.28/data2.xlsx")
        if not data_path.exists():
            pytest.skip("Test data file not found")

        df = pd.read_excel(data_path)

        # Group by temperature
        grouped = group_by_temperature(df, "Space1")
        temps = grouped["Temperature"].values
        values = grouped["Space1"].values

        # Remove outliers
        temps_clean, values_clean, mask = remove_outliers(temps, values, window=5, threshold=5.0)

        # Should detect some outliers (the spikes we saw earlier)
        outlier_count = np.sum(mask)
        assert outlier_count > 0, "Failed to detect any outliers in data with known spikes"

        # After cleaning, the data should be smoother (lower variance in differences)
        # Compare the variance of differences before and after cleaning
        original_diff_var = np.var(np.diff(values))
        cleaned_diff_var = np.var(np.diff(values_clean))
        # Cleaned data should have lower or similar variance in differences
        assert cleaned_diff_var <= original_diff_var * 1.1, "Cleaning should not increase variance"

    def test_remove_outliers_consecutive_zeros(self):
        """Test detection of consecutive zero values (sensor dropout)."""
        # Create smooth data with 4 consecutive zeros (sensor dropout scenario)
        temps = np.linspace(0, 30, 100)
        values = 100 + 5 * temps  # Linear trend

        # Simulate sensor dropout: 4 consecutive zeros
        values[48:52] = 0

        temps_clean, values_clean, mask = remove_outliers(
            temps, values, window=11, threshold=5.0
        )

        # All zero points should be detected as outliers
        for i in range(48, 52):
            assert mask[i] == True, f"Zero at index {i} not detected as outlier"

        # Interpolated values should be close to expected linear value
        for i in range(48, 52):
            expected = 100 + 5 * temps[i]
            assert abs(values_clean[i] - expected) < 30, (
                f"Interpolated value at index {i} too far from expected: "
                f"got {values_clean[i]:.1f}, expected ~{expected:.1f}"
            )

    def test_remove_outliers_real_data_six_spikes(self):
        """Test detection of 6 known sensor spikes in data2.xlsx.

        Expected spike temperatures: 9.8°C, 10.0°C, 22.0°C, 22.2°C, 22.3°C, 22.4°C
        """
        from pathlib import Path

        data_path = Path("原始数据/2026.2.28/data2.xlsx")
        if not data_path.exists():
            pytest.skip("Test data file not found")

        df = pd.read_excel(data_path)

        # Group by temperature
        grouped = group_by_temperature(df, "Space1")
        temps = grouped["Temperature"].values
        values = grouped["Space1"].values

        # Remove outliers with improved algorithm
        temps_clean, values_clean, mask = remove_outliers(
            temps, values, window=11, threshold=5.0
        )

        # Expected spike temperatures
        expected_spike_temps = [9.8, 10.0, 22.0, 22.2, 22.3, 22.4]

        # Find indices of expected spike temperatures
        spike_indices = []
        for t in expected_spike_temps:
            idx = np.where(np.abs(temps - t) < 0.05)[0]
            if len(idx) > 0:
                spike_indices.append(idx[0])

        # Verify that most of the expected spikes are detected
        detected_count = 0
        for idx in spike_indices:
            if mask[idx]:
                detected_count += 1

        # At least 5 out of 6 spikes should be detected
        assert detected_count >= 5, (
            f"Only {detected_count}/6 expected spikes detected. "
            f"Spike temps: {expected_spike_temps}"
        )

        # Total outlier count should match expected (allow some tolerance for edge effects)
        total_outliers = np.sum(mask)
        assert 4 <= total_outliers <= 12, (
            f"Unexpected outlier count: {total_outliers} (expected ~6)"
        )

    def test_remove_outliers_no_ringing_after_smoothing(self):
        """Test that cleaned data produces no ringing artifacts after Savitzky-Golay smoothing."""
        from pathlib import Path
        from scipy.signal import savgol_filter

        data_path = Path("原始数据/2026.2.28/data2.xlsx")
        if not data_path.exists():
            pytest.skip("Test data file not found")

        df = pd.read_excel(data_path)

        # Group by temperature
        grouped = group_by_temperature(df, "Space1")
        temps = grouped["Temperature"].values
        values = grouped["Space1"].values

        # Remove outliers first
        temps_clean, values_clean, mask = remove_outliers(
            temps, values, window=11, threshold=5.0
        )

        # Apply Savitzky-Golay smoothing
        smoothed = savgol_filter(values_clean, window_length=51, polyorder=3)

        # Check for upward spikes (ringing artifacts) in the smoothed curve
        # Ringing would appear as sudden upward deviations from the general trend
        # Calculate the rolling median of the smoothed data
        s = pd.Series(smoothed)
        rolling_med = s.rolling(window=15, center=True, min_periods=7).median()

        # Calculate deviation from rolling median
        deviations = np.abs(smoothed - rolling_med.values)

        # Remove NaN values from deviations
        valid_deviations = deviations[~np.isnan(deviations)]

        # Calculate MAD (median absolute deviation) of the smoothed curve
        mad = np.median(valid_deviations)

        # No point should deviate more than 3 * MAD from the rolling median
        # (this would indicate ringing artifacts)
        max_deviation = np.max(valid_deviations)
        threshold = 3 * mad if mad > 0 else 10

        assert max_deviation < threshold, (
            f"Ringing artifacts detected in smoothed curve: "
            f"max deviation {max_deviation:.2f} > threshold {threshold:.2f}"
        )

    def test_remove_outliers_normal_data_zero_false_positives(self):
        """Test that clean real data produces zero or minimal false positives."""
        import json
        from pathlib import Path

        data_path = Path("原始数据/2026.2.26/AFReport_SP_20250507_102452.json")
        if not data_path.exists():
            pytest.skip("Test data file not found")

        with open(data_path) as f:
            data = json.load(f)

        df = pd.DataFrame(data)
        df = df.replace("NaN", np.nan)
        for col in ["Space1", "Space2", "Space3", "Space4", "Space5", "Space6"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Test multiple channels
        for channel in ["Space1", "Space2", "Space3"]:
            grouped = group_by_temperature(df, channel)
            temps = grouped["Temperature"].values
            values = grouped[channel].values

            # Remove outliers with default threshold
            temps_clean, values_clean, mask = remove_outliers(
                temps, values, window=11, threshold=5.0
            )

            # Should have zero or minimal false positives
            outlier_count = np.sum(mask)
            max_allowed = 2  # Allow up to 2 edge-effect false positives

            assert outlier_count <= max_allowed, (
                f"Too many false positives in {channel}: "
                f"{outlier_count} outliers detected (max allowed: {max_allowed})"
            )
