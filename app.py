"""
EKAM — One Customer Graph Prototype
------------------------------------
Tab 1: Steward Dashboard    -> banker/admin view of ONE household, with clickable
                               product tiles that drill into full detail
Tab 2: Backend / P&L Engine -> product P&L vs household P&L, transfer pricing,
                               with clickable silos that mirror the same drill-down

Run with:
    pip install streamlit pandas
    streamlit run app.py
"""

import copy
import streamlit as st
import pandas as pd

st.set_page_config(page_title="EKAM — One Customer Graph", layout="wide")

# ---------------------------------------------------------------------------
# MOCK DATA
# Each product carries:
#   value / status / flag  -> shown on the tile itself
#   details                -> read-only info shown when you click the tile
#   cross_sell_fields       -> if present, an admin form is shown to add new info
# ---------------------------------------------------------------------------

HOUSEHOLDS_SEED = {
    "Rohan Mehta — Salaried, Mumbai": {
        "tier": "Mass",
        "ratio": "1 steward : 3,000–5,000 households",
        "health_score": 78,
        "primacy": "CASA share 62%",
        "cross_sell_depth": 2.4,
        "products": {
            "Deposits": {
                "value": "₹4.2L", "status": "Active", "flag": None,
                "details": {
                    "Savings balance": "₹2.8L",
                    "Fixed deposit balance": "₹1.4L",
                    "Average monthly balance": "₹3.5L",
                    "Interest rate": "3.5% p.a.",
                },
            },
            "Loans": {
                "value": "Home loan — ₹68L", "status": "In underwriting", "flag": "New application",
                "details": {
                    "Principal amount": "₹68,00,000",
                    "Tenure": "20 years",
                    "Interest rate": "8.65% (floating)",
                    "EMI": "₹59,800/month",
                    "Purpose": "Home purchase",
                    "Collateral": "Property under registration",
                },
            },
            "Cards": {
                "value": "2 cards active", "status": "Active", "flag": None,
                "details": {
                    "Cards held": "2 (1 rewards, 1 travel)",
                    "Credit limit": "₹3,00,000",
                    "Utilisation": "22%",
                    "Credit score": "762",
                    "Transaction fees (YTD)": "₹1,200",
                    "Customer acquisition cost": "₹450",
                },
            },
            "Insurance": {
                "value": "None", "status": "Not enrolled", "flag": "Cross-sell opportunity",
                "details": {
                    "Current life cover": "None",
                    "Current health cover": "None",
                    "Nominee on file (from KYC)": "Priya Mehta (spouse)",
                    "Related signal": "Home loan in underwriting — insurance typically bundled at disbursement",
                },
                "cross_sell_fields": [
                    {"label": "Policy type", "type": "select", "options": ["Term life", "Health", "Term + Health bundle", "Home loan protection"]},
                    {"label": "Sum assured (₹)", "type": "number", "default": 5000000},
                    {"label": "Annual premium (₹)", "type": "number", "default": 18000},
                    {"label": "Payment frequency", "type": "select", "options": ["Monthly", "Quarterly", "Annual"]},
                ],
            },
            "Wealth": {
                "value": "₹3.1L SIPs", "status": "Active", "flag": None,
                "details": {
                    "Portfolio value": "₹3,10,000",
                    "Funds held": "3 mutual funds",
                    "Monthly SIP": "₹15,000",
                    "Risk profile": "Moderate",
                    "Returns (YTD)": "11.2%",
                },
            },
            "Forex": {
                "value": "$5,000 remittance pending", "status": "Queued", "flag": "Pricing decision needed",
                "details": {
                    "Amount": "$5,000",
                    "Purpose": "Education — dependent's tuition",
                    "Current pricing tier": "Standard desk rate",
                    "Standard markup": "2.5–3.5%",
                    "Ekam household rate": "~0% (netting cost)",
                },
                "cross_sell_fields": [
                    {"label": "Approve household pricing tier", "type": "select", "options": ["Zero-margin (Ekam household rate)", "Standard desk rate (override)"]},
                    {"label": "Approved by (steward name)", "type": "text", "default": ""},
                ],
            },
        },
    },
    "Priya Nair — MSME Owner": {
        "tier": "Complex",
        "ratio": "1 squad+bench : 250–400 households",
        "health_score": 85,
        "primacy": "CASA share 71%",
        "cross_sell_depth": 3.1,
        "products": {
            "Deposits": {
                "value": "₹22L (business + personal)", "status": "Active", "flag": None,
                "details": {
                    "Business account balance": "₹18,00,000",
                    "Personal account balance": "₹4,00,000",
                    "Average balance": "₹20,00,000",
                    "Interest rate": "3.2% p.a.",
                },
            },
            "Loans": {
                "value": "Working capital — ₹1.2Cr", "status": "Active", "flag": None,
                "details": {
                    "Principal / limit": "₹1,20,00,000",
                    "Type": "Revolving working capital",
                    "Interest rate": "10.25%",
                    "Current utilisation": "68%",
                    "Purpose": "Inventory financing",
                },
            },
            "Cards": {
                "value": "Business credit card", "status": "Active", "flag": None,
                "details": {
                    "Cards held": "1 business card",
                    "Credit limit": "₹10,00,000",
                    "Utilisation": "35%",
                    "Credit score": "781",
                    "Transaction fees (YTD)": "₹8,400",
                    "Customer acquisition cost": "₹600",
                },
            },
            "Insurance": {
                "value": "Key-person cover", "status": "Active", "flag": None,
                "details": {
                    "Policy": "Key-person cover",
                    "Sum assured": "₹50,00,000",
                    "Annual premium": "₹42,000",
                    "Renewal date": "March 2027",
                },
            },
            "Wealth": {
                "value": "₹40L portfolio", "status": "Active", "flag": None,
                "details": {
                    "Portfolio value": "₹40,00,000",
                    "Mandate": "Balanced / growth",
                    "Risk profile": "Growth",
                    "Returns (YTD)": "9.8%",
                },
            },
            "Forex": {
                "value": "Import payments — monthly", "status": "Active", "flag": "Recurring volume, review pricing tier",
                "details": {
                    "Pattern": "Recurring monthly import remittance",
                    "Average volume": "$8,000/month",
                    "Current pricing tier": "Standard desk rate (1.8%)",
                    "Eligible for": "Household-tier pricing upgrade",
                },
                "cross_sell_fields": [
                    {"label": "Recommended pricing tier", "type": "select", "options": ["Household-preferred (0.5%)", "Zero-margin (Ekam)", "Keep standard desk rate"]},
                    {"label": "Steward sign-off", "type": "text", "default": ""},
                ],
            },
        },
    },
    "The Kapoor Family — NRI-Linked": {
        "tier": "Private",
        "ratio": "1 dedicated squad : 30–60 households",
        "health_score": 91,
        "primacy": "CASA share 80%",
        "cross_sell_depth": 4.0,
        "products": {
            "Deposits": {
                "value": "₹1.1Cr (NRE/NRO)", "status": "Active", "flag": None,
                "details": {
                    "NRE balance": "₹70,00,000",
                    "NRO balance": "₹41,00,000",
                    "Interest rate": "4.1% p.a.",
                },
            },
            "Loans": {
                "value": "None", "status": "—", "flag": None,
                "details": {"Current exposure": "None on record"},
            },
            "Cards": {
                "value": "3 cards, multi-currency", "status": "Active", "flag": None,
                "details": {
                    "Cards held": "3, multi-currency",
                    "Combined credit limit": "₹8,00,000",
                    "Utilisation": "14%",
                    "Credit score": "812",
                    "Transaction fees (YTD)": "₹5,600",
                    "Customer acquisition cost": "₹900",
                },
            },
            "Insurance": {
                "value": "Family floater + term", "status": "Active", "flag": None,
                "details": {
                    "Policy": "Family floater + term life",
                    "Sum assured": "₹1,00,00,000",
                    "Annual premium": "₹1,10,000",
                    "Renewal date": "January 2027",
                },
            },
            "Wealth": {
                "value": "₹2.4Cr AUM (Burgundy)", "status": "Active", "flag": None,
                "details": {
                    "AUM": "₹2,40,00,000",
                    "Tier": "Burgundy",
                    "Portfolio": "Diversified — equity, debt, alternates",
                    "Returns (YTD)": "13.4%",
                },
            },
            "Forex": {
                "value": "Education remittance — $12,000/yr", "status": "Active", "flag": None,
                "details": {
                    "Pattern": "Annual education remittance",
                    "Amount": "$12,000/year",
                    "Pricing tier": "Household (Ekam) rate",
                    "Markup": "~0%",
                },
            },
        },
    },
}

