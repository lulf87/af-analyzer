"""
Tests for tangent_analysis module.
"""

import numpy as np
import pytest

from core.tangent_analysis import (
    compute_derivative, find_max_slope_index,
    fit_baseline, compute_tangent_at_point, find_intersection, analyze_channel
)


class TestComputeDerivative:
    """Tests for compute_derivative function."""

    def test_compute_derivative_basic(self):
        """Test basic derivative computation."""
        temps = np.array([10.0, 11.0, 12.0, 13.0])
        values = np.array([100.0, 110.0, 120.0, 130.0])

        deriv = compute_derivative(temps, values)

        # For linear data, derivative should be constant
        assert len(deriv) == len(values)
        np.testing.assert_allclose(deriv, 10.0, rtol=0.1)

    def test_compute_derivative_non_uniform_spacing(self):
        """Test derivative with non-uniform temperature spacing."""
        temps = np.array([10.0, 11.0, 13.0, 16.0])  # Non-uniform spacing
        values = np.array([100.0, 110.0, 120.0, 130.0])

        deriv = compute_derivative(temps, values)

        # np.gradient handles non-uniform spacing
        assert len(deriv) == len(values)
        # Derivatives should be positive and similar magnitude
        assert np.all(deriv > 0)

    def test_compute_derivative_curved_data(self):
        """Test derivative with curved (non-linear) data."""
        temps = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        values = temps ** 2  # Parabola: derivative = 2 * temps

        deriv = compute_derivative(temps, values)

        # Derivative of x^2 is 2x
        # At endpoints, gradient uses one-sided difference
        # Interior points should be close to 2*temps
        assert deriv[2] == pytest.approx(4.0, abs=0.5)  # At temp=2
        assert deriv[3] == pytest.approx(6.0, abs=0.5)  # At temp=3

    def test_compute_derivative_length_mismatch_raises_error(self):
        """Test that mismatched input lengths raise ValueError."""
        temps = np.array([10.0, 11.0, 12.0])
        values = np.array([100.0, 110.0])  # Different length

        with pytest.raises(ValueError, match="Length mismatch"):
            compute_derivative(temps, values)

    def test_compute_derivative_single_point_raises_error(self):
        """Test that single point raises ValueError."""
        temps = np.array([10.0])
        values = np.array([100.0])

        with pytest.raises(ValueError, match="at least 2 points"):
            compute_derivative(temps, values)

    def test_compute_derivative_negative_slope(self):
        """Test derivative with negative slope."""
        temps = np.array([10.0, 11.0, 12.0, 13.0])
        values = np.array([130.0, 120.0, 110.0, 100.0])  # Decreasing

        deriv = compute_derivative(temps, values)

        # Derivatives should be negative
        assert np.all(deriv < 0)
        np.testing.assert_allclose(deriv, -10.0, rtol=0.1)


