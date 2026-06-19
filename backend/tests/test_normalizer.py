"""Tests for the coordinate normalization module."""

import math

import pytest

from app.services import normalizer as nz


def approx(a, b, tol=1e-4):
    return math.isclose(a, b, abs_tol=tol)


class TestParsing:
    def test_dms_standard(self):
        c = nz.parse_line("41° 7' 54.29\" N 71° 37' 49.17\" E")
        assert c is not None
        assert approx(c.latitude, 41.131747)
        assert approx(c.longitude, 71.630325)
        assert c.valid

    def test_decimal(self):
        c = nz.parse_line("41.131747, 71.630325")
        assert c is not None
        assert approx(c.latitude, 41.131747)
        assert approx(c.longitude, 71.630325)

    def test_russian_symbols(self):
        c = nz.parse_line('40°53\'30.32"С 71°22\'33.80"В')
        assert c is not None
        assert approx(c.latitude, 40.891756, tol=1e-3)
        assert approx(c.longitude, 71.376056, tol=1e-3)

    def test_mixed_formatting(self):
        c = nz.parse_line("41 7 54.29 N, 71 37 49.17 E")
        assert c is not None
        assert approx(c.latitude, 41.131747)
        assert approx(c.longitude, 71.630325)

    def test_decimal_space_separated(self):
        c = nz.parse_line("41.131747 71.630325")
        assert c is not None
        assert approx(c.latitude, 41.131747)
        assert approx(c.longitude, 71.630325)

    def test_dms_comma_decimal_seconds(self):
        # User-reported case: comma used as decimal separator in seconds.
        c = nz.parse_line('41°8\'26,774"N 71°39\'27,257"E')
        assert c is not None
        assert approx(c.latitude, 41 + 8 / 60 + 26.774 / 3600)
        assert approx(c.longitude, 71 + 39 / 60 + 27.257 / 3600)
        assert c.valid

    def test_decimal_comma_with_space(self):
        # European decimal degrees, comma decimal, space separated.
        c = nz.parse_line("41,131747 71,630325")
        assert c is not None
        assert approx(c.latitude, 41.131747)
        assert approx(c.longitude, 71.630325)

    def test_decimal_comma_full_european(self):
        # Comma decimal AND comma pair separator, no spaces.
        c = nz.parse_line("41,131747,71,630325")
        assert c is not None
        assert approx(c.latitude, 41.131747)
        assert approx(c.longitude, 71.630325)

    def test_period_pair_separator_still_works(self):
        # Period decimals with comma separator must NOT be misread.
        c = nz.parse_line("41.131747,71.630325")
        assert c is not None
        assert approx(c.latitude, 41.131747)
        assert approx(c.longitude, 71.630325)

    def test_mixed_comma_decimal_with_hemisphere(self):
        c = nz.parse_line("41 7 54,29 N 71 37 49,17 E")
        assert c is not None
        assert approx(c.latitude, 41.131747)
        assert approx(c.longitude, 71.630325)

    def test_southern_western_hemisphere(self):
        c = nz.parse_line("33.8688 S, 151.2093 W")
        assert c is not None
        assert c.latitude < 0
        assert c.longitude < 0


class TestFormatting:
    def test_standard_output(self):
        s = nz.decimal_to_dms(41.131747, is_lat=True)
        assert s == "41°07'54.29\"N"

    def test_longitude_output(self):
        s = nz.decimal_to_dms(71.630325, is_lat=False)
        assert s == "71°37'49.17\"E"

    def test_negative_lat_is_south(self):
        s = nz.decimal_to_dms(-1.5, is_lat=True)
        assert s.endswith("S")

    def test_minutes_two_digits(self):
        s = nz.decimal_to_dms(41.05, is_lat=True)
        assert s == "41°03'00.00\"N"


class TestValidation:
    def test_invalid_latitude(self):
        c = nz.parse_line("95.0, 50.0")
        assert c is not None
        assert not c.valid

    def test_invalid_longitude(self):
        c = nz.parse_line("45.0, 200.0")
        assert c is not None
        assert not c.valid


class TestNormalizeText:
    def test_multiline(self):
        text = """41.131747, 71.630325
40.891756, 71.376056
41.131747, 71.630325"""  # duplicate of first
        res = nz.normalize_text(text)
        assert len(res.coordinates) == 2
        assert res.duplicates_removed == 1
        assert res.coordinates[0].point_number == 1
        assert res.coordinates[1].point_number == 2

    def test_csv_with_id_column(self):
        text = "1,41.131747,71.630325\n2,40.891756,71.376056"
        res = nz.normalize_text(text)
        assert len(res.coordinates) == 2

    def test_invalid_collected_separately(self):
        text = "95.0, 50.0\n41.13, 71.63"
        res = nz.normalize_text(text)
        assert len(res.coordinates) == 1
        assert len(res.invalid) == 1
