cat > /home/erp/frappe-bench/apps/controlz_customizations/controlz_customizations/controlz_customizations/report/internal_mis_report/internal_mis_report.py << 'EOF'
import frappe
from frappe.utils import nowdate, get_first_day, get_last_day

def execute(filters=None):
    if not filters:
        filters = {}

    def R(v):
        return round(v, 2) if v else 0.0

    from_date = filters.get("from_date") or get_first_day(nowdate())
    to_date   = filters.get("to_date")   or get_last_day(nowdate())

    si_rows = frappe.db.sql("""
        SELECT sii.item_group, si.custom_sales_order_type AS channel,
               SUM(sii.net_amount) AS amount,
               SUM(sii.qty * sii.incoming_rate) AS cogs,
               SUM(sii.qty) AS qty
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE si.docstatus = 1
        AND si.posting_date BETWEEN %s AND %s
        GROUP BY sii.item_group, si.custom_sales_order_type
    """, (from_date, to_date), as_dict=True)

    pi_rows = frappe.db.sql("""
        SELECT pii.expense_account AS account, SUM(pii.net_amount) AS amount
        FROM `tabPurchase Invoice` pi
        JOIN `tabPurchase Invoice Item` pii ON pii.parent = pi.name
        WHERE pi.docstatus = 1
        AND pi.posting_date BETWEEN %s AND %s
        GROUP BY pii.expense_account
    """, (from_date, to_date), as_dict=True)

    je_rows = frappe.db.sql("""
        SELECT jea.account, SUM(jea.debit - jea.credit) AS amount
        FROM `tabJournal Entry` je
        JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
        WHERE je.docstatus = 1
        AND je.posting_date BETWEEN %s AND %s
        GROUP BY jea.account
    """, (from_date, to_date), as_dict=True)

    SVC_LIST = ["Services","Spare Part","Protection Services","Other Services","Tempered Glass","Expenses","Other"]
    ACC_LIST = ["Accessories"]

    rev_dev_on=0.0; rev_dev_off=0.0; rev_dev_b2b=0.0; rev_dev_oth=0.0
    rev_acc_on=0.0; rev_acc_off=0.0; rev_acc_b2b=0.0; rev_acc_oth=0.0
    rev_svc_on=0.0; rev_svc_off=0.0; rev_svc_b2b=0.0; rev_svc_oth=0.0
    cog_dev_on=0.0; cog_dev_off=0.0; cog_dev_b2b=0.0; cog_dev_oth=0.0
    cog_acc_on=0.0; cog_acc_off=0.0; cog_acc_b2b=0.0; cog_acc_oth=0.0
    cog_svc_on=0.0; cog_svc_off=0.0; cog_svc_b2b=0.0; cog_svc_oth=0.0
    qty_dev_on=0.0; qty_dev_off=0.0; qty_dev_b2b=0.0

    for r in si_rows:
        ig  = (r.item_group or "").strip()
        ch  = (r.channel    or "").strip().upper()
        amt = r.amount or 0.0
        cst = r.cogs   or 0.0
        q   = r.qty    or 0.0
        grp = "svc" if ig in SVC_LIST else ("acc" if ig in ACC_LIST else "dev")
        col = "on" if ch == "D2C" else ("off" if ch in ("STORE","OFFLINE SALE") else ("b2b" if ch == "B2B" else "oth"))

        if grp == "dev":
            if col == "on":    rev_dev_on  += amt; cog_dev_on  += cst; qty_dev_on  += q
            elif col == "off": rev_dev_off += amt; cog_dev_off += cst; qty_dev_off += q
            elif col == "b2b": rev_dev_b2b += amt; cog_dev_b2b += cst; qty_dev_b2b += q
            else:              rev_dev_oth += amt; cog_dev_oth += cst
        elif grp == "acc":
            if col == "on":    rev_acc_on  += amt; cog_acc_on  += cst
            elif col == "off": rev_acc_off += amt; cog_acc_off += cst
            elif col == "b2b": rev_acc_b2b += amt; cog_acc_b2b += cst
            else:              rev_acc_oth += amt; cog_acc_oth += cst
        else:
            if col == "on":    rev_svc_on  += amt; cog_svc_on  += cst
            elif col == "off": rev_svc_off += amt; cog_svc_off += cst
            elif col == "b2b": rev_svc_b2b += amt; cog_svc_b2b += cst
            else:              rev_svc_oth += amt; cog_svc_oth += cst

    rd2c=rev_dev_on+rev_dev_off; rd_t=rd2c+rev_dev_b2b+rev_dev_oth
    ra2c=rev_acc_on+rev_acc_off; ra_t=ra2c+rev_acc_b2b+rev_acc_oth
    rs2c=rev_svc_on+rev_svc_off; rs_t=rs2c+rev_svc_b2b+rev_svc_oth
    cd2c=cog_dev_on+cog_dev_off; cd_t=cd2c+cog_dev_b2b+cog_dev_oth
    ca2c=cog_acc_on+cog_acc_off; ca_t=ca2c+cog_acc_b2b+cog_acc_oth
    cs2c=cog_svc_on+cog_svc_off; cs_t=cs2c+cog_svc_b2b+cog_svc_oth
    tr_on=rev_dev_on+rev_acc_on+rev_svc_on
    tr_off=rev_dev_off+rev_acc_off+rev_svc_off
    tr_b2b=rev_dev_b2b+rev_acc_b2b+rev_svc_b2b
    tr_oth=rev_dev_oth+rev_acc_oth+rev_svc_oth
    tr_d2c=tr_on+tr_off; tr_gt=tr_d2c+tr_b2b+tr_oth
    tc_on=cog_dev_on+cog_acc_on+cog_svc_on
    tc_off=cog_dev_off+cog_acc_off+cog_svc_off
    tc_b2b=cog_dev_b2b+cog_acc_b2b+cog_svc_b2b
    tc_oth=cog_dev_oth+cog_acc_oth+cog_svc_oth
    tc_d2c=tc_on+tc_off; tc_gt=tc_d2c+tc_b2b+tc_oth
    gt = tr_gt or 1

    asp_on  = R(rev_dev_on  / qty_dev_on)  if qty_dev_on  else 0.0
    asp_off = R(rev_dev_off / qty_dev_off) if qty_dev_off else 0.0
    asp_b2b = R(rev_dev_b2b / qty_dev_b2b) if qty_dev_b2b else 0.0
    acp_on  = R(cog_dev_on  / qty_dev_on)  if qty_dev_on  else 0.0
    acp_off = R(cog_dev_off / qty_dev_off) if qty_dev_off else 0.0
    acp_b2b = R(cog_dev_b2b / qty_dev_b2b) if qty_dev_b2b else 0.0

    marketing=0.0; branding=0.0; logistics=0.0; store_rent=0.0
    payroll=0.0; interest=0.0; pg=0.0

    for r in pi_rows:
        acct = r.account or ""
        amt  = r.amount or 0.0
        if acct == "Performance - UW":                         marketing  += amt
        elif acct == "Branding - UW":                          branding   += amt
        elif acct == "Logistics & Shipping Expenses - UW":     logistics  += amt
        elif acct == "Rent Expense - UW":                      store_rent += amt

    for r in je_rows:
        acct = r.account or ""
        amt  = r.amount or 0.0
        if acct == "Director Remuneration - UW":                       payroll  += amt
        elif acct == "Interest on term loan - UW":                     interest += amt
        elif acct == "Interest Payable on Ghalla Bhanshali loan - UW": interest += amt
        elif acct == "Razorpay Pvt Ltd A/c - UW":                      pg       += amt

    warranty   = tr_gt * 0.005
    pg_log     = pg + logistics
    mktg_total = marketing + branding + store_rent
    corp_total = payroll

    cm1_on=tr_on-tc_on; cm1_off=tr_off-tc_off; cm1_b2b=tr_b2b-tc_b2b; cm1_oth=tr_oth-tc_oth
    cm1_d2c=cm1_on+cm1_off; cm1_gt=cm1_d2c+cm1_b2b+cm1_oth-warranty
    cm2_on=cm1_on-pg_log; cm2_off=cm1_off; cm2_b2b=cm1_b2b; cm2_oth=cm1_oth
    cm2_d2c=cm2_on+cm2_off; cm2_gt=cm1_gt-pg_log
    cm3_on=cm2_on-(marketing+branding); cm3_off=cm2_off-store_rent
    cm3_b2b=cm2_b2b; cm3_oth=cm2_oth
    cm3_d2c=cm3_on+cm3_off; cm3_gt=cm2_gt-mktg_total
    ebitda_val=cm3_gt-corp_total
    net_profit=ebitda_val-interest

    def P(v):
        return round(v / gt * 100, 2)

    N = None

    columns = [
        {"label": "Particulars",        "fieldname": "particulars",  "fieldtype": "Data",     "width": 300},
        {"label": "D2C Online",          "fieldname": "d2c_online",   "fieldtype": "Currency", "width": 140},
        {"label": "D2C Offline (Store)", "fieldname": "d2c_offline",  "fieldtype": "Currency", "width": 150},
        {"label": "D2C Total",           "fieldname": "d2c_total",    "fieldtype": "Currency", "width": 130},
        {"label": "Distribution (B2B)",  "fieldname": "distribution", "fieldtype": "Currency", "width": 150},
        {"label": "Others / Repair",     "fieldname": "others",       "fieldtype": "Currency", "width": 130},
        {"label": "% of Rev",            "fieldname": "pct_rev",      "fieldtype": "Percent",  "width": 90},
        {"label": "Grand Total",         "fieldname": "grand_total",  "fieldtype": "Currency", "width": 150},
    ]

    data = [
        {"particulars": "MONTHLY MIS — {} to {}".format(from_date, to_date), "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "No. of Devices Sold", "d2c_online": qty_dev_on, "d2c_offline": qty_dev_off, "d2c_total": qty_dev_on+qty_dev_off, "distribution": qty_dev_b2b, "others": N, "pct_rev": N, "grand_total": qty_dev_on+qty_dev_off+qty_dev_b2b},
        {"particulars": "Avg Selling Price (Device)", "d2c_online": asp_on, "d2c_offline": asp_off, "d2c_total": N, "distribution": asp_b2b, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "Avg Device Cost",            "d2c_online": acp_on, "d2c_offline": acp_off, "d2c_total": N, "distribution": acp_b2b, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "REVENUE FROM OPERATIONS", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "  Devices",     "d2c_online": R(rev_dev_on), "d2c_offline": R(rev_dev_off), "d2c_total": R(rd2c), "distribution": R(rev_dev_b2b), "others": R(rev_dev_oth), "pct_rev": P(rd_t),  "grand_total": R(rd_t)},
        {"particulars": "  Accessories", "d2c_online": R(rev_acc_on), "d2c_offline": R(rev_acc_off), "d2c_total": R(ra2c), "distribution": R(rev_acc_b2b), "others": R(rev_acc_oth), "pct_rev": P(ra_t),  "grand_total": R(ra_t)},
        {"particulars": "  Services",    "d2c_online": R(rev_svc_on), "d2c_offline": R(rev_svc_off), "d2c_total": R(rs2c), "distribution": R(rev_svc_b2b), "others": R(rev_svc_oth), "pct_rev": P(rs_t),  "grand_total": R(rs_t)},
        {"particulars": "Total Revenue", "d2c_online": R(tr_on),      "d2c_offline": R(tr_off),      "d2c_total": R(tr_d2c), "distribution": R(tr_b2b),    "others": R(tr_oth),       "pct_rev": 100.0,    "grand_total": R(tr_gt)},
        {"particulars": "", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "DIRECT COSTS", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "  Device Cost",             "d2c_online": R(cog_dev_on), "d2c_offline": R(cog_dev_off), "d2c_total": R(cd2c), "distribution": R(cog_dev_b2b), "others": R(cog_dev_oth), "pct_rev": P(cd_t), "grand_total": R(cd_t)},
        {"particulars": "  Spare Parts Cost",        "d2c_online": R(cog_svc_on), "d2c_offline": R(cog_svc_off), "d2c_total": R(cs2c), "distribution": R(cog_svc_b2b), "others": R(cog_svc_oth), "pct_rev": P(cs_t), "grand_total": R(cs_t)},
        {"particulars": "  Cost of Add-ons",         "d2c_online": R(cog_acc_on), "d2c_offline": R(cog_acc_off), "d2c_total": R(ca2c), "distribution": R(cog_acc_b2b), "others": R(cog_acc_oth), "pct_rev": P(ca_t), "grand_total": R(ca_t)},
        {"particulars": "  Warranty Provision @0.5%","d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": P(warranty), "grand_total": R(warranty)},
        {"particulars": "Total Direct Costs",        "d2c_online": R(tc_on), "d2c_offline": R(tc_off), "d2c_total": R(tc_d2c), "distribution": R(tc_b2b), "others": R(tc_oth), "pct_rev": P(tc_gt), "grand_total": R(tc_gt)},
        {"particulars": "", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "CONTRIBUTION MARGIN 1", "d2c_online": R(cm1_on), "d2c_offline": R(cm1_off), "d2c_total": R(cm1_d2c), "distribution": R(cm1_b2b), "others": R(cm1_oth), "pct_rev": P(cm1_gt), "grand_total": R(cm1_gt)},
        {"particulars": "  CM1 %", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": P(cm1_gt), "grand_total": N},
        {"particulars": "", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "PAYMENT GATEWAY & LOGISTICS", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "  Payment Gateway (Razorpay)", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": P(pg),       "grand_total": R(pg)},
        {"particulars": "  Outward Logistics",          "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": P(logistics), "grand_total": R(logistics)},
        {"particulars": "", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "CONTRIBUTION MARGIN 2", "d2c_online": R(cm2_on), "d2c_offline": R(cm2_off), "d2c_total": R(cm2_d2c), "distribution": R(cm2_b2b), "others": R(cm2_oth), "pct_rev": P(cm2_gt), "grand_total": R(cm2_gt)},
        {"particulars": "  CM2 %", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": P(cm2_gt), "grand_total": N},
        {"particulars": "", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "MARKETING & STORE", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "  Marketing / Performance", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": P(marketing),  "grand_total": R(marketing)},
        {"particulars": "  Branding",                "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": P(branding),   "grand_total": R(branding)},
        {"particulars": "  Store Rent",              "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": P(store_rent), "grand_total": R(store_rent)},
        {"particulars": "  Total Mktg & Store",      "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": P(mktg_total), "grand_total": R(mktg_total)},
        {"particulars": "", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "CONTRIBUTION MARGIN 3", "d2c_online": R(cm3_on), "d2c_offline": R(cm3_off), "d2c_total": R(cm3_d2c), "distribution": R(cm3_b2b), "others": R(cm3_oth), "pct_rev": P(cm3_gt), "grand_total": R(cm3_gt)},
        {"particulars": "  CM3 %", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": P(cm3_gt), "grand_total": N},
        {"particulars": "", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "CORPORATE OVERHEADS", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "  Director Remuneration",   "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": P(payroll),    "grand_total": R(payroll)},
        {"particulars": "Total Corporate Overheads", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": P(corp_total), "grand_total": R(corp_total)},
        {"particulars": "", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "EBITDA",    "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": P(ebitda_val), "grand_total": R(ebitda_val)},
        {"particulars": "  EBITDA %","d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": P(ebitda_val), "grand_total": N},
        {"particulars": "", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "BELOW THE LINE", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "  Interest on Loans", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": P(interest), "grand_total": R(interest)},
        {"particulars": "", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": N, "grand_total": N},
        {"particulars": "NET PROFIT / (LOSS)", "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": P(net_profit), "grand_total": R(net_profit)},
        {"particulars": "  Net Margin %",      "d2c_online": N, "d2c_offline": N, "d2c_total": N, "distribution": N, "others": N, "pct_rev": P(net_profit), "grand_total": N},
    ]

    return columns, data
EOF