class TestFindMaxSlopeIndex:
    """Tests for find_max_slope_index function."""

    def test_find_max_slope_index_basic(self):
        """Test finding index of maximum absolute derivative."""
        derivs = np.array([0.1, 0.5, 1.2, 0.8, 0.3])

        idx = find_max_slope_index(derivs)

        # Maximum absolute value is 1.2 at index 2
        assert idx == 2

    def test_find_max_slope_index_negative_values(self):
        """Test with negative derivative values."""
        derivs = np.array([0.1, -0.5, -1.2, 0.8, 0.3])

        idx = find_max_slope_index(derivs)

        # Maximum absolute value is |-1.2| at index 2
        assert idx == 2

    def test_find_max_slope_index_with_positive_offset(self):
        """Test offset adjustment toward higher temperature."""
        derivs = np.array([0.1, 0.5, 1.2, 0.8, 0.3])

        idx = find_max_slope_index(derivs, offset=1)

        # Max is at index 2, offset of 1 gives index 3
        assert idx == 3

    def test_find_max_slope_index_with_negative_offset(self):
        """Test offset adjustment toward lower temperature."""
        derivs = np.array([0.1, 0.5, 1.2, 0.8, 0.3])

        idx = find_max_slope_index(derivs, offset=-1)

        # Max is at index 2, offset of -1 gives index 1
        assert idx == 1

    def test_find_max_slope_index_offset_clips_upper_bound(self):
        """Test that offset is clipped at array upper bound."""
        derivs = np.array([0.1, 0.5, 1.2, 0.8, 0.3])

        # Large offset should be clipped
        idx = find_max_slope_index(derivs, offset=10)

        # Max at index 2, offset would give 12, but clipped to 4 (last index)
        assert idx == 4

    def test_find_max_slope_index_offset_clips_lower_bound(self):
        """Test that offset is clipped at array lower bound."""
        derivs = np.array([0.1, 0.5, 1.2, 0.8, 0.3])

        # Large negative offset should be clipped
        idx = find_max_slope_index(derivs, offset=-10)

        # Max at index 2, offset would give -8, but clipped to 0
        assert idx == 0

    def test_find_max_slope_index_empty_raises_error(self):
        """Test that empty array raises ValueError."""
        derivs = np.array([])

        with pytest.raises(ValueError, match="cannot be empty"):
            find_max_slope_index(derivs)

    def test_find_max_slope_index_single_element(self):
        """Test with single element array."""
        derivs = np.array([1.5])

        idx = find_max_slope_index(derivs)

        # Should return 0 (only valid index)
        assert idx == 0

    def test_find_max_slope_index_offset_with_single_element(self):
        """Test offset clipping with single element."""
        derivs = np.array([1.5])

        idx_pos = find_max_slope_index(derivs, offset=5)
        idx_neg = find_max_slope_index(derivs, offset=-5)

        # Both should be clipped to 0
        assert idx_pos == 0
        assert idx_neg == 0

    def test_find_max_slope_index_equal_values(self):
        """Test with equal derivative values."""
        derivs = np.array([1.0, 1.0, 1.0, 1.0])

        idx = find_max_slope_index(derivs)

        # argmax returns first occurrence when values are equal
        assert idx == 0

    def test_find_max_slope_index_all_zeros(self):
        """Test with all zero derivatives."""
        derivs = np.array([0.0, 0.0, 0.0])

        idx = find_max_slope_index(derivs)

        # Should return first index
        assert idx == 0


class TestFitBaseline:
    """Tests for fit_baseline function."""

    def test_fit_baseline_basic(self):
        """Test basic baseline fitting."""
        temps = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
        values = np.array([100.0, 101.0, 102.0, 103.0, 104.0])

        slope, intercept = fit_baseline(temps, values, 10.0, 12.0)

        # Should fit a line with slope ~1
        assert abs(slope - 1.0) < 0.1
        # intercept should be around 90 (y = x + 90)
        assert abs(intercept - 90.0) < 1.0

    def test_fit_baseline_no_data_in_range(self):
        """Test error when no data points in range."""
        temps = np.array([10.0, 11.0, 12.0])
        values = np.array([100.0, 110.0, 120.0])

        with pytest.raises(ValueError, match="No data points"):
            fit_baseline(temps, values, 20.0, 25.0)

    def test_fit_baseline_single_point_raises_error(self):
        """Test error when only one point in range."""
        temps = np.array([10.0, 11.0, 12.0])
        values = np.array([100.0, 110.0, 120.0])

        with pytest.raises(ValueError, match="at least 2 points"):
            fit_baseline(temps, values, 11.0, 11.0)


class TestComputeTangentAtPoint:
    """Tests for compute_tangent_at_point function."""

    def test_compute_tangent_at_point_basic(self):
        """Test basic tangent computation."""
        temps = np.array([10.0, 11.0, 12.0])
        values = np.array([100.0, 110.0, 125.0])
        derivatives = np.array([10.0, 15.0, 20.0])

        slope, intercept = compute_tangent_at_point(temps, values, derivatives, 1)

        # Slope should be the derivative at index 1
        assert slope == 15.0
        # Line passes through (11.0, 110.0): intercept = 110 - 15*11 = -55
        assert abs(intercept - (-55.0)) < 0.01

    def test_compute_tangent_at_point_index_out_of_bounds(self):
        """Test error when index is out of bounds."""
        temps = np.array([10.0, 11.0, 12.0])
        values = np.array([100.0, 110.0, 125.0])
        derivatives = np.array([10.0, 15.0, 20.0])

        with pytest.raises(ValueError, match="out of bounds"):
            compute_tangent_at_point(temps, values, derivatives, 5)

    def test_compute_tangent_at_point_length_mismatch(self):
        """Test error when arrays have different lengths."""
        temps = np.array([10.0, 11.0, 12.0])
        values = np.array([100.0, 110.0])
        derivatives = np.array([10.0, 15.0, 20.0])

        with pytest.raises(ValueError, match="same length"):
            compute_tangent_at_point(temps, values, derivatives, 1)


