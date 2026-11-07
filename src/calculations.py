"""
Calculation engine for salary.
All formulas match the school's salary rules.
"""
from src.config import WORKING_DAYS_PER_MONTH
from src import app_settings


# ----------------------------------------
# FIXED RULES (as per school policy)
# ----------------------------------------
SHORT_LEAVE_RATIO = 0.5        # Half day per short leave
LEAVE_RATIO = 1.0              # Full day per leave


def calculate_salary(basic_pay, inputs):
    """
    Given basic_pay and user inputs, compute all derived fields.
    """
    # ---- Load Settings ----
    settings = app_settings.load_settings()
    LATE_ARRIVAL_FINE = settings.get("late_arrival_fine", 100)
    GP_FUND_MONTHLY = settings.get("gp_fund_monthly", 200)
    default_ot_rate = settings.get("overtime_rate_per_hour", 200)
    
    SS_AMT = settings.get("social_security_amount", 1300)
    OAB_AMT = settings.get("oab_amount", 480)
    ABSENTEE_DAYS_MULTIPLIER = 2

    # ---- Earnings ----
    writing = inputs.get('writing', 0) or 0
    speaking = inputs.get('speaking', 0) or 0
    checking = inputs.get('checking', 0) or 0
    class_teacher = inputs.get('class_teacher', 0) or 0
    coordination = inputs.get('coordination', 0) or 0
    increment = inputs.get('increment', 0) or 0
    previous_pay = inputs.get('previous_pay', 0) or 0   # display only
    misc_allowance = inputs.get('misc_allowance', 0) or 0 # NAYA

    # ---- Overtime inputs ----
    ot_hours = inputs.get('ot_hours', 0) or 0
    ot_days = inputs.get('ot_days', 0) or 0
    overtime_rate = inputs.get('overtime_rate', default_ot_rate) or default_ot_rate

    # ---- Leaves (counts) ----
    no_late_arrivals = int(inputs.get('no_late_arrivals', 0) or 0)
    no_short_leaves = int(inputs.get('no_short_leaves', 0) or 0)
    no_leaves = int(inputs.get('no_leaves', 0) or 0)
    no_absentees = int(inputs.get('no_absentees', 0) or 0)

    # ---- Deductions Inputs (Checkboxes) ----
    apply_ss = inputs.get('apply_social_security', 0)
    apply_oab = inputs.get('apply_oab', 0)
    security_deduction = inputs.get('security_deduction', 0) or 0
    misc_deduction = inputs.get('misc_deduction', 0) or 0 # NAYA

    # ---- Gross Pay (WITHOUT overtime, WITHOUT previous pay) ----
    gross_pay = (
        basic_pay + writing + speaking + checking +
        class_teacher + coordination + increment
    )

    # ---- Deduction rate base ----
    if previous_pay > 0:
        deduction_base = previous_pay
    else:
        deduction_base = gross_pay

    daily_rate = deduction_base / WORKING_DAYS_PER_MONTH if deduction_base else 0

    # ---- Overtime calculation (Both Hours & Days) ----
    amount_from_hours = overtime_rate * ot_hours
    daily_overtime_rate = round(gross_pay / WORKING_DAYS_PER_MONTH) if gross_pay else 0
    amount_from_days = daily_overtime_rate * ot_days
    
    final_overtime = amount_from_hours + amount_from_days
    overtime_calculated = final_overtime
    overtime_count = ot_hours + ot_days # Total count for display

    # ---- Auto-calculated deductions ----
    late_arrival_deduction = LATE_ARRIVAL_FINE * no_late_arrivals
    short_leave_deduction = (daily_rate * SHORT_LEAVE_RATIO) * no_short_leaves
    leaves_deduction = (daily_rate * LEAVE_RATIO) * no_leaves
    
    # Absentee Deduction (Fixed Amount x Count)
    absentee_deduction = daily_rate * ABSENTEE_DAYS_MULTIPLIER * no_absentees

    # GP Fund fixed
    gp_fund = GP_FUND_MONTHLY

    # Social Security & OAB (Sirf tab calculate hoga jab checkbox checked ho)
    social_security = SS_AMT if apply_ss else 0
    oab = OAB_AMT if apply_oab else 0

    # ---- Total Deductions ----
    total_deductions = (
        late_arrival_deduction + short_leave_deduction +
        leaves_deduction + absentee_deduction +
        gp_fund + social_security + security_deduction + oab +
        misc_deduction # NAYA
    )

    # ---- Total Earnings (Gross + OT + Misc Allowance) ----
    total_earnings = gross_pay + final_overtime + misc_allowance

    # ---- Net Pay ----
    net_pay = total_earnings - total_deductions

    return {
        # Earnings
        'writing': writing,
        'speaking': speaking,
        'checking': checking,
        'class_teacher': class_teacher,
        'coordination': coordination,
        'increment': increment,
        'misc_allowance': misc_allowance, # NAYA

        # Overtime
        'ot_hours': ot_hours,
        'ot_days': ot_days,
        'overtime_rate': overtime_rate,
        'overtime_calculated': overtime_calculated,
        'overtime_allowance': final_overtime,

        # Other
        'previous_pay': previous_pay,
        'gross_pay': gross_pay,
        'total_earnings': total_earnings,

        # Leaves & auto deductions
        'no_late_arrivals': no_late_arrivals,
        'late_arrival_deduction': late_arrival_deduction,
        'no_short_leaves': no_short_leaves,
        'short_leave_deduction': short_leave_deduction,
        'no_leaves': no_leaves,
        'leaves_deduction': leaves_deduction,

        # Manual + fixed deductions
        'no_absentees': no_absentees,
        'absentee_deduction': absentee_deduction,
        'gp_fund': gp_fund,
        'social_security': social_security,
        'oab': oab,
        'security_deduction': security_deduction,
        'apply_social_security': apply_ss,
        'apply_oab': apply_oab,
        'misc_deduction': misc_deduction, # NAYA
        'total_deductions': total_deductions,

        # Final
        'net_pay': net_pay,
    }