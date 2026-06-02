import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# Green Hydrogen LCOH Calculator
# ---------------------------------------------------------

st.set_page_config(
    page_title="Green Hydrogen LCOH Calculator",
    layout="wide",
)

# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------


def capital_recovery_factor(discount_rate, lifetime):
    """
    Calculate Capital Recovery Factor (CRF)
    """
    r = discount_rate
    n = lifetime

    if r == 0:
        return 1 / n

    return (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def calculate_lcoh(
    electrolyzer_size_mw,
    electrolyzer_capex,
    electricity_price,
    specific_energy_consumption, #the amount of energy required to produce 1 kg of hydrogen
    capacity_factor, #ratio of actual output to maximum possible output
    opex, 
    discount_rate,
    lifetime,
):
    """
    Calculate LCOH and annual metrics
    """

    # Convert MW to kW
    size_kw = electrolyzer_size_mw * 1000

    # CAPEX
    total_capex = size_kw * electrolyzer_capex

    # Annual operation
    operating_hours = 8760 * capacity_factor

    annual_energy_consumption = size_kw * operating_hours

    annual_hydrogen_production = (
        annual_energy_consumption / specific_energy_consumption
    )

    # Costs
    annual_electricity_cost = (
        annual_energy_consumption * electricity_price
    )

    annual_opex =  opex

    crf = capital_recovery_factor(discount_rate, lifetime)

    annualized_capex = total_capex * crf

    total_annual_cost = (
        annualized_capex
        + annual_opex
        + annual_electricity_cost
    )

    lcoh = total_annual_cost / annual_hydrogen_production

    # Cost breakdown
    capex_component = annualized_capex / annual_hydrogen_production
    opex_component = annual_opex / annual_hydrogen_production
    electricity_component = (
        annual_electricity_cost / annual_hydrogen_production
    )

    annual_h2_tonnes = annual_hydrogen_production / 1000

    return {
        "lcoh": lcoh,
        "annual_h2": annual_hydrogen_production,
        "annual_energy": annual_energy_consumption,
        "annualized_capex": annualized_capex,
        "annual_opex": annual_opex,
        "annual_electricity": annual_electricity_cost,
        "capex_component": capex_component,
        "opex_component": opex_component,
        "electricity_component": electricity_component,
        "annual_h2_tonnes": annual_h2_tonnes,
    }


# ---------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------

st.sidebar.title("Input Parameters")

electrolyzer_size_mw = st.sidebar.number_input(
    "Electrolyzer Size (MW)", 
    min_value=1, 
    value=900, 
    step=1,
    help = "Total capacity of the electrolyzer in megawatts (MW)."
   
)

electrolyzer_capex = st.sidebar.number_input(
    "Electrolyzer CAPEX (€/kW)", 
    min_value=1, 
    value=2100, 
    step=1, 
    help = "Capital cost of the electrolyzer per kW of capacity."
)

electricity_price = st.sidebar.slider(
    "Electricity Price (€/kWh)",
    0.01,
    0.20,
    0.06,
)

specific_energy_consumption = st.sidebar.slider(
    "Specific Energy Consumption (kWh/kg H₂)",
    40.0,
    70.0,
    50.0,
    help = "Energy needed to produce 1 kg of hydrogen."
)

capacity_factor = st.sidebar.slider(
    "Capacity Factor",
    0.10,
    1.00,
    0.85,
    help = "Ratio of actual output to maximum possible output, reflecting plant utilization."
)

opex = st.sidebar.number_input(
    "Annual OPEX (€)", 
    min_value=0.0, 
    value=46000000.0, 
    step=10000.0, 
    help = "Annual operating expenses excluding electricity."
)



discount_rate = (
    st.sidebar.slider(
        "Discount Rate (%)",
        0.0,
        20.0,
        8.0,
        help = "Rate used to discount future cash flows to present value."
    )
    / 100
)

lifetime = st.sidebar.slider(
    "Plant Lifetime (years)",
    5,
    40,
    20,
)

energy_unit = st.sidebar.selectbox(
    "Annual Energy Display Unit",
    ["kWh/year", "GWh/year", "TWh/year"],
    index=0,
)

# ---------------------------------------------------------
# Main title
# ---------------------------------------------------------

st.title("Green Hydrogen LCOH Calculator")

st.markdown(
    """
This tool estimates the **Levelised Cost of Hydrogen (LCOH)** for a
green hydrogen production plant using water electrolysis.

The model includes:
- Capital expenditure (CAPEX)
- Operating expenditure (OPEX)
- Electricity costs
- Financing assumptions
"""
)

# ---------------------------------------------------------
# Run calculations
# ---------------------------------------------------------

results = calculate_lcoh(
    electrolyzer_size_mw,
    electrolyzer_capex,
    electricity_price,
    specific_energy_consumption,
    capacity_factor,
    opex,
    discount_rate,
    lifetime,
)

# ---------------------------------------------------------
# Main metrics
# ---------------------------------------------------------

st.header("Key Results")

col1, col2, col3 = st.columns(3)

col1.markdown(
    f"""
    <div style="text-align:center">
      <p style="font-size:2rem; margin:0; font-weight:600">LCOH</p>
      <p style="font-size:4rem; margin:0">{results['lcoh']:.2f} €/kg H₂</p>
    </div>
    """,
    unsafe_allow_html=True,
)


col2.metric(
    "Annual Hydrogen Production",
    f"{results['annual_h2_tonnes']:,.0f} tonnes/year",
)

energy_factor = 1.0
if energy_unit == "GWh/year":
    energy_factor = 1e-6
elif energy_unit == "TWh/year":
    energy_factor = 1e-9

annual_energy_display = results["annual_energy"] * energy_factor

col3.metric(
    "Annual Electricity Use",
    f"{annual_energy_display:,.2f} {energy_unit}",
)

# ---------------------------------------------------------
# Cost breakdown
# ---------------------------------------------------------

st.header("LCOH Cost Breakdown")

breakdown_df = pd.DataFrame(
    {
        "Component": [
            "CAPEX",
            "OPEX",
            "Electricity",
        ],
        "€/kg H₂": [
            results["capex_component"],
            results["opex_component"],
            results["electricity_component"],
        ],
    }
)

fig, ax = plt.subplots(figsize=(7, 4))

ax.bar(
    breakdown_df["Component"],
    breakdown_df["€/kg H₂"],
)

ax.set_ylabel("€/kg H₂")
ax.set_title("LCOH Breakdown")

st.pyplot(fig)

# ---------------------------------------------------------
# Financial summary
# ---------------------------------------------------------

st.header("Annual Financial Summary")

summary_df = pd.DataFrame(
    {
        "Metric": [
            "Annualized CAPEX",
            "Annual OPEX",
            "Annual Electricity Cost",
        ],
        "Value (€)": [
            results["annualized_capex"],
            results["annual_opex"],
            results["annual_electricity"],
        ],
    }
)

st.dataframe(summary_df, width="stretch")

# ---------------------------------------------------------
# Sensitivity insights
# ---------------------------------------------------------

st.header("Quick Insights")

electricity_share = (
    results["electricity_component"] / results["lcoh"]
) * 100

st.info(
    f"""
Electricity contributes approximately
{electricity_share:.1f}% of the total hydrogen production cost.

This shows how strongly green hydrogen economics depend on
renewable electricity pricing and electrolyzer efficiency.
"""
)

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------

st.markdown("---")

st.caption(
    """
Assumptions:
- Constant annual operation
- Fixed electricity price
- No hydrogen storage or transport costs
- No stack replacement costs
- No water treatment costs
"""
)