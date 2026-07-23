"""
Ekam: One Customer Graph
A live demo accompanying the Axis Bank 2035 transformation pitch.

Tab 1, Steward Dashboard: the banker admin view of a single household, with
clickable product tiles that open full underlying detail.

Tab 2, Operating Model and P&L Engine: how the household P&L, transfer
pricing, and enterprise impact case actually work underneath the dashboard.

Run with:
    pip install streamlit pandas
    streamlit run app.py
"""

import copy
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Ekam: One Customer Graph", layout="wide")

USD_INR = 83.0


def inr_l(amount):
    """Format a rupee amount as lakhs, Indian convention, e.g. 588200 -> 'Rs 5.88 L'."""
    sign = "-" if amount < 0 else ""
    return f"{sign}Rs {abs(amount) / 100000:,.2f} L"


def inr_plain(amount):
    """Format a rupee amount plainly with comma separators."""
    sign = "-" if amount < 0 else ""
    return f"{sign}Rs {abs(amount):,.0f}"


def calc_emi(principal, annual_rate, years):
    r = annual_rate / 12
    n = years * 12
    if r == 0:
        return principal / n
    return principal * r * (1 + r) ** n / ((1 + r) ** n - 1)


# ---------------------------------------------------------------------------
# HOUSEHOLD DATA
# Each product carries a "financials" dict (the numbers a real system would
# hold) and a "meta" dict (static descriptive fields). Display details and
# P&L breakdowns are both derived from these, so the two tabs stay consistent
# with each other.
# ---------------------------------------------------------------------------

HOUSEHOLDS_SEED = {
    "Rohan Mehta, Salaried, Mumbai": {
        "tier": "Mass",
        "ratio": "1 steward per 3,000 to 5,000 households",
        "health_score": 78,
        "primacy": "CASA share 62 percent",
        "cross_sell_depth": 2.2,
        "products": {
            "Deposits": {
                "status": "Active", "flag": None,
                "financials": {"balance": 420000, "deposit_rate": 0.035, "asset_yield": 0.070},
            },
            "Loans": {
                "status": "In underwriting", "flag": "New application",
                "financials": {
                    "principal": 6800000, "rate": 0.0865, "cost_of_funds": 0.065,
                    "provisioning": 0.004, "opex": 0.003, "tenure_years": 20,
                },
                "meta": {"purpose": "Home purchase", "collateral": "Property under registration"},
            },
            "Cards": {
                "status": "Active", "flag": None,
                "financials": {
                    "limit": 300000, "utilization": 0.22, "annual_spend": 180000,
                    "interchange_rate": 0.015, "annual_fee": 1000, "acquisition_cost": 450,
                    "loss_rate": 0.006, "credit_score": 762,
                },
            },
            "Insurance": {
                "status": "Not enrolled", "flag": "Cross-sell opportunity",
                "financials": {"premium": 0},
                "meta": {"nominee_on_file": "Priya Mehta, spouse, from KYC",
                         "signal": "Home loan in underwriting: insurance is typically bundled at disbursement"},
                "cross_sell_fields": [
                    {"label": "Policy type", "type": "select",
                     "options": ["Term life", "Health", "Term and health bundle", "Home loan protection"]},
                    {"label": "Sum assured (Rs)", "type": "number", "default": 5000000},
                    {"label": "Annual premium (Rs)", "type": "number", "default": 18000},
                    {"label": "Payment frequency", "type": "select", "options": ["Monthly", "Quarterly", "Annual"]},
                ],
            },
            "Wealth": {
                "status": "Active", "flag": None,
                "financials": {"aum": 310000, "fee_rate": 0.010, "advisory_cost_rate": 0.003,
                               "returns_ytd": 0.112, "monthly_sip": 15000},
                "meta": {"risk_profile": "Moderate", "funds_held": "3 mutual funds"},
            },
            "Forex": {
                "status": "Queued", "flag": "Pricing decision needed",
                "financials": {"annual_usd": 5000, "markup_today": 0.030, "netting_cost_rate": 0.002},
                "meta": {"purpose": "Education, dependent's tuition"},
                "cross_sell_fields": [
                    {"label": "Approve household pricing tier", "type": "select",
                     "options": ["Zero-margin, Ekam household rate", "Standard desk rate, override"]},
                    {"label": "Approved by, steward name", "type": "text", "default": ""},
                ],
            },
        },
    },
    "Priya Nair, MSME Owner": {
        "tier": "Complex",
        "ratio": "1 squad and bench per 250 to 400 households",
        "health_score": 85,
        "primacy": "CASA share 71 percent",
        "cross_sell_depth": 3.1,
        "products": {
            "Deposits": {
                "status": "Active", "flag": None,
                "financials": {"balance": 2200000, "deposit_rate": 0.032, "asset_yield": 0.070},
            },
            "Loans": {
                "status": "Active", "flag": None,
                "financials": {
                    "principal": 12000000, "rate": 0.1025, "cost_of_funds": 0.075,
                    "provisioning": 0.008, "opex": 0.004, "tenure_years": None,
                    "revolving": True, "utilization": 0.68,
                },
                "meta": {"purpose": "Inventory financing", "type": "Revolving working capital"},
            },
            "Cards": {
                "status": "Active", "flag": None,
                "financials": {
                    "limit": 1000000, "utilization": 0.35, "annual_spend": 1200000,
                    "interchange_rate": 0.015, "annual_fee": 2500, "acquisition_cost": 600,
                    "loss_rate": 0.007, "credit_score": 781,
                },
            },
            "Insurance": {
                "status": "Active", "flag": None,
                "financials": {"premium": 42000, "commission_rate": 0.15},
                "meta": {"policy": "Key-person cover", "sum_assured": "Rs 50,00,000", "renewal": "March 2027"},
            },
            "Wealth": {
                "status": "Active", "flag": None,
                "financials": {"aum": 4000000, "fee_rate": 0.010, "advisory_cost_rate": 0.003, "returns_ytd": 0.098},
                "meta": {"risk_profile": "Growth", "mandate": "Balanced"},
            },
            "Forex": {
                "status": "Active", "flag": "Recurring volume, review pricing tier",
                "financials": {"annual_usd": 96000, "markup_today": 0.018, "netting_cost_rate": 0.003},
                "meta": {"pattern": "Recurring monthly import remittance, average $8,000 per month"},
                "cross_sell_fields": [
                    {"label": "Recommended pricing tier", "type": "select",
                     "options": ["Household-preferred, 0.5 percent", "Zero-margin, Ekam", "Keep standard desk rate"]},
                    {"label": "Steward sign-off", "type": "text", "default": ""},
                ],
            },
        },
    },
    "The Kapoor Family, NRI-Linked": {
        "tier": "Private",
        "ratio": "1 dedicated squad per 30 to 60 households",
        "health_score": 91,
        "primacy": "CASA share 80 percent",
        "cross_sell_depth": 4.2,
        "products": {
            "Deposits": {
                "status": "Active", "flag": None,
                "financials": {"balance": 11100000, "deposit_rate": 0.041, "asset_yield": 0.070},
            },
            "Loans": {
                "status": "No active exposure", "flag": None,
                "financials": {"principal": 0, "rate": 0, "cost_of_funds": 0, "provisioning": 0, "opex": 0},
            },
            "Cards": {
                "status": "Active", "flag": None,
                "financials": {
                    "limit": 800000, "utilization": 0.14, "annual_spend": 900000,
                    "interchange_rate": 0.015, "annual_fee": 5000, "acquisition_cost": 900,
                    "loss_rate": 0.003, "credit_score": 812,
                },
            },
            "Insurance": {
                "status": "Active", "flag": None,
                "financials": {"premium": 110000, "commission_rate": 0.15},
                "meta": {"policy": "Family floater and term life", "sum_assured": "Rs 1,00,00,000", "renewal": "January 2027"},
            },
            "Wealth": {
                "status": "Active", "flag": None,
                "financials": {"aum": 24000000, "fee_rate": 0.012, "advisory_cost_rate": 0.003, "returns_ytd": 0.134},
                "meta": {"tier": "Burgundy", "mandate": "Diversified, equity, debt and alternates"},
            },
            "Forex": {
                "status": "Active", "flag": None,
                "financials": {"annual_usd": 12000, "markup_today": 0.002, "netting_cost_rate": 0.002},
                "meta": {"pattern": "Annual education remittance, already on household pricing"},
            },
        },
    },
}

FEED_SEED = {
    "Rohan Mehta, Salaried, Mumbai": [
        {"id": 1, "text": "CKYC 2.0 auto-verified identity for the loan and forex request. No re-documentation needed.",
         "auto": True, "escalate": False},
        {"id": 2, "text": "Household holds 4 of 6 products and shows an education remittance pattern. Flagging a wealth planning conversation.",
         "auto": True, "escalate": True,
         "why": "This is a judgment call about the relationship, not a system parameter. Routed to the human steward."},
        {"id": 3, "text": "Forex priced at netting cost instead of desk rate. Applied automatically under the household pricing rule.",
         "auto": True, "escalate": False},
        {"id": 4, "text": "Income category changed on the latest salary credit. Recommend reviewing loan eligibility and life stage needs together.",
         "auto": True, "escalate": True,
         "why": "A change in life or income circumstances should be a human conversation, not an automated update."},
    ],
    "Priya Nair, MSME Owner": [
        {"id": 1, "text": "Recurring import remittance volume detected. Household is eligible for a forex pricing tier upgrade.",
         "auto": True, "escalate": True,
         "why": "A pricing tier change affects relationship economics and requires steward sign-off."},
        {"id": 2, "text": "Working capital utilization pattern is stable. No action needed.",
         "auto": True, "escalate": False},
    ],
    "The Kapoor Family, NRI-Linked": [
        {"id": 1, "text": "Annual education remittance cycle is starting. Pre-cleared at the household rate, no desk involvement required.",
         "auto": True, "escalate": False},
    ],
}

PNL_OWNER = {
    "Deposits": ("Deposits P&L head", "Deposit growth"),
    "Loans": ("Loans P&L head", "Disbursement volume"),
    "Cards": ("Cards P&L head", "Cards issued and spend"),
    "Insurance": ("Insurance JV partner", "Policies sold"),
    "Wealth": ("Wealth P&L head", "AUM growth"),
    "Forex": ("Forex desk", "Margin captured per transaction"),
}


def build_details(product, fin, meta):
    """Read-only display details, derived from the underlying financials."""
    meta = meta or {}
    if product == "Deposits":
        return {
            "Balance": inr_plain(fin["balance"]),
            "Deposit rate paid to customer": f"{fin['deposit_rate'] * 100:.1f} percent per annum",
            "Bank asset yield on these funds": f"{fin['asset_yield'] * 100:.1f} percent per annum",
        }
    if product == "Loans":
        if fin.get("principal", 0) == 0:
            return {"Exposure": "None on record"}
        d = {"Principal amount": inr_plain(fin["principal"]), "Interest rate": f"{fin['rate'] * 100:.2f} percent"}
        if fin.get("revolving"):
            d["Type"] = meta.get("type", "Revolving working capital")
            d["Current utilization"] = f"{fin['utilization'] * 100:.0f} percent"
        else:
            d["Tenure"] = f"{fin['tenure_years']} years"
            d["EMI"] = inr_plain(calc_emi(fin["principal"], fin["rate"], fin["tenure_years"]))
        if meta.get("purpose"):
            d["Purpose"] = meta["purpose"]
        if meta.get("collateral"):
            d["Collateral"] = meta["collateral"]
        return d
    if product == "Cards":
        return {
            "Credit limit": inr_plain(fin["limit"]),
            "Utilization": f"{fin['utilization'] * 100:.0f} percent",
            "Credit score": str(fin["credit_score"]),
            "Annual spend": inr_plain(fin["annual_spend"]),
            "Transaction fee and interchange revenue, annual": inr_plain(fin["annual_spend"] * fin["interchange_rate"] + fin["annual_fee"]),
            "Customer acquisition cost": inr_plain(fin["acquisition_cost"]),
        }
    if product == "Insurance":
        if fin.get("premium", 0) == 0:
            d = {"Current cover": "None"}
            if meta.get("nominee_on_file"):
                d["Nominee on file"] = meta["nominee_on_file"]
            if meta.get("signal"):
                d["Related signal"] = meta["signal"]
            return d
        d = {"Policy": meta.get("policy", "Active policy"), "Annual premium": inr_plain(fin["premium"])}
        if meta.get("sum_assured"):
            d["Sum assured"] = meta["sum_assured"]
        if meta.get("renewal"):
            d["Renewal date"] = meta["renewal"]
        return d
    if product == "Wealth":
        d = {
            "Portfolio value": inr_plain(fin["aum"]),
            "Returns, year to date": f"{fin['returns_ytd'] * 100:.1f} percent",
            "Advisory fee": f"{fin['fee_rate'] * 100:.2f} percent of AUM annually",
        }
        if meta.get("risk_profile"):
            d["Risk profile"] = meta["risk_profile"]
        if meta.get("mandate"):
            d["Mandate"] = meta["mandate"]
        if fin.get("monthly_sip"):
            d["Monthly SIP"] = inr_plain(fin["monthly_sip"])
        return d
    if product == "Forex":
        inr_value = fin["annual_usd"] * USD_INR
        d = {
            "Annual remittance value": f"${fin['annual_usd']:,.0f} ({inr_plain(inr_value)})",
            "Current markup": f"{fin['markup_today'] * 100:.1f} percent",
            "Ekam household rate": f"{fin['netting_cost_rate'] * 100:.1f} percent, at processing cost",
        }
        if meta.get("purpose"):
            d["Purpose"] = meta["purpose"]
        if meta.get("pattern"):
            d["Pattern"] = meta["pattern"]
        return d
    return {}


def build_pnl(product, fin):
    """Returns (line_items, revenue, net_margin) in rupees, derived from financials."""
    if product == "Deposits":
        balance = fin["balance"]
        interest_expense = -balance * fin["deposit_rate"]
        float_income = balance * fin["asset_yield"]
        net = float_income + interest_expense
        return [("Float income earned on balance", float_income),
                ("Interest paid to customer", interest_expense),
                ("Net contribution", net)], float_income, net
    if product == "Loans":
        principal = fin.get("principal", 0)
        if principal == 0:
            return [("No active exposure", 0)], 0, 0
        base = principal * fin["utilization"] if fin.get("revolving") else principal
        interest_income = base * fin["rate"]
        cost_of_funds = -base * fin["cost_of_funds"]
        provisioning = -base * fin["provisioning"]
        opex = -base * fin["opex"]
        net = interest_income + cost_of_funds + provisioning + opex
        return [("Interest income", interest_income),
                ("Cost of funds", cost_of_funds),
                ("Credit provisioning", provisioning),
                ("Operating cost", opex),
                ("Net margin", net)], interest_income, net
    if product == "Cards":
        revenue = fin["annual_spend"] * fin["interchange_rate"] + fin["annual_fee"]
        acquisition = -fin["acquisition_cost"]
        loss = -fin["annual_spend"] * fin["loss_rate"]
        net = revenue + acquisition + loss
        return [("Interchange and fee revenue", revenue),
                ("Customer acquisition cost", acquisition),
                ("Credit and fraud losses", loss),
                ("Net margin", net)], revenue, net
    if product == "Insurance":
        premium = fin.get("premium", 0)
        if premium == 0:
            return [("No active policy, untapped opportunity", 0)], 0, 0
        commission = premium * fin.get("commission_rate", 0.15)
        servicing = -premium * 0.05
        net = commission + servicing
        return [("Commission revenue", commission),
                ("Servicing cost", servicing),
                ("Net margin", net)], commission, net
    if product == "Wealth":
        aum = fin["aum"]
        fee_revenue = aum * fin["fee_rate"]
        advisory_cost = -aum * fin["advisory_cost_rate"]
        net = fee_revenue + advisory_cost
        return [("AUM-based fee revenue", fee_revenue),
                ("Advisory and operations cost", advisory_cost),
                ("Net margin", net)], fee_revenue, net
    if product == "Forex":
        inr_value = fin["annual_usd"] * USD_INR
        markup_revenue = inr_value * fin["markup_today"]
        processing_cost = -inr_value * fin["netting_cost_rate"]
        net_today = markup_revenue + processing_cost
        net_ekam = processing_cost
        return [("Annual remittance value processed", inr_value),
                ("Revenue at current desk markup", markup_revenue),
                ("Processing cost", processing_cost),
                ("Net margin at current pricing", net_today),
                ("Net margin under Ekam zero-margin pricing", net_ekam)], markup_revenue, net_today
    return [], 0, 0


# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------
if "escalated" not in st.session_state:
    st.session_state.escalated = set()
if "hh_state" not in st.session_state:
    st.session_state.hh_state = copy.deepcopy(HOUSEHOLDS_SEED)
if "selected_product" not in st.session_state:
    st.session_state.selected_product = {}
if "selected_silo" not in st.session_state:
    st.session_state.selected_silo = {}

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.title("Ekam: One Customer Graph")
st.caption("Live demo accompanying the One Axis 2035 transformation pitch: the steward dashboard bankers "
           "would use, and the P&L mechanics running underneath it.")

tab1, tab2 = st.tabs(["Steward Dashboard", "Operating Model and P&L Engine"])

# ===========================================================================
# TAB 1: STEWARD DASHBOARD
# ===========================================================================
with tab1:
    household_name = st.selectbox("Select household", list(st.session_state.hh_state.keys()), key="hh_select_tab1")
    hh = st.session_state.hh_state[household_name]

    st.divider()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Household health score", f"{hh['health_score']} of 100")
    c2.metric("Primacy", hh["primacy"])
    c3.metric("Cross-sell depth", f"{hh['cross_sell_depth']}x")
    c4.metric("Coverage tier", hh["tier"], help=hh["ratio"])

    st.info(f"One steward. One graph. Coverage model: {hh['ratio']}")

    st.divider()

    st.subheader("Household: one view, all products")
    st.caption("Click a tile to see full detail. Tiles flagged with an opportunity also let you add new information as the bank admin.")

    cols = st.columns(6)
    for col, (product, info) in zip(cols, hh["products"].items()):
        with col:
            is_selected = st.session_state.selected_product.get(household_name) == product
            if st.button(product, key=f"tile-{household_name}-{product}",
                         use_container_width=True, type="primary" if is_selected else "secondary"):
                st.session_state.selected_product[household_name] = product
                st.rerun()
            st.caption(info["status"])
            if info["flag"]:
                st.warning(info["flag"])

    st.markdown("")

    selected = st.session_state.selected_product.get(household_name)
    if selected:
        info = hh["products"][selected]
        fin = info["financials"]
        meta = info.get("meta", {})
        details = build_details(selected, fin, meta)

        with st.container(border=True):
            st.markdown(f"### {selected}: full detail")
            st.caption(f"Status: {info['status']}")

            detail_cols = st.columns(2)
            items = list(details.items())
            half = (len(items) + 1) // 2
            for label, value in items[:half]:
                detail_cols[0].markdown(f"**{label}:** {value}")
            for label, value in items[half:]:
                detail_cols[1].markdown(f"**{label}:** {value}")

            if "cross_sell_fields" in info:
                st.divider()
                st.markdown("**Add new details, bank admin action**")
                already_added = info.get("added")
                if already_added:
                    st.success("Submitted. This household's record now reflects the update below.")
                    for label, value in already_added.items():
                        st.write(f"**{label}:** {value}")
                else:
                    with st.form(key=f"form-{household_name}-{selected}"):
                        entered = {}
                        for field in info["cross_sell_fields"]:
                            fkey = f"f-{household_name}-{selected}-{field['label']}"
                            if field["type"] == "select":
                                entered[field["label"]] = st.selectbox(field["label"], field["options"], key=fkey)
                            elif field["type"] == "number":
                                entered[field["label"]] = st.number_input(field["label"], value=field["default"], key=fkey)
                            else:
                                entered[field["label"]] = st.text_input(field["label"], value=field["default"], key=fkey)
                        submitted = st.form_submit_button("Save to household record")
                        if submitted:
                            info["added"] = entered
                            info["flag"] = None
                            info["status"] = "Active, pending activation"
                            st.rerun()
    else:
        st.caption("Click any product tile above to view its full details.")

    st.divider()

    st.subheader("AI steward feed")
    st.caption("AI-first, human at trust moments. Everything below resolves automatically unless it is escalated.")

    for item in FEED_SEED[household_name]:
        key = f"{household_name}-{item['id']}"
        with st.container(border=True):
            st.write(item["text"])
            if item["escalate"]:
                if key in st.session_state.escalated:
                    st.error(f"Escalated to human steward. {item['why']}")
                else:
                    if st.button("Escalate to human steward", key=f"btn-{key}"):
                        st.session_state.escalated.add(key)
                        st.rerun()
            else:
                st.success("Resolved automatically. No human action needed.")

    st.divider()

    st.subheader("Governance")
    g1, g2, g3 = st.columns(3)
    g1.success("Credit sanction: independent")
    g2.success("Risk: independent")
    g3.success("Compliance: independent")
    st.caption("The three lines of defence never sit inside relationship squads. They read one graph instead of five.")

# ===========================================================================
# TAB 2: OPERATING MODEL AND P&L ENGINE
# ===========================================================================
with tab2:
    st.subheader("Product P&L today versus household P&L under Ekam")
    st.caption("Same underlying revenue and cost, a different unit of account, ownership, and incentive. "
               "Click a silo below to see its revenue and cost breakdown for the selected household.")

    household_name_2 = st.selectbox("Household in view", list(st.session_state.hh_state.keys()), key="hh_select_tab2")
    hh2 = st.session_state.hh_state[household_name_2]

    st.markdown("**Today: six silo P&Ls, nobody owns the household**")

    silo_results = {}
    for product, info in hh2["products"].items():
        line_items, revenue, net = build_pnl(product, info["financials"])
        silo_results[product] = {"line_items": line_items, "revenue": revenue, "net": net}

    scols = st.columns(6)
    for col, silo in zip(scols, hh2["products"].keys()):
        with col:
            is_sel = st.session_state.selected_silo.get(household_name_2) == silo
            if st.button(silo, key=f"silo-{household_name_2}-{silo}",
                         use_container_width=True, type="primary" if is_sel else "secondary"):
                st.session_state.selected_silo[household_name_2] = silo
                st.rerun()
            col.caption(f"Net: {inr_l(silo_results[silo]['net'])}")

    sel_silo = st.session_state.selected_silo.get(household_name_2)
    if sel_silo:
        owner, incentive = PNL_OWNER[sel_silo]
        with st.container(border=True):
            st.markdown(f"### {sel_silo}: P&L breakdown")
            c1, c2 = st.columns(2)
            c1.markdown(f"**Owner today:** {owner}")
            c2.markdown(f"**Incentive tied to:** {incentive}")

            breakdown_df = pd.DataFrame(
                [(label, inr_l(value)) for label, value in silo_results[sel_silo]["line_items"]],
                columns=["Line item", "Amount"],
            )
            st.dataframe(breakdown_df, hide_index=True, use_container_width=True)

            product_info = hh2["products"].get(sel_silo, {})
            if "cross_sell_fields" in product_info and "added" not in product_info:
                st.warning("This silo currently shows an untapped opportunity for this household. "
                           "See the matching flag on the Steward Dashboard tab.")
                fin = product_info["financials"]
                meta = product_info.get("meta", {})
                st.markdown("**What we already know, read-only:**")
                for label, value in build_details(sel_silo, fin, meta).items():
                    st.write(f"- **{label}:** {value}")
                st.caption("Add this household's new details from the Steward Dashboard tab. Once saved there, "
                           "it will show as resolved here too, since both tabs read the same household record.")
            elif "added" in product_info:
                st.success("Opportunity resolved. Admin-entered details now feed into this household's P&L.")
                for label, value in product_info["added"].items():
                    st.write(f"- **{label}:** {value}")
    else:
        st.caption("Click a silo above to see its revenue and cost breakdown and current internal ownership.")

    total_revenue = sum(r["revenue"] for r in silo_results.values())
    total_net = sum(r["net"] for r in silo_results.values())
    st.caption(
        f"Six-silo total for this household: {inr_l(total_revenue)} revenue, {inr_l(total_net)} net contribution. "
        "This sum exists in the general ledger, but no single number represents this household's total "
        "relationship value, and no single owner is accountable for it."
    )

    st.divider()

    st.markdown("**Ekam: one household P&L, one steward accountable**")
    colA, colB, colC = st.columns(3)
    colA.metric("Household revenue", inr_l(total_revenue),
                help="Same underlying revenue, now attributed to one household instead of six silos.")
    forex_fin = hh2["products"]["Forex"]["financials"]
    forex_today = forex_fin["annual_usd"] * USD_INR * forex_fin["markup_today"]
    forex_ekam = forex_fin["annual_usd"] * USD_INR * forex_fin["netting_cost_rate"]
    colB.metric("Forex margin given up", f"{inr_l(forex_today)} to {inr_l(forex_ekam)}",
                help="Zero-margin forex is the falsifiable proof that the model actually changed.")
    colC.metric("Net household contribution", inr_l(total_net),
                help="What the steward is now accountable for, in place of six separate product targets.")

    st.divider()

    st.subheader("Transfer pricing: how factories charge squads")
    st.caption("Product teams do not disappear. They become internal factories, selling capacity to relationship "
               "squads at a published internal rate.")

    transfer_pricing = pd.DataFrame([
        {"Factory": "Loans operations", "Internal rate charged to squad": "Cost-plus service level rate",
         "Volume for this household": hh2["products"]["Loans"]["financials"].get("principal", 0) and inr_l(hh2["products"]["Loans"]["financials"]["principal"]) or "No active file"},
        {"Factory": "Insurance operations", "Internal rate charged to squad": "Per-policy service fee",
         "Volume for this household": inr_l(hh2["products"]["Insurance"]["financials"].get("premium", 0)) if hh2["products"]["Insurance"]["financials"].get("premium", 0) else "No active policy"},
        {"Factory": "Forex operations", "Internal rate charged to squad": "Netting cost, near-zero markup",
         "Volume for this household": f"${hh2['products']['Forex']['financials']['annual_usd']:,.0f} per year"},
        {"Factory": "Wealth operations", "Internal rate charged to squad": "Basis points on AUM serviced",
         "Volume for this household": inr_l(hh2["products"]["Wealth"]["financials"]["aum"])},
    ])
    st.dataframe(transfer_pricing, hide_index=True, use_container_width=True)
    st.caption("Council-published rate cards, reviewed annually. This is the mechanism that keeps factory heads "
               "accountable as capability owners for cost, quality and speed, without letting them own the "
               "customer relationship.")

    st.divider()

    st.subheader("Enterprise impact model")
    st.caption("Adjust the assumptions below to see the projected enterprise-level impact recompute. "
               "Defaults are set to the 2035 targets already stated in the transformation thesis.")

    cross_sell = st.slider("Cross-sell depth, products per customer", 1.5, 3.5, 3.0, 0.1)
    casa_bps = st.slider("CASA and primacy uplift, basis points", 0, 400, 350, 10)
    forex_retained = st.slider("Forex margin retained by the bank versus today, percent", 0, 100, 10, 5)
    customer_base_cr = st.number_input(
        "Addressable customer base, in crore",
        value=5.0, step=0.5,
        help="Set to match the 5 crore-plus base already cited in the transformation thesis.",
    )

    fee_per_product_unit = 100       # Rs per customer, per unit of cross-sell depth, per year
    forex_value_per_customer = 130   # Rs per customer per year, blended across the addressable base
    casa_multiplier = 3              # Rs crore per basis point of CASA and primacy uplift

    cross_sell_component = (cross_sell - 1.5) * fee_per_product_unit * customer_base_cr
    forex_component = forex_value_per_customer * (1 - forex_retained / 100) * customer_base_cr
    casa_component = casa_bps * casa_multiplier

    total_impact = round(cross_sell_component + forex_component + casa_component)

    st.metric("Projected incremental annual profit impact by 2035", f"Rs {total_impact:,.0f} crore")
    st.caption(
        "This is a modeled run-rate, not a multi-year cumulative figure. It is built from the same three drivers "
        "stated in the transformation thesis: cross-sell depth, CASA and primacy uplift, and forex margin "
        "capture, so every input on screen is traceable to an assumption that can be defended in discussion. "
        "At the stated defaults, the model lands close to the scale of the One Axis synergy programme already "
        "disclosed, which is the intended check: this is a scale-up of a mechanism already proven to work, "
        "not an unprecedented bet."
    )