class TestFindIntersection:
    """Tests for find_intersection function."""

    def test_find_intersection_basic(self):
        """Test basic intersection calculation."""
        # Line 1: y = 2x + 10
        # Line 2: y = -x + 25
        # Intersection at x = 5, y = 20
        x = find_intersection(2, 10, -1, 25)

        assert abs(x - 5.0) < 0.01

    def test_find_intersection_parallel_lines(self):
        """Test that parallel lines return np.nan."""
        # Two parallel lines with different intercepts
        x = find_intersection(2, 10, 2, 20)

        assert np.isnan(x)

    def test_find_intersection_identical_lines(self):
        """Test that identical lines (parallel) return np.nan."""
        x = find_intersection(2, 10, 2, 10)

        assert np.isnan(x)

    def test_find_intersection_vertical_shift(self):
        """Test intersection with vertical shift."""
        # Line 1: y = x
        # Line 2: y = x + 10 (parallel, no intersection)
        x = find_intersection(1, 0, 1, 10)

        assert np.isnan(x)

    def test_find_intersection_negative_slopes(self):
        """Test intersection with negative slopes."""
        # Line 1: y = -2x + 20
        # Line 2: y = -x + 15
        # Intersection: -2x + 20 = -x + 15 => x = 5
        x = find_intersection(-2, 20, -1, 15)

        assert abs(x - 5.0) < 0.01


class TestAnalyzeChannel:
    """Tests for analyze_channel high-level interface."""

    def test_analyze_channel_basic(self):
        """Test basic channel analysis."""
        # Create sigmoid-like curve (simulating phase transformation)
        temps = np.linspace(0, 30, 100)
        # Sigmoid transition from ~50 to ~150, centered at 15
        values = 50 + 100 / (1 + np.exp(-(temps - 15) / 2))

        result = analyze_channel(
            temps, values,
            low_range=(0, 5),
            high_range=(25, 30),
            smooth_params=(11, 2)
        )

        # Check result structure
        assert "As" in result
        assert "Af_tan" in result
        assert "max_slope_temp" in result
        assert "low_baseline" in result
        assert "high_baseline" in result
        assert "tangent" in result

        # As should be in reasonable range
        assert not np.isnan(result["As"])
        # Af_tan should be greater than As
        assert result["Af_tan"] > result["As"]

    def test_analyze_channel_length_mismatch_raises_error(self):
        """Test error when temps and values have different lengths."""
        temps = np.array([10.0, 11.0, 12.0])
        values = np.array([100.0, 110.0])

        with pytest.raises(ValueError, match="same length"):
            analyze_channel(temps, values, (0, 1), (2, 3))

    def test_analyze_channel_too_few_points_raises_error(self):
        """Test error with too few data points."""
        temps = np.array([10.0, 11.0])
        values = np.array([100.0, 110.0])

        with pytest.raises(ValueError, match="at least 10 points"):
            analyze_channel(temps, values, (0, 1), (2, 3))

    def test_analyze_channel_returns_line_parameters(self):
        """Test that line parameters are returned correctly."""
        temps = np.linspace(0, 30, 100)
        values = 50 + 100 / (1 + np.exp(-(temps - 15) / 2))

        result = analyze_channel(
            temps, values,
            low_range=(0, 5),
            high_range=(25, 30),
            smooth_params=(11, 2)
        )

        # Check that baselines and tangent are tuples of (slope, intercept)
        assert len(result["low_baseline"]) == 2
        assert len(result["high_baseline"]) == 2
        assert len(result["tangent"]) == 2

        # All should be numeric
        for param in [result["low_baseline"], result["high_baseline"], result["tangent"]]:
            assert isinstance(param[0], (int, float))
            assert isinstance(param[1], (int, float))
