"""Tests for notanumber."""

import struct

import pytest

import notanumber as nn


class TestHighLevelAPI:
    """Test high-level encode/decode functions."""

    @pytest.mark.parametrize("method", ["zero", "inf", "nan", "subnormal"])
    def test_round_trip_basic(self, method):
        """Test basic round trip for all methods."""
        data = b"Hello, world!"
        encoded = nn.encode(data, method)
        decoded = nn.decode(encoded, method)
        assert decoded == data

    @pytest.mark.parametrize("method", ["zero", "inf", "nan", "subnormal"])
    def test_round_trip_empty(self, method):
        """Test empty data."""
        data = b""
        encoded = nn.encode(data, method)
        decoded = nn.decode(encoded, method)
        assert decoded == data

    def test_invalid_method_encode(self):
        """Test invalid encoding method."""
        with pytest.raises(ValueError, match="There is no invalid room"):
            nn.encode(b"test", "invalid")

    def test_invalid_method_decode(self):
        """Test invalid decoding method."""
        encoded = nn.encode(b"test", "nan")
        with pytest.raises(ValueError, match="There is no invalid room"):
            nn.decode(encoded, "invalid")

    def test_large_data_rejection(self):
        """Test that overly large data is rejected."""
        # Try to encode 101MB (over the 100MB limit)
        large_data = b"X" * (101 * 1024 * 1024)
        with pytest.raises(ValueError, match="Data too large"):
            nn.encode(large_data, "nan")


class TestLowLevelAPI:
    """Test low-level to_*/from_* functions."""

    def test_zero_methods(self):
        """Test to_zero and from_zero."""
        data = b"Test zero"
        encoded = nn.to_zero(data)
        decoded = nn.from_zero(encoded)
        assert decoded == data

    def test_inf_methods(self):
        """Test to_inf and from_inf."""
        data = b"Test infinity"
        encoded = nn.to_inf(data)
        decoded = nn.from_inf(encoded)
        assert decoded == data

    def test_nan_methods(self):
        """Test to_nan and from_nan."""
        data = b"Test NaN"
        encoded = nn.to_nan(data)
        decoded = nn.from_nan(encoded)
        assert decoded == data

    def test_subnormal_methods(self):
        """Test to_subnormal and from_subnormal."""
        data = b"Test subnormal"
        encoded = nn.to_subnormal(data)
        decoded = nn.from_subnormal(encoded)
        assert decoded == data

    def test_all_bytes_low_level(self):
        """Test all byte values with low-level functions."""
        data = bytes(range(256))

        # Test each method pair
        for to_func, from_func in [
            (nn.to_zero, nn.from_zero),
            (nn.to_inf, nn.from_inf),
            (nn.to_nan, nn.from_nan),
            (nn.to_subnormal, nn.from_subnormal),
        ]:
            encoded = to_func(data)
            decoded = from_func(encoded)
            assert decoded == data


class TestNullByteHandling:
    """Test that null bytes are preserved correctly."""

    @pytest.mark.parametrize("method", ["nan", "subnormal"])
    def test_trailing_null_bytes(self, method):
        """Test data ending with null bytes."""
        data = b"Hello\x00\x00\x00"
        encoded = nn.encode(data, method)
        decoded = nn.decode(encoded, method)
        assert decoded == data
        assert len(decoded) == len(data)

    @pytest.mark.parametrize("method", ["nan", "subnormal"])
    def test_all_null_bytes(self, method):
        """Test data that is all null bytes."""
        data = b"\x00" * 10
        encoded = nn.encode(data, method)
        decoded = nn.decode(encoded, method)
        assert decoded == data
        assert len(decoded) == 10

    @pytest.mark.parametrize("method", ["zero", "inf", "nan", "subnormal"])
    def test_mixed_null_bytes(self, method):
        """Test data with null bytes throughout."""
        data = b"\x00Hello\x00World\x00\x00"
        encoded = nn.encode(data, method)
        decoded = nn.decode(encoded, method)
        assert decoded == data


class TestAutoDetection:
    """Test automatic method detection."""

    @pytest.mark.parametrize("method", ["zero", "inf", "nan", "subnormal"])
    def test_auto_detect(self, method):
        """Test auto-detection for each method."""
        data = b"Auto-detect this!"
        encoded = nn.encode(data, method)
        decoded = nn.decode(encoded, "auto")
        assert decoded == data

    def test_auto_detect_insufficient_data(self):
        """Test auto-detection with insufficient data."""
        with pytest.raises(ValueError, match="more than crumbs"):
            nn.decode(b"X", "auto")

    def test_auto_detect_invalid_data(self):
        """Test auto-detection with invalid data."""
        # Create invalid fp16 pattern
        invalid = struct.pack("<H", 0x1234)
        with pytest.raises(ValueError, match="doesn't look like anything"):
            nn.decode(invalid, "auto")


class TestEfficiency:
    """Test encoding efficiency."""

    def test_zero_efficiency(self):
        """Test zero encoding uses 16x space."""
        data = b"X"
        encoded = nn.encode(data, "zero")
        assert len(encoded) == len(data) * 16

    def test_inf_efficiency(self):
        """Test infinity encoding uses 16x space."""
        data = b"X"
        encoded = nn.encode(data, "inf")
        assert len(encoded) == len(data) * 16

    def test_nan_efficiency(self):
        """Test NaN encoding efficiency."""
        # Account for 4-byte length header
        data = b"X" * 100
        encoded = nn.encode(data, "nan")
        # (100 + 4) bytes * 8 bits / 9 bits per NaN * 2 bytes per NaN
        expected_size = ((100 + 4) * 8 + 8) // 9 * 2
        assert len(encoded) == expected_size

    def test_subnormal_efficiency(self):
        """Test subnormal encoding efficiency."""
        # Account for 4-byte length header
        data = b"X" * 100
        encoded = nn.encode(data, "subnormal")
        # (100 + 4) bytes * 8 bits / 10 bits per subnormal * 2 bytes per subnormal
        expected_size = ((100 + 4) * 8 + 9) // 10 * 2
        assert len(encoded) == expected_size