FEED_SEED = {
    "Rohan Mehta — Salaried, Mumbai": [
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
    "Priya Nair — MSME Owner": [
        {"id": 1, "text": "Recurring import remittance volume detected — eligible for household-tier forex pricing upgrade.",
         "auto": True, "escalate": True,
         "why": "Pricing tier change affects relationship economics — steward sign-off required."},
        {"id": 2, "text": "Working capital utilisation pattern stable — no action needed.",
         "auto": True, "escalate": False},
    ],
    "The Kapoor Family — NRI-Linked": [
        {"id": 1, "text": "Annual education remittance cycle starting — pre-cleared at household rate, no desk involvement.",
         "auto": True, "escalate": False},
    ],
}

PRODUCT_ICONS = {
    "Deposits": "💰", "Loans": "🏠", "Cards": "💳",
    "Insurance": "🛡️", "Wealth": "📈", "Forex": "🌍",
}

# Illustrative, same-for-all-households P&L breakdown per silo (₹L)
PNL_BREAKDOWN = {
    "Deposits": [("Interest expense paid to customer", -3.5), ("Float income earned", 8.2), ("Net contribution", 4.7)],
    "Loans": [("Interest income", 28.0), ("Cost of funds", -14.0), ("Credit provisioning", -3.0), ("Opex", -2.0), ("Net margin", 9.0)],
    "Cards": [("Interchange + fee revenue", 6.0), ("Customer acquisition cost", -1.5), ("Fraud / credit losses", -0.8), ("Net margin", 3.7)],
    "Insurance": [("Commission revenue", 4.0), ("Servicing cost", -1.0), ("Net margin", 3.0)],
    "Wealth": [("AUM-based fee revenue", 9.0), ("Advisory / ops cost", -3.0), ("Net margin", 6.0)],
    "Forex": [("Markup revenue (today)", 7.0), ("Netting cost under Ekam", -6.3), ("Net margin under Ekam", 0.7)],
}
PNL_OWNER = {
    "Deposits": ("Deposits P&L head", "Deposit growth"),
    "Loans": ("Loans P&L head", "Disbursement volume"),
    "Cards": ("Cards P&L head", "Cards issued / spend"),
    "Insurance": ("Insurance JV partner", "Policies sold"),
    "Wealth": ("Wealth P&L head", "AUM growth"),
    "Forex": ("Forex desk", "Margin captured per txn"),
}

# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------
if "escalated" not in st.session_state:
    st.session_state.escalated = set()
if "hh_state" not in st.session_state:
    # deep copy so admin edits never mutate the seed data
    st.session_state.hh_state = copy.deepcopy(HOUSEHOLDS_SEED)
if "selected_product" not in st.session_state:
    st.session_state.selected_product = {}
if "selected_silo" not in st.session_state:
    st.session_state.selected_silo = {}

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
    household_name = st.selectbox("Select household", list(st.session_state.hh_state.keys()), key="hh_select_tab1")
    hh = st.session_state.hh_state[household_name]

    st.divider()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Household Health Score", f"{hh['health_score']}/100")
    c2.metric("Primacy", hh["primacy"])
    c3.metric("Cross-sell depth", f"{hh['cross_sell_depth']}x")
    c4.metric("Coverage tier", hh["tier"], help=hh["ratio"])

    st.info(f"**One steward. One graph.** Coverage model: {hh['ratio']}")

    st.divider()

    # --- Clickable unified product strip ---
    st.subheader("Household — one view, all products")
    st.caption("Click a tile to see full details. Tiles flagged with an opportunity also let you add new information.")

    cols = st.columns(6)
    for col, (product, info) in zip(cols, hh["products"].items()):
        with col:
            is_selected = st.session_state.selected_product.get(household_name) == product
            label = f"{PRODUCT_ICONS.get(product, '')} {product}"
            if st.button(label, key=f"tile-{household_name}-{product}",
                         use_container_width=True, type="primary" if is_selected else "secondary"):
                st.session_state.selected_product[household_name] = product
            st.caption(info["value"])
            if info["flag"]:
                st.warning(info["flag"], icon="⚠️")

    st.markdown("")  # spacing

    selected = st.session_state.selected_product.get(household_name)
    if selected:
        info = hh["products"][selected]
        with st.container(border=True):
            st.markdown(f"### {PRODUCT_ICONS.get(selected, '')} {selected} — full detail")
            st.caption(f"Status: {info['status']}")

            # Read-only current details
            detail_cols = st.columns(2)
            items = list(info["details"].items())
            half = (len(items) + 1) // 2
            for label, value in items[:half]:
                detail_cols[0].markdown(f"**{label}:** {value}")
            for label, value in items[half:]:
                detail_cols[1].markdown(f"**{label}:** {value}")

            # If this tile is a cross-sell / action opportunity, show an add-details form
            if "cross_sell_fields" in info:
                st.divider()
                st.markdown("**Add new details (bank admin action)**")
                already_added = info.get("added")
                if already_added:
                    st.success("✅ Submitted — this household's record now reflects the update below.")
                    for label, value in already_added.items():
                        st.write(f"**{label}:** {value}")
                else:
                    with st.form(key=f"form-{household_name}-{selected}"):
                        entered = {}
                        for field in info["cross_sell_fields"]:
                            if field["type"] == "select":
                                entered[field["label"]] = st.selectbox(field["label"], field["options"],
                                                                        key=f"f-{household_name}-{selected}-{field['label']}")
                            elif field["type"] == "number":
                                entered[field["label"]] = st.number_input(field["label"], value=field["default"],
                                                                           key=f"f-{household_name}-{selected}-{field['label']}")
                            else:
                                entered[field["label"]] = st.text_input(field["label"], value=field["default"],
                                                                         key=f"f-{household_name}-{selected}-{field['label']}")
                        submitted = st.form_submit_button("Save to household record")
                        if submitted:
                            info["added"] = entered
                            info["flag"] = None
                            info["status"] = "Active — pending activation"
                            st.rerun()
    else:
        st.caption("👆 Click any product tile above to drill into its details.")

    st.divider()

    # --- AI Steward feed ---
    st.subheader("AI Steward feed")
    st.caption("AI-first, human at trust moments — everything below resolves automatically unless it's escalated.")

    for item in FEED_SEED[household_name]:
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
    st.caption("Same underlying revenue and cost — a different unit of account, ownership, and incentive. "
               "Click a silo below to see its revenue/cost breakdown.")

    household_name_2 = st.selectbox("Household in view", list(st.session_state.hh_state.keys()), key="hh_select_tab2")
    hh2 = st.session_state.hh_state[household_name_2]

    st.markdown("**Today — six silo P&Ls, nobody owns the household**")

    scols = st.columns(6)
    for col, silo in zip(scols, PNL_BREAKDOWN.keys()):
        with col:
            is_sel = st.session_state.selected_silo.get(household_name_2) == silo
            if st.button(f"{PRODUCT_ICONS.get(silo,'')} {silo}", key=f"silo-{household_name_2}-{silo}",
                         use_container_width=True, type="primary" if is_sel else "secondary"):
                st.session_state.selected_silo[household_name_2] = silo
            net_margin = PNL_BREAKDOWN[silo][-1][1]
            col.caption(f"Net: ₹{net_margin}L")

    sel_silo = st.session_state.selected_silo.get(household_name_2)
    if sel_silo:
        owner, incentive = PNL_OWNER[sel_silo]
        with st.container(border=True):
            st.markdown(f"### {PRODUCT_ICONS.get(sel_silo,'')} {sel_silo} — P&L breakdown")
            c1, c2 = st.columns(2)
            c1.markdown(f"**Owner today:** {owner}")
            c2.markdown(f"**Incentive tied to:** {incentive}")

            breakdown_df = pd.DataFrame(PNL_BREAKDOWN[sel_silo], columns=["Line item", "₹L"])
            st.dataframe(breakdown_df, hide_index=True, use_container_width=True)

            # Mirror the Tab-1 cross-sell opportunity here, read-only + same form
            product_info = hh2["products"].get(sel_silo, {})
            if "cross_sell_fields" in product_info and "added" not in product_info:
                st.warning("This silo currently shows an untapped opportunity for this household "
                           "(see the matching flag in the Steward Dashboard tab).", icon="⚠️")
                st.markdown("**What we already know (read-only):**")
                for label, value in product_info["details"].items():
                    st.write(f"- **{label}:** {value}")
                st.caption("➡️ Add this household's new details from the **Steward Dashboard** tab — "
                           "once saved there, it will show as resolved here too, since both tabs read the same household record.")
            elif "added" in product_info:
                st.success("✅ Opportunity resolved — admin-entered details now feeding into this household's P&L.")
                for label, value in product_info["added"].items():
                    st.write(f"- **{label}:** {value}")
    else:
        st.caption("👆 Click a silo above to see its revenue/cost breakdown and internal ownership.")

    st.caption(
        "Six-silo view sums to a total revenue and margin — but no single number represents *this household's* "
        "total relationship value, and no single owner is accountable for it."
    )

    st.divider()

    st.markdown("**Ekam — one household P&L, one steward accountable**")
    total_revenue = sum(items[0][1] if items[0][1] > 0 else 0 for items in PNL_BREAKDOWN.values())
    colA, colB, colC = st.columns(3)
    colA.metric("Household revenue", f"₹{total_revenue:.1f}L", help="Same underlying revenue — now attributed to one household, not six silos.")
    colB.metric("Forex margin foregone", "− ₹7L → ~₹0.7L", help="Zero-margin forex is the falsifiable proof the model changed.")
    colC.metric("Cross-sell synergy gain", "+ ₹5L (est.)", help="Captured because the steward can see and act on the whole graph, not one product at a time.")

    st.divider()

    st.subheader("Transfer pricing — how factories charge squads")
    st.caption("Product teams don't disappear — they become internal factories, selling capacity to relationship squads at a published internal rate.")

    transfer_pricing = pd.DataFrame([
        {"Factory": "Loans Ops", "Internal rate charged to squad": "Cost-plus SLA rate", "Volume this household": "1 active file"},
        {"Factory": "Insurance Ops", "Internal rate charged to squad": "Per-policy service fee", "Volume this household": "0 policies (opportunity)"},
        {"Factory": "Forex Ops", "Internal rate charged to squad": "Netting cost (~0 markup)", "Volume this household": "1 pending remittance"},
        {"Factory": "Wealth Ops", "Internal rate charged to squad": "bps on AUM serviced", "Volume this household": "₹3.1L SIP book"},
    ])
    st.dataframe(transfer_pricing, hide_index=True, use_container_width=True)
    st.caption(
        "Council-published rate cards, reviewed annually — this is the mechanism that keeps factory heads as "
        "capability owners (cost, quality, speed) without letting them own the customer relationship."
    )

    st.divider()

    st.subheader("Live impact calculator")
    st.caption("Drag the assumptions to see the projected 2035 impact recompute.")

    cross_sell = st.slider("Cross-sell depth (products per customer)", 1.5, 4.0, 2.4, 0.1)
    casa_bps = st.slider("CASA / primacy uplift (bps)", 0, 400, 150, 10)
    forex_capture = st.slider("Forex margin retained vs today (%)", 0, 100, 20, 5)
    customer_base_cr = st.number_input("Customer base (Cr customers)", value=3.0, step=0.5)

    baseline_fee_per_product = 8000
    baseline_forex_loss_per_customer = 1200

    incremental_cross_sell_revenue = (cross_sell - 1.5) * baseline_fee_per_product * customer_base_cr
    forex_value_unlocked = baseline_forex_loss_per_customer * (1 - forex_capture / 100) * customer_base_cr
    casa_value = casa_bps * 0.5

    total_impact = round(incremental_cross_sell_revenue + forex_value_unlocked + casa_value, 0)

    st.metric("Estimated cumulative impact by 2035 (illustrative)", f"₹{total_impact:,.0f} Cr")
    st.caption(
        "⚠️ Illustrative model for pitch purposes — built from the deck's own stated drivers "
        "(cross-sell depth, CASA/primacy bps, forex margin capture) so every number on screen is traceable "
        "to an assumption you can defend, not a black box."
    )
