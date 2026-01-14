import streamlit as st
import pandas as pd
import numpy as np
import itertools
import plotly.express as px
import plotly.graph_objects as go
import random

def main():
    st.set_page_config(page_title="GSAT Scoring Simulation", page_icon="📝", layout="wide")
    
    st.title("GSAT Multichoice Scoring Strategies")
    
    # --- Sidebar Controls ---
    st.sidebar.header("Parameters")
    
    x = st.sidebar.number_input("Known Correct Options (x)", min_value=0, max_value=5, value=0, step=1)
    y = st.sidebar.number_input("Known Incorrect Options (y)", min_value=0, max_value=5, value=0, step=1)

    if x + y > 5:
        st.error(f"Error: x + y ({x+y}) cannot exceed 5.")
        return

    remaining_options = 5 - x - y
    st.sidebar.markdown(f"**Remaining Unknown Options:** {remaining_options}")

    st.sidebar.subheader("Scoring Rules")
    scoring_mode = st.sidebar.radio(
        "Select Scoring Logic",
        options=[
            "Custom (5 - Errors)",
            "GSAT Standard (5/3/1/0)",
            "Strict Binary (5 or 0)",
            "All"
        ],
        index=0
    )

    # --- Shared Calculation Logic ---
    # 1. Generate Truth Worlds
    all_worlds = list(itertools.product([True, False], repeat=5))
    valid_worlds = [w for w in all_worlds if any(w)] 
    
    compatible_worlds = []
    for w in valid_worlds:
        if not all(w[i] for i in range(x)): continue
        if any(w[i] for i in range(x, x+y)): continue
        compatible_worlds.append(w)

    if not compatible_worlds:
        st.warning("No valid scenarios exist for these inputs.")
        return

    # Helper function to calculate scores
    def calculate_scores(selection, world_list):
        # selection: [True/False]*5
        # world_list: list of [True/False]*5
        results = {"Custom": [], "GSAT": [], "Strict": []}
        
        is_empty = not any(selection)
        
        for w in world_list:
            if is_empty:
                results["Custom"].append(0)
                results["GSAT"].append(0)
                results["Strict"].append(0)
                continue
                
            fp = 0
            fn = 0
            for i in range(5):
                if selection[i] and not w[i]: fp += 1
                if not selection[i] and w[i]: fn += 1
            errors = fp + fn
            
            results["Custom"].append(max(0, 5 - errors))
            
            if errors == 0: s_gsat = 5
            elif errors == 1: s_gsat = 3
            elif errors == 2: s_gsat = 1
            else: s_gsat = 0
            results["GSAT"].append(s_gsat)
            
            results["Strict"].append(5 if errors == 0 else 0)
            
        return results

    # --- TABS ---
    tab1, tab2 = st.tabs(["📊 Theoretical Analysis", "🎲 Monte Carlo Simulation"])

    # --- TAB 1: Theoretical Analysis ---
    with tab1:
        st.markdown(f"### Theoretical Expected Values (Based on {len(compatible_worlds)} equal-probability worlds)")
        
        results = []
        possible_z_values = range(remaining_options + 1)
        
        for z in possible_z_values:
            selection = [False]*5
            for i in range(x): selection[i] = True
            for i in range(z): selection[x+y+i] = True
            
            scores = calculate_scores(selection, compatible_worlds)
            
            # Helper to get stats
            def get_stats(score_list):
                return np.mean(score_list), np.std(score_list), score_list

            ev_custom, std_custom, dist_custom = get_stats(scores["Custom"])
            ev_gsat, std_gsat, dist_gsat = get_stats(scores["GSAT"])
            ev_strict, std_strict, dist_strict = get_stats(scores["Strict"])
            
            results.append({
                "Guess Count (z)": z,
                "Total Selected": x + z,
                "EV (Custom)": ev_custom, "Std Dev (Custom)": std_custom,
                "EV (GSAT)": ev_gsat, "Std Dev (GSAT)": std_gsat,
                "EV (Strict)": ev_strict, "Std Dev (Strict)": std_strict,
                "_dist_custom": dist_custom, "_dist_gsat": dist_gsat, "_dist_strict": dist_strict
            })

        df = pd.DataFrame(results)
        
        # Display Table
        target_cols = ["Guess Count (z)", "Total Selected"]
        if scoring_mode == "All":
            target_cols += ["EV (Custom)", "Std Dev (Custom)", "EV (GSAT)", "Std Dev (GSAT)", "EV (Strict)", "Std Dev (Strict)"]
        elif "Custom" in scoring_mode: target_cols += ["EV (Custom)", "Std Dev (Custom)"]
        elif "GSAT" in scoring_mode: target_cols += ["EV (GSAT)", "Std Dev (GSAT)"]
        else: target_cols += ["EV (Strict)", "Std Dev (Strict)"]
            
        st.dataframe(df[target_cols].style.highlight_max(axis=0, subset=[c for c in target_cols if "EV" in c]), use_container_width=True)
        
        # Display Chart
        if scoring_mode == "All":
            melted = df.melt(id_vars=["Guess Count (z)"], value_vars=["EV (Custom)", "EV (GSAT)", "EV (Strict)"], 
                             var_name="Mode", value_name="EV")
            fig = px.line(melted, x="Guess Count (z)", y="EV", color="Mode", markers=True)
        else:
            y_col = [c for c in target_cols if "EV" in c][0]
            fig = px.line(df, x="Guess Count (z)", y=y_col, markers=True, title="Expected Value Trend")
        st.plotly_chart(fig, use_container_width=True)
        
        # Distribution
        st.divider()
        st.subheader("Score Distribution")
        col1, col2 = st.columns([1,2])
        with col1:
            z_select = st.selectbox("Select z to view distribution", possible_z_values)
            dist_key = "Custom"
            if scoring_mode == "All":
                dist_key = st.radio("Select Scoring Mode", ["Custom", "GSAT", "Strict"])
            elif "GSAT" in scoring_mode: dist_key = "GSAT"
            elif "Strict" in scoring_mode: dist_key = "Strict"
            
            row = df[df["Guess Count (z)"] == z_select].iloc[0]
            scores = row[f"_dist_{dist_key.lower()}"]
            
        with col2:
            counts = pd.Series(scores).value_counts(normalize=True).reset_index()
            counts.columns = ["Score", "Probability"]
            fig_dist = px.bar(counts, x="Score", y="Probability", text_auto='.1%', range_x=[-0.5, 5.5], title=f"z={z_select}, {dist_key}")
            st.plotly_chart(fig_dist, use_container_width=True)

    # --- TAB 2: Monte Carlo Simulation ---
    with tab2:
        st.markdown("### 🎲 Monte Carlo Simulation (N=k Trials)")
        
        col1, col2 = st.columns(2)
        with col1:
            k_trials = st.number_input("Number of Trials (k)", min_value=10, max_value=100000, value=1000, step=100)
        with col2:
            z_sim = st.selectbox("Select Strategy (z to guess)", possible_z_values, key="z_sim")
            
        if st.button("Run Simulation"):
            # Setup Strategy
            selection = [False]*5
            for i in range(x): selection[i] = True
            for i in range(z_sim): selection[x+y+i] = True
            
            # Run Simulation
            # Randomly sample worlds
            sampled_worlds = random.choices(compatible_worlds, k=k_trials)
            sim_scores = calculate_scores(selection, sampled_worlds)
            
            # Determine which result to show
            if scoring_mode == "All":
                modes_to_show = ["Custom", "GSAT", "Strict"]
            elif "Custom" in scoring_mode: modes_to_show = ["Custom"]
            elif "GSAT" in scoring_mode: modes_to_show = ["GSAT"]
            else: modes_to_show = ["Strict"]
            
            for m in modes_to_show:
                s_data = sim_scores[m]
                actual_mean = np.mean(s_data)
                
                # Get Theoretical Mean for comparison
                theo_row = df[df["Guess Count (z)"] == z_sim].iloc[0]
                theo_mean = theo_row[f"EV ({m})"]
                
                st.subheader(f"Results for {m} Scoring")
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                metric_col1.metric("Simulated Avg", f"{actual_mean:.4f}")
                metric_col2.metric("Theoretical EV", f"{theo_mean:.4f}")
                metric_col3.metric("Diff", f"{actual_mean - theo_mean:.4f}")
                
                # Histogram Comparison
                fig_sim = go.Figure()
                fig_sim.add_trace(go.Histogram(x=s_data, histnorm='probability', name='Simulated', opacity=0.75))
                
                # Add theoretical markers
                theo_dist = theo_row[f"_dist_{m.lower()}"]
                theo_counts = pd.Series(theo_dist).value_counts(normalize=True).sort_index()
                fig_sim.add_trace(go.Scatter(x=theo_counts.index, y=theo_counts.values, mode='markers', name='Theoretical', marker=dict(size=12, symbol="star", color="red")))
                
                fig_sim.update_layout(title=f"Simulation vs Theory (N={k_trials})", xaxis_title="Score", yaxis_title="Probability", barmode='overlay')
                st.plotly_chart(fig_sim, use_container_width=True)

if __name__ == "__main__":
    main()