class TestDataIntegrity:
    """Test data integrity checks."""

    def test_zero_corrupted(self):
        """Test detection of corrupted zero encoding."""
        # Create a non-zero value in what should be zeros
        corrupted = struct.pack("<8H", 0x0001, 0, 0, 0, 0, 0, 0, 0)
        with pytest.raises(ValueError, match="Impure zeros"):
            nn.decode(corrupted, "zero")

    def test_inf_corrupted_not_inf(self):
        """Test detection of non-infinity in infinity encoding."""
        # Create a finite value (1.0 in fp16)
        corrupted = struct.pack("<8H", *[0x3C00] * 8)
        with pytest.raises(ValueError, match="Non-infinity"):
            nn.decode(corrupted, "inf")

    def test_inf_corrupted_nan(self):
        """Test detection of NaN in infinity encoding."""
        # Create NaN instead of infinity
        corrupted = struct.pack("<8H", *[0x7E00] * 8)
        with pytest.raises(ValueError, match="NaN snuck"):
            nn.decode(corrupted, "inf")

    def test_nan_corrupted(self):
        """Test detection of non-NaN in NaN encoding."""
        # Create a regular number
        corrupted = struct.pack("<H", 0x3C00)
        with pytest.raises(ValueError, match="pretending to be NaN"):
            nn.decode(corrupted, "nan")

    def test_subnormal_corrupted_normal(self):
        """Test detection of normal value in subnormal encoding."""
        # Create a normalized value
        corrupted = struct.pack("<H", 0x3C00)
        with pytest.raises(ValueError, match="aren't subnormal"):
            nn.decode(corrupted, "subnormal")

    def test_subnormal_corrupted_negative(self):
        """Test detection of negative subnormal."""
        # Create negative subnormal
        corrupted = struct.pack("<H", 0x8001)
        with pytest.raises(ValueError, match="Wrong kind of small"):
            nn.decode(corrupted, "subnormal")


class TestEdgeCases:
    """Test edge cases and special values."""

    def test_various_sizes(self):
        """Test various data sizes."""
        # Test sizes that will have different padding
        for size in [1, 7, 8, 9, 10, 11, 63, 64, 65, 127, 128, 129]:
            data = b"X" * size
            for method in ["zero", "inf", "nan", "subnormal"]:
                encoded = nn.encode(data, method)
                decoded = nn.decode(encoded, method)
                assert decoded == data

    def test_zero_length_arrays(self):
        """Test handling of zero-length arrays."""
        for method in ["zero", "inf", "nan", "subnormal"]:
            empty = b""
            encoded = nn.encode(empty, method)
            decoded = nn.decode(encoded, method)
            assert decoded == empty

    def test_subnormal_zero_mantissa(self):
        """Test that subnormal encoding handles zero mantissa correctly."""
        # Create data that includes bytes that would map to zero mantissa
        data = b"\x00\x00"
        encoded = nn.encode(data, "subnormal")
        decoded = nn.decode(encoded, "subnormal")
        assert decoded == data

    @pytest.mark.parametrize("method", ["zero", "inf", "nan", "subnormal"])
    def test_large_safe_data(self, method):
        """Test with larger but safe data."""
        # 1MB should be fine
        data = b"Pure imagination! " * (1024 * 1024 // 18)
        encoded = nn.encode(data, method)
        decoded = nn.decode(encoded, method)
        assert decoded == data


class TestCorruptedHeaders:
    """Test handling of corrupted length headers."""

    def test_nan_corrupted_header(self):
        """Test corrupted length header in NaN encoding."""
        # Create a NaN array with invalid length
        corrupted = struct.pack("<10H", *[0x7E00 | 0xFF] * 10)
        with pytest.raises(ValueError, match="Corrupted length header"):
            nn.from_nan(corrupted)

    def test_subnormal_corrupted_header(self):
        """Test corrupted length header in subnormal encoding."""
        # Create a subnormal array with invalid length
        corrupted = struct.pack("<10H", *[0x01FF] * 10)
        with pytest.raises(ValueError, match="Corrupted length header"):
            nn.from_subnormal(corrupted)


class TestSubnormalEdgeCases:
    """Test subnormal-specific edge cases."""

    def test_subnormal_uses_zero(self):
        """Test that subnormal method correctly uses zero mantissa."""
        # Encode data that should produce zero mantissa
        data = b"\x00"  # First 10 bits will be 0
        encoded = nn.to_subnormal(data)

        # Check first value is zero
        first_val = struct.unpack("<H", encoded[4:6])[0]  # Skip length header
        assert first_val == 0  # Should be zero, not subnormal

    def test_subnormal_max_mantissa(self):
        """Test subnormal with maximum mantissa value."""
        # Create data that will produce mantissa 1023 (0x3FF)
        encoded = nn.to_subnormal(b"\xff\x03")

        # Verify it encodes without overflow
        decoded = nn.from_subnormal(encoded)
        assert decoded == b"\xff\x03"


if __name__ == "__main__":
    pytest.main([__file__])
