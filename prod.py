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
    }


# ---------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------

st.sidebar.title("Input Parameters")

electrolyzer_size_mw = st.sidebar.slider(
    "Electrolyzer Size (MW)",
    1.0,
    500.0,
    20.0,
)

electrolyzer_capex = st.sidebar.slider(
    "Electrolyzer CAPEX (€/kW)",
    300,
    2500,
    900,
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
)

capacity_factor = st.sidebar.slider(
    "Capacity Factor",
    0.1,
    1.0,
    0.85,
)

opex = (
    st.sidebar.slider(
        "Annual OPEX ",
        0.0,
        2500,
        3.0,
    )
    / 100
)

discount_rate = (
    st.sidebar.slider(
        "Discount Rate (%)",
        0.0,
        20.0,
        8.0,
    )
    / 100
)

lifetime = st.sidebar.slider(
    "Plant Lifetime (years)",
    5,
    40,
    20,
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
- Plant utilization
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

col1.metric(
    "LCOH",
    f"{results['lcoh']:.2f} €/kg H₂",
)

col2.metric(
    "Annual Hydrogen Production",
    f"{results['annual_h2']:,.0f} kg/year",
)

col3.metric(
    "Annual Electricity Use",
    f"{results['annual_energy']:,.0f} kWh/year",
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

st.dataframe(summary_df, use_container_width=True)

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