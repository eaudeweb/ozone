import enum
import decimal


# Default values for decimal
DECIMAL_FIELD_DIGITS = 25
DECIMAL_FIELD_DECIMALS = 15


@enum.unique
class RatificationTypes(enum.Enum):
    """
    General enum of ratification types; should be useful in other models too
    """

    ACCESSION = 'Accession'
    APPROVAL = 'Approval'
    ACCEPTANCE = 'Acceptance'
    RATIFICATION = 'Ratification'
    SUCCESSION = 'Succession'
    SIGNING = 'Signing'


def model_to_dict(instance, fields=None, exclude=None):
    data = instance.__dict__
    attributes = {}
    for key, value in data.items():
        if fields and key not in fields:
            continue
        if exclude and key in exclude:
            continue
        attributes[key] = data[key]
    return attributes


def round_float_half_up(x, decimals=0):
    # Be aware that some floats are represented with extra decimals, e.g.
    # 9.075 => Decimal('9.074999999999999289457264239899814128875732421875')
    # 1171.545 => Decimal('1171.545000000000072759576141834259033203125')
    # 49.95 => Decimal('49.9500000000000028421709430404007434844970703125')

    decimal.getcontext().rounding = decimal.ROUND_HALF_UP
    return float(round(decimal.Decimal(str(x)), decimals))


def round_decimal_half_up(x, decimals=0):
    decimal.getcontext().rounding = decimal.ROUND_HALF_UP
    return round(x, decimals)


def decimal_zero_if_none(value):
    return value if value is not None else decimal.Decimal(0.0)


def float_to_decimal_zero_if_none(value):
    """Converts float to decimal, avoiding exception if value is None"""
    return decimal.Decimal(str(value)) if value else decimal.Decimal(0.0)


def float_to_decimal(value):
    """Converts null-able float to decimal, returns None if value is None"""
    return decimal.Decimal(str(value)) if value else None


def quantize(value):
    """Quantize to DECIMAL_FIELD_DECIMALS decimal places"""
    quant = decimal.Decimal(10) ** -DECIMAL_FIELD_DECIMALS
    return value.quantize(quant)
