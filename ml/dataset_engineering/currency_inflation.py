"""
CineMetrics — Currency Conversion & CPI Inflation Deflator Module
Normalizes multi-currency movie budgets and revenues to Nominal USD and Real Constant 2024 USD.
"""

import math
import re
from typing import Optional, Union

# Historical Average Annual Exchange Rates: 1 USD to INR (1980 - 2024)
USD_TO_INR_RATES = {
    1980: 7.86, 1981: 8.66, 1982: 9.46, 1983: 10.10, 1984: 11.36,
    1985: 12.38, 1986: 12.61, 1987: 12.96, 1988: 13.92, 1989: 16.23,
    1990: 17.50, 1991: 22.74, 1992: 25.92, 1993: 30.49, 1994: 31.37,
    1995: 32.43, 1996: 35.43, 1997: 36.31, 1998: 41.26, 1999: 43.06,
    2000: 44.94, 2001: 47.19, 2002: 48.61, 2003: 46.58, 2004: 45.32,
    2005: 44.10, 2006: 45.31, 2007: 41.35, 2008: 43.51, 2009: 48.41,
    2010: 45.73, 2011: 46.67, 2012: 53.44, 2013: 58.60, 2014: 61.03,
    2015: 64.15, 2016: 67.20, 2017: 65.12, 2018: 68.39, 2019: 70.42,
    2020: 74.10, 2021: 73.92, 2022: 78.60, 2023: 82.56, 2024: 83.50,
}

# US Consumer Price Index (CPI-U) Annual Averages (1980 - 2024)
# Reference: US Bureau of Labor Statistics (BLS)
US_CPI_SERIES = {
    1980: 82.4, 1981: 90.9, 1982: 96.5, 1983: 99.6, 1984: 103.9,
    1985: 107.6, 1986: 109.6, 1987: 113.6, 1988: 118.3, 1989: 124.0,
    1990: 130.7, 1991: 136.2, 1992: 140.3, 1993: 144.5, 1994: 148.2,
    1995: 152.4, 1996: 156.9, 1997: 160.5, 1998: 163.0, 1999: 166.6,
    2000: 172.2, 2001: 177.1, 2002: 179.9, 2003: 184.0, 2004: 188.9,
    2005: 195.3, 2006: 201.6, 2007: 207.3, 2008: 215.3, 2009: 214.5,
    2010: 218.1, 2011: 224.9, 2012: 229.6, 2013: 233.0, 2014: 236.7,
    2015: 237.0, 2016: 240.0, 2017: 245.1, 2018: 251.1, 2019: 255.7,
    2020: 258.8, 2021: 271.0, 2022: 292.7, 2023: 304.7, 2024: 314.2,
}

CPI_2024_BASELINE = US_CPI_SERIES[2024]


def parse_inr_amount(val: Union[str, float, int]) -> Optional[float]:
    """
    Parses messy Indian currency strings (e.g., '₹ 150.5 Cr', '1000 Crore', '45.2', '₹20,00,000')
    into actual INR value.
    """
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None

    if isinstance(val, (int, float)):
        # If float value is under 5000, assume it was entered as Crores
        if 0 < val < 5000:
            return float(val * 10_000_000)
        return float(val)

    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "-", "n/a", "tbd"):
        return None

    # Check for Crore mentions
    is_crore = bool(re.search(r"(cr|crore)", s, re.IGNORECASE))
    is_lakh = bool(re.search(r"(lakh|lac)", s, re.IGNORECASE))

    # Clean non-numeric characters except dots and digits
    cleaned = re.sub(r"[^\d.]", "", s)
    if not cleaned:
        return None

    try:
        num = float(cleaned)
        if is_crore or (0 < num < 5000 and "." in s):
            return num * 10_000_000  # 1 Crore = 10,000,000 INR
        elif is_lakh:
            return num * 100_000      # 1 Lakh = 100,000 INR
        return num
    except ValueError:
        return None


def convert_inr_to_usd(amount_inr: Optional[float], release_year: Optional[int]) -> Optional[float]:
    """Converts INR amount to USD based on release year's historical FX rate."""
    if amount_inr is None or amount_inr <= 0:
        return None

    year = int(release_year) if release_year and not math.isnan(release_year) else 2020
    year = min(max(year, 1980), 2024)
    fx_rate = USD_TO_INR_RATES.get(year, 83.50)
    return round(amount_inr / fx_rate, 2)


def deflate_to_constant_2024_usd(nominal_usd: Optional[float], release_year: Optional[int]) -> Optional[float]:
    """
    Adjusts nominal USD box-office and budget numbers to Real Constant 2024 USD using CPI.
    Formula: Real_2024 = Nominal * (CPI_2024 / CPI_release_year)
    """
    if nominal_usd is None or nominal_usd <= 0:
        return None

    year = int(release_year) if release_year and not math.isnan(release_year) else 2024
    year = min(max(year, 1980), 2024)
    cpi_year = US_CPI_SERIES.get(year, CPI_2024_BASELINE)

    deflation_factor = CPI_2024_BASELINE / cpi_year
    return round(nominal_usd * deflation_factor, 2)


if __name__ == "__main__":
    # Smoke tests
    test_val = "₹ 150.5 Cr"
    inr = parse_inr_amount(test_val)
    usd = convert_inr_to_usd(inr, 2023)
    real_usd = deflate_to_constant_2024_usd(usd, 2023)
    print(f"Test: '{test_val}' -> INR: {inr:,.0f} -> USD (2023): ${usd:,.2f} -> Real 2024 USD: ${real_usd:,.2f}")

