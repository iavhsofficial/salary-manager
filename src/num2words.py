"""
Convert numbers to English words (Indian numbering system).
Example: 245600 -> "Two Lakh Forty Five Thousand Six Hundred"
"""

ONES = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
    "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
    "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"
]

TENS = [
    "", "", "Twenty", "Thirty", "Forty", "Fifty",
    "Sixty", "Seventy", "Eighty", "Ninety"
]


def _two_digits(n):
    """Convert 0-99 to words."""
    if n < 20:
        return ONES[n]
    return TENS[n // 10] + (" " + ONES[n % 10] if n % 10 else "")


def _three_digits(n):
    """Convert 0-999 to words."""
    if n < 100:
        return _two_digits(n)
    return ONES[n // 100] + " Hundred" + (
        " " + _two_digits(n % 100) if n % 100 else ""
    )


def number_to_words(n):
    """
    Convert integer to English words (Indian system).
    Example: 245600 -> "Two Lakh Forty Five Thousand Six Hundred"
    """
    if n == 0:
        return "Zero"

    n = int(n)

    # Handle crores (10 million+)
    if n >= 10000000:
        crores = n // 10000000
        remainder = n % 10000000
        result = number_to_words(crores) + " Crore"
        if remainder:
            result += " " + number_to_words(remainder)
        return result

    # Handle lakhs
    if n >= 100000:
        lakhs = n // 100000
        remainder = n % 100000
        result = _two_digits(lakhs) + " Lakh"
        if remainder:
            result += " " + number_to_words(remainder)
        return result

    # Handle thousands
    if n >= 1000:
        thousands = n // 1000
        remainder = n % 1000
        result = _two_digits(thousands) + " Thousand"
        if remainder:
            result += " " + _three_digits(remainder)
        return result

    # 0-999
    return _three_digits(n)


def amount_in_words(amount):
    """
    Convert amount to 'Rupees X Only' format.
    Handles paisa (decimals) if needed.
    """
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return "Rupees Zero Only"

    rupees = int(amount)
    paisa = int(round((amount - rupees) * 100))

    if rupees == 0 and paisa == 0:
        return "Rupees Zero Only"

    words = "Rupees " + number_to_words(rupees)

    if paisa > 0:
        words += " and " + number_to_words(paisa) + " Paisa"

    return words + " Only"