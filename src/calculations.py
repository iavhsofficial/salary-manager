"""
Calculation engine for salary.
All formulas match the original Excel sheet exactly.
"""
from src.config import WORKING_DAYS_PER_MONTH


def calculate_salary(basic_pay, inputs):
    """
    Given basic_pay and user inputs, compute all derived fields.

    inputs dict keys:
        writing, speaking, checking, dis, ct, od,
        ot_extra, e_day, la_adv, gp_fund, sec, s_sec,
        oab, sl, cl_day, ann_l, ab_fine
    """
    # ---- Earnings ----
    writing = inputs.get('writing', 0) or 0
    speaking = inputs.get('speaking', 0) or 0
    checking = inputs.get('checking', 0) or 0
    dis = inputs.get('dis', 0) or 0
    ct = inputs.get('ct', 0) or 0
    od = inputs.get('od', 0) or 0
    ot_extra = inputs.get('ot_extra', 0) or 0
    e_day = inputs.get('e_day', 0) or 0

    # ---- Deductions input ----
    la_adv = inputs.get('la_adv', 0) or 0
    gp_fund = inputs.get('gp_fund', 0) or 0
    sec = inputs.get('sec', 0) or 0
    s_sec = inputs.get('s_sec', 0) or 0
    oab = inputs.get('oab', 0) or 0
    sl = inputs.get('sl', 0) or 0
    cl_day = inputs.get('cl_day', 0) or 0
    ann_l = inputs.get('ann_l', 0) or 0
    ab_fine = inputs.get('ab_fine', 0) or 0

    # ---- Auto-calculated ----
    total_1 = basic_pay + writing + speaking
    total_2 = checking + dis + ct + od

    eda = (ot_extra / WORKING_DAYS_PER_MONTH) * e_day if ot_extra else 0

    gross_pay = total_1 + total_2 + ot_extra + e_day + eda

    # Fines based on OT rate (as in your Excel)
    if ot_extra:
        daily_rate = ot_extra / WORKING_DAYS_PER_MONTH
    else:
        daily_rate = basic_pay / WORKING_DAYS_PER_MONTH if basic_pay else 0

    fine = (daily_rate / 2) * cl_day
    cl_fine = daily_rate * cl_day

    total_ded = (
        la_adv + gp_fund + sec + s_sec + oab + sl +
        fine + cl_fine + ann_l + ab_fine
    )

    net_pay = gross_pay - total_ded

    return {
        # Input fields (returned for storage)
        'writing': writing,
        'speaking': speaking,
        'checking': checking,
        'dis': dis,
        'ct': ct,
        'od': od,
        'ot_extra': ot_extra,
        'e_day': e_day,
        'la_adv': la_adv,
        'gp_fund': gp_fund,
        'sec': sec,
        's_sec': s_sec,
        'oab': oab,
        'sl': sl,
        'cl_day': cl_day,
        'ann_l': ann_l,
        'ab_fine': ab_fine,
        # Derived fields
        'total_1': total_1,
        'total_2': total_2,
        'eda': eda,
        'fine': fine,
        'cl_fine': cl_fine,
        'gross_pay': gross_pay,
        'total_ded': total_ded,
        'net_pay': net_pay,
    }