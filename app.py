"""
EKAM — One Customer Graph Prototype
------------------------------------
Tab 1: Steward Dashboard   -> what a banker/admin sees managing ONE household
Tab 2: Backend / P&L Engine -> how the household P&L + transfer pricing actually works

Run with:
    pip install streamlit pandas
    streamlit run steward_dashboard_app.py
"""

import streamlit as st
import pandas as pd

st.set_page_config(page_title="EKAM — One Customer Graph", layout="wide")

# ---------------------------------------------------------------------------
# MOCK DATA
# ---------------------------------------------------------------------------

HOUSEHOLDS = {
    "Rohan Mehta — Salaried, Mumbai": {
        "tier": "Mass",
        "ratio": "1 steward : 3,000–5,000 households",
        "health_score": 78,
        "primacy": "CASA share 62%",
        "cross_sell_depth": 2.4,
        "products": {
            "Deposits": {"value": "₹4.2L", "status": "Active", "flag": None},
            "Loans":    {"value": "Home loan — ₹68L", "status": "In underwriting", "flag": "New application"},
            "Cards":    {"value": "2 cards active", "status": "Active", "flag": None},
            "Insurance":{"value": "None", "status": "Not enrolled", "flag": "Cross-sell opportunity"},
            "Wealth":   {"value": "₹3.1L SIPs", "status": "Active", "flag": None},
            "Forex":    {"value": "$5,000 remittance pending", "status": "Queued", "flag": "Pricing decision needed"},
        },
        "feed": [
            {"id": 1, "text": "CKYC 2.0 auto-verified identity for loan + forex request — no re-documentation needed.",
             "auto": True, "escalate": False},
            {"id": 2, "text": "Household has 4/6 products + a college remittance pattern — flagging a wealth/education-planning conversation.",
             "auto": True, "escalate": True,
             "why": "Cross-sell judgment call: needs a relationship conversation, not just a system nudge — routed to human steward."},
            {"id": 3, "text": "Forex priced at netting cost (~0 markup) instead of desk rate — auto-applied, household-level pricing rule.",
             "auto": True, "escalate": False},
            {"id": 4, "text": "Income category changed on latest salary credit — recommend reviewing loan eligibility and life-stage needs together.",
             "auto": True, "escalate": True,
             "why": "Trust moment: a change in life/income circumstances should be a human conversation, not an automated parameter update."},
        ],
    },
    "Priya Nair — MSME Owner": {
        "tier": "Complex",
        "ratio": "1 squad+bench : 250–400 households",
        "health_score": 85,
        "primacy": "CASA share 71%",
        "cross_sell_depth": 3.1,
        "products": {
            "Deposits": {"value": "₹22L (business + personal)", "status": "Active", "flag": None},
            "Loans":    {"value": "Working capital — ₹1.2Cr", "status": "Active", "flag": None},
            "Cards":    {"value": "Business credit card", "status": "Active", "flag": None},
            "Insurance":{"value": "Key-person cover", "status": "Active", "flag": None},
            "Wealth":   {"value": "₹40L portfolio", "status": "Active", "flag": None},
            "Forex":    {"value": "Import payments — monthly", "status": "Active", "flag": "Recurring volume, review pricing tier"},
        },
        "feed": [
            {"id": 1, "text": "Recurring import remittance volume detected — eligible for household-tier forex pricing upgrade.",
             "auto": True, "escalate": True,
             "why": "Pricing tier change affects relationship economics — steward sign-off required."},
            {"id": 2, "text": "Working capital utilisation pattern stable — no action needed.",
             "auto": True, "escalate": False},
        ],
    },
    "The Kapoor Family — NRI-Linked": {
        "tier": "Private",
        "ratio": "1 dedicated squad : 30–60 households",
        "health_score": 91,
        "primacy": "CASA share 80%",
        "cross_sell_depth": 4.0,
        "products": {
            "Deposits": {"value": "₹1.1Cr (NRE/NRO)", "status": "Active", "flag": None},
            "Loans":    {"value": "None", "status": "—", "flag": None},
            "Cards":    {"value": "3 cards, multi-currency", "status": "Active", "flag": None},
            "Insurance":{"value": "Family floater + term", "status": "Active", "flag": None},
            "Wealth":   {"value": "₹2.4Cr AUM (Burgundy)", "status": "Active", "flag": None},
            "Forex":    {"value": "Education remittance — $12,000/yr", "status": "Active", "flag": None},
        },
        "feed": [
            {"id": 1, "text": "Annual education remittance cycle starting — pre-cleared at household rate, no desk involvement.",
             "auto": True, "escalate": False},
        ],
    },
}

# ---------------------------------------------------------------------------
# SESSION STATE — remember which feed items have been escalated
# ---------------------------------------------------------------------------
if "escalated" not in st.session_state:
    st.session_state.escalated = set()

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.title("EKAM — One Customer Graph")
st.caption("Prototype: banker/steward admin interface, and the P&L engine running underneath it.")

tab1, tab2 = st.tabs(["🧑‍💼 Steward Dashboard", "⚙️ Backend — P&L Engine"])

# ===========================================================================
# TAB 1 — STEWARD DASHBOARD (banker/admin-facing)
# ===========================================================================
with tab1:
    household_name = st.selectbox("Select household", list(HOUSEHOLDS.keys()))
    hh = HOUSEHOLDS[household_name]

    st.divider()

    # --- Household header ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Household Health Score", f"{hh['health_score']}/100")
    c2.metric("Primacy", hh["primacy"])
    c3.metric("Cross-sell depth", f"{hh['cross_sell_depth']}x")
    c4.metric("Coverage tier", hh["tier"], help=hh["ratio"])

    st.info(f"**One steward. One graph.** Coverage model: {hh['ratio']}")

    st.divider()

    # --- Unified product strip ---
    st.subheader("Household — one view, all products")
    cols = st.columns(6)
    for col, (product, info) in zip(cols, hh["products"].items()):
        with col:
            st.markdown(f"**{product}**")
            st.write(info["value"])
            st.caption(info["status"])
            if info["flag"]:
                st.warning(info["flag"], icon="⚠️")

    st.divider()

    # --- AI Steward feed ---
    st.subheader("AI Steward feed")
    st.caption("AI-first, human at trust moments — everything below resolves automatically unless it's escalated.")

    for item in hh["feed"]:
        key = f"{household_name}-{item['id']}"
        with st.container(border=True):
            st.write(item["text"])
            if item["escalate"]:
                if key in st.session_state.escalated:
                    st.error(f"🔺 **Escalated to human steward** — {item['why']}")
                else:
                    if st.button("Escalate to human steward", key=f"btn-{key}"):
                        st.session_state.escalated.add(key)
                        st.rerun()
            else:
                st.success("✅ Resolved automatically — no human action needed", icon="✅")

    st.divider()

    # --- Governance badge ---
    st.subheader("Governance")
    g1, g2, g3 = st.columns(3)
    g1.success("✅ Credit sanction — independent")
    g2.success("✅ Risk — independent")
    g3.success("✅ Compliance — independent")
    st.caption("Three lines of defence never sit inside relationship squads — they read one graph instead of five.")

# ===========================================================================
# TAB 2 — BACKEND: HOW THE P&L ACTUALLY WORKS
# ===========================================================================
with tab2:
    st.subheader("Product P&L (today) vs Household P&L (Ekam)")
    st.caption("Same underlying revenue and cost — a different unit of account, ownership, and incentive.")

    # --- Product P&L (today) ---
    product_pnl = pd.DataFrame([
        {"Silo": "Deposits",  "Revenue (₹L)": 12, "Cost (₹L)": 4, "Owner": "Deposits P&L head", "Incentive tied to": "Deposit growth"},
        {"Silo": "Loans",     "Revenue (₹L)": 28, "Cost (₹L)": 9, "Owner": "Loans P&L head",    "Incentive tied to": "Disbursement volume"},
        {"Silo": "Cards",     "Revenue (₹L)": 6,  "Cost (₹L)": 2, "Owner": "Cards P&L head",     "Incentive tied to": "Cards issued / spend"},
        {"Silo": "Insurance", "Revenue (₹L)": 4,  "Cost (₹L)": 1, "Owner": "Insurance JV partner","Incentive tied to": "Policies sold"},
        {"Silo": "Wealth",    "Revenue (₹L)": 9,  "Cost (₹L)": 3, "Owner": "Wealth P&L head",    "Incentive tied to": "AUM growth"},
        {"Silo": "Forex",     "Revenue (₹L)": 7,  "Cost (₹L)": 1, "Owner": "Forex desk",         "Incentive tied to": "Margin captured per txn"},
    ])
    product_pnl["Margin (₹L)"] = product_pnl["Revenue (₹L)"] - product_pnl["Cost (₹L)"]

    st.markdown("**Today — six silo P&Ls, nobody owns the household**")
    st.dataframe(product_pnl, hide_index=True, use_container_width=True)
    st.caption(
        f"Sum of six silos: ₹{product_pnl['Revenue (₹L)'].sum()}L revenue, "
        f"₹{product_pnl['Margin (₹L)'].sum()}L margin — but no single number represents *this household's* "
        "total relationship value, and no single owner is accountable for it."
    )

    st.divider()

    st.markdown("**Ekam — one household P&L, one steward accountable**")
    hh_revenue = product_pnl["Revenue (₹L)"].sum()
    hh_cost_before = product_pnl["Cost (₹L)"].sum()

    colA, colB, colC = st.columns(3)
    colA.metric("Household revenue", f"₹{hh_revenue}L", help="Same underlying revenue — now attributed to one household, not six silos.")
    colB.metric("Forex margin foregone", "− ₹7L → ~₹0", help="Zero-margin forex is the falsifiable proof the model changed.")
    colC.metric("Cross-sell synergy gain", "+ ₹5L (est.)", help="Captured because the steward can see and act on the whole graph, not one product at a time.")

    st.divider()

    # --- Transfer pricing between factories and squads ---
    st.subheader("Transfer pricing — how factories charge squads")
    st.caption("Product teams don't disappear — they become internal factories, selling capacity to relationship squads at a published internal rate.")

    transfer_pricing = pd.DataFrame([
        {"Factory": "Loans Ops",     "Internal rate charged to squad": "Cost-plus SLA rate", "Volume this household": "1 active file"},
        {"Factory": "Insurance Ops", "Internal rate charged to squad": "Per-policy service fee", "Volume this household": "0 policies (opportunity)"},
        {"Factory": "Forex Ops",     "Internal rate charged to squad": "Netting cost (~0 markup)", "Volume this household": "1 pending remittance"},
        {"Factory": "Wealth Ops",    "Internal rate charged to squad": "bps on AUM serviced", "Volume this household": "₹3.1L SIP book"},
    ])
    st.dataframe(transfer_pricing, hide_index=True, use_container_width=True)
    st.caption(
        "Council-published rate cards, reviewed annually — this is the mechanism that keeps factory heads as "
        "capability owners (cost, quality, speed) without letting them own the customer relationship."
    )

    st.divider()

    # --- Live impact calculator ---
    st.subheader("Live impact calculator")
    st.caption("Drag the assumptions to see the projected 2035 impact recompute.")

    cross_sell = st.slider("Cross-sell depth (products per customer)", 1.5, 4.0, 2.4, 0.1)
    casa_bps = st.slider("CASA / primacy uplift (bps)", 0, 400, 150, 10)
    forex_capture = st.slider("Forex margin retained vs today (%)", 0, 100, 20, 5)
    customer_base_cr = st.number_input("Customer base (Cr customers)", value=3.0, step=0.5)

    baseline_fee_per_product = 8000       # ₹ per product per customer per year (illustrative)
    baseline_forex_loss_per_customer = 1200  # ₹ per year (illustrative)

    incremental_cross_sell_revenue = (cross_sell - 1.5) * baseline_fee_per_product * customer_base_cr * 1e7 / 1e7  # ₹ Cr, simplified
    forex_value_unlocked = baseline_forex_loss_per_customer * (1 - forex_capture / 100) * customer_base_cr * 1e7 / 1e7
    casa_value = casa_bps * 0.5  # illustrative multiplier, ₹ Cr

    total_impact = round(incremental_cross_sell_revenue + forex_value_unlocked + casa_value, 0)

    st.metric("Estimated cumulative impact by 2035 (illustrative)", f"₹{total_impact:,.0f} Cr")
    st.caption(
        "⚠️ Illustrative model for pitch purposes — built from the deck's own stated drivers "
        "(cross-sell depth, CASA/primacy bps, forex margin capture) so every number on screen is traceable "
        "to an assumption you can defend, not a black box."
    )
