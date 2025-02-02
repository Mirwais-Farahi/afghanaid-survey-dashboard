import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from data_loader import load_dataset
from gis_analysis import add_location_columns
from data_visualization import group_by_visualize_and_download, display_group_by_table, plot_boxplot, plot_time_series, show_eligibility_table, visualize_eligibility

from data_analysis import calculate_statistics, filter_data, apply_filters, filter_short_surveys, get_unique_responses, filter_responses
from streamlit_extras.metric_cards import style_metric_cards
from datetime import datetime

st.set_page_config(page_title="Dashboard", page_icon="🌍", layout="wide")

# Load Style CSS
def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def home():
    st.title("Welcome to the Data Dashboard!")
    st.markdown(
        """
        This application provides insights into various datasets collected from field surveys. 
        Use the navigation menu on the left to select a project and explore the data.
        
        ### Features:
        - Data filtering
        - Statistical analysis
        - Visual data representation
        
        Select a dataset from the menu to begin!
        """
    )

# Global variable to store the dataset
dataset_load = None

def load_data(selected, submitted_after):
    global dataset_load
    dataset_load = load_dataset(selected, submitted_after=submitted_after)

def tracker():
    global dataset_load

    if dataset_load is not None and not dataset_load.empty:
        st.success(f"{st.session_state.selected_option} dataset loaded successfully!")

        available_columns = dataset_load.columns.tolist()
        selected_columns = st.multiselect("Select columns to filter:", available_columns)

        # Filter data dynamically
        filters = filter_data(dataset_load, selected_columns)
        for column in filters.keys():
            filters[column] = st.multiselect(f"Select values for {column}:", filters[column])
        filtered_data = apply_filters(dataset_load, filters)

        with st.expander("VIEW EXCEL DATASET"):
            showData = st.multiselect('Filter columns to display:', filtered_data.columns.tolist())
            if showData:
                st.dataframe(filtered_data[showData], use_container_width=True)

        selected_columns = st.multiselect("Select Columns for Statistical Calculation:", filtered_data.dropna(axis=1, how='all').columns.tolist(), default=[])

        total_1 = len(filtered_data) if len(filtered_data) > 0 else 0
        total_2_mean, total_2_median, total_3_min, total_3_max, total_4 = calculate_statistics(filtered_data, selected_columns)

        total1, total2, total3, total4 = st.columns(4, gap='small')
        with total1:
            st.metric(label="Total Surveys", value=f"{total_1:,.0f}", help="Total Collected Surveys")
        with total2:
            st.metric(label="Mean / Median", value=f"{total_2_mean:,.0f} / {total_2_median:,.0f}", help=selected_columns[0] if len(selected_columns) > 0 else "No Columns Selected")
        with total3:
            st.metric(label="Min / Max", value=f"{total_3_min:,.0f} / {total_3_max:,.0f}", help=selected_columns[1] if len(selected_columns) > 1 else "No Columns Selected")
        with total4:
            st.metric(label="Number of Outliers", value=f"{total_4:,.0f}", help=selected_columns[2] if len(selected_columns) > 2 else "No Columns Selected")

        style_metric_cards(background_color="#FFFFFF", border_left_color="#686664", border_color="#000000", box_shadow="#F71938")

        plot_time_series(filtered_data)
        group_by_visualize_and_download(filtered_data)
        display_group_by_table(filtered_data)
    else:
        st.warning("No data available for the selected option.")

def data_quality_review():
    global dataset_load

    if dataset_load is not None and not dataset_load.empty:
        st.success(f"{st.session_state.selected_option} dataset loaded successfully!")

        available_columns = dataset_load.columns.tolist()
        selected_columns = st.multiselect("Select columns to filter:", available_columns, key="data_quality_review_columns")

        # Filter data dynamically
        filters = filter_data(dataset_load, selected_columns)
        
        # Use unique keys for each filter multiselect
        for column in filters.keys():
            filters[column] = st.multiselect(f"Select values for {column}:", filters[column], key=f"filter_{column}")

        filtered_data = apply_filters(dataset_load, filters)
        filtered_data = filtered_data.dropna(axis=1, how='all')
        # Display filtered data or other relevant information as needed
        st.dataframe(filtered_data.head())

        # Remove null columns for single selection box
        non_null_columns = filtered_data.columns.tolist()
        column_for_boxplot = st.selectbox("Select a numeric column for box-plot:", non_null_columns)

        if st.button("Plot Box-Plot"):
            plot_boxplot(filtered_data, column_for_boxplot)

        # Surveys duration analysis
        available_columns = filtered_data.columns.tolist()
        selected_columns = st.multiselect("Select Start and End Date Columns:", available_columns, max_selections=2)

        # Step 2: Validate the selection
        if len(selected_columns) == 2:
            start_column, end_column = selected_columns

            # Step 3: Call the function to filter short surveys
            short_survey_data = filter_short_surveys(filtered_data, start_column, end_column)

            # Display the filtered results
            if not short_survey_data.empty:
                st.write("Surveys completed in less than 30 minutes:")
                st.dataframe(short_survey_data)  # Display the filtered surveys
                # Call the download function when the button is pressed
            else:
                st.write("No surveys found that took less than 30 minutes.")
        else:
            st.warning("Please select exactly two columns for the start and end dates.")

        with st.expander("DATA INCONSISTENCY ANALYSIS"):
            first_question = st.selectbox("Select First Question", available_columns)
            first_response = st.selectbox("Select First Response", get_unique_responses(filtered_data, first_question))

            second_question = st.selectbox("Select Second Question", available_columns)
            second_response = st.selectbox("Select Second Response", get_unique_responses(filtered_data, second_question))

            # Filter DataFrame
            if st.button("Apply Filter"):
                filtered_response = filter_responses(filtered_data, first_question, second_question, first_response, second_response)
                
                st.write("Filtered Data:")
                st.dataframe(filtered_response)
            else:
                st.warning("No data available for the selected filter criteria.")
        with st.expander("GPS LOCATION ANALYSIS"):
            geo_column = st.selectbox("Select GPS Locations Column", available_columns)

            if st.button("Add Location Data"):
                # Apply the function and update the DataFrame
                updated_df = add_location_columns(filtered_data, geo_column)
                
                st.write("Updated DataFrame with Location Columns:")
                st.dataframe(updated_df)
    else:
        st.warning("No data available for the selected option.")

def baseline_eligibility_analysis():
    global dataset_load

    if dataset_load is not None and not dataset_load.empty:
        st.success(f"{st.session_state.selected_option} dataset loaded successfully!")

        available_columns = dataset_load.columns.tolist()
        selected_columns = st.multiselect("Apply filter:", available_columns, key="baseline_eligibility_analysis")

        # Filter data dynamically
        filters = filter_data(dataset_load, selected_columns)

        # Use unique keys for each filter multiselect
        for column in filters.keys():
            filters[column] = st.multiselect(f"Select values for {column}:", filters[column], key=f"filter_{column}")

        # Apply filters and drop columns with only NaN values
        filtered_data = apply_filters(dataset_load, filters).dropna(axis=1, how='all')

        # Define parameters for both interventions in a single dictionary
        parameters = {
            "Wheat": {
                "eligibility_criteria": [
                    {
                        "eligibility_column": "part_2_wheat/part_2_agriculture/part_2_irrigated_land",
                        "eligibility_range": (2, 5),
                        "criteria_description": "Household Dependence on Subsistence Farming with Access to 2-5 Jeribs of Irrigated Land"
                    },
                    {
                        "eligibility_column": "part_2_wheat/part_2_agriculture/part_2_access_seed",
                        "eligibility_value": "no",
                        "criteria_description": "Households with No Access to Improved Wheat Seeds"
                    },
                    {
                        "eligibility_column": ["fcs/cereals", "fcs/pulses", "fcs/milk", "fcs/meat", "fcs/veg", "fcs/fruit", "fcs/oil", "fcs/sugar"],
                        "eligibility_range": (0, 42),
                        "criteria_description": "Household Food Consumption Scores: Poor to Borderline"
                    }
                ]
            },
            "Livestock": {
                "eligibility_criteria": [
                    {
                        "eligibility_column": "part_1_livestock/part_1_livestock_sub_section/part_1_main_livelihood",
                        "eligibility_value": "yes",
                        "criteria_description": "HH Depends Primarily on subsistence Livestock Farming Activities"
                    },
                    {
                        "eligibility_column": "part_1_livestock/part_1_livestock_sub_section/part_1_access_animal_feed",
                        "eligibility_value": "no",
                        "criteria_description": "Households with No Access to Livestock Feed"
                    },
                    {
                        "eligibility_column": "part_1_livestock/part_1_livestock_basic_service/part_1_ngo_assistance_this_year",
                        "eligibility_value": "no",
                        "criteria_description": "HH Has Not Received Animal Feed Assistance This Year"
                    },
                    {
                        "eligibility_column": ["part_1_livestock/part_1_livestock_sub_section/part_1_cattle", "part_1_livestock/part_1_livestock_sub_section/part_1_buffalo", "part_1_livestock/part_1_livestock_sub_section/part_1_goat_sheep", "part_1_livestock/part_1_livestock_sub_section/part_1_donkey_mule_horse", "part_1_livestock/part_1_livestock_sub_section/part_1_camel"],
                        "eligibility_range": (1, 15),
                        "criteria_description": "Household Must Have 1-15 Animals"
                    },
                    {
                        "eligibility_column": ["fcs/cereals", "fcs/pulses", "fcs/milk", "fcs/meat", "fcs/veg", "fcs/fruit", "fcs/oil", "fcs/sugar"],
                        "eligibility_range": (0, 42),
                        "criteria_description": "Household Food Consumption Scores: Poor to Borderline"
                    }
                ]
            },
            "Vegetable_Home_Gardening": {
                "eligibility_criteria": [
                    {
                        "eligibility_column": "gen_info/sex",
                        "eligibility_value": "female",
                        "criteria_description": "Permanent Female Headed Household or Temporary Female Headed Household"
                    },
                    {
                        "eligibility_column": "part_3_hg/part_3_income/part_3_cultivate_veg_jerib",
                        "eligibility_range": (0, 0.2),
                        "criteria_description": "Households Having Access to a Backyard up to 400 sq.mt. (0.2) of Land"
                    },
                    {
                        "eligibility_column": ["fcs/cereals", "fcs/pulses", "fcs/milk", "fcs/meat", "fcs/veg", "fcs/fruit", "fcs/oil", "fcs/sugar"],
                        "eligibility_range": (0, 42),
                        "criteria_description": "Household Food Consumption Scores: Poor to Borderline"
                    }    
                ]
            },
            "Cash_for_Work": {
                "eligibility_criteria": [
                    {
                        "eligibility_column": "gen_info/hh_head_age",
                        "eligibility_range": (18, 64),
                        "criteria_description": "Household have labour force within the HH, between 18 and 64 years old"
                    },
                    {
                        "eligibility_column": "part_5_cfw/part_5_agriculture/part_5_irrigated_land",
                        "eligibility_range": (0, 0.5),
                        "criteria_description": "Household Having No Agricultural Productive Land, or 0.5 Jerib of Irrigated Land"
                    },
                    {
                        "eligibility_column": "part_5_cfw/part_5_agriculture/part_5_rainfed_land",
                        "eligibility_range": (0, 5),
                        "criteria_description": "Household Having No Agricultural Productive Land, or 1 to 5 Jerib of Rain-fed Land"
                    },
                    {
                        "eligibility_column": ["part_5_cfw/part_5_livestock/part_5_cattle", "part_5_cfw/part_5_livestock/part_5_buffalo", "part_5_cfw/part_5_livestock/part_5_goat_sheep", "part_5_cfw/part_5_livestock/part_5_donkey_mule_horse", "part_5_cfw/part_5_livestock/part_5_camel"],
                        "eligibility_range": (0, 5),
                        "criteria_description": "Household having no livestock or 5 Animals"
                    },
                    {
                        "eligibility_column": ["fcs/cereals", "fcs/pulses", "fcs/milk", "fcs/meat", "fcs/veg", "fcs/fruit", "fcs/oil", "fcs/sugar"],
                        "eligibility_range": (0, 28),
                        "criteria_description": "Household Food Consumption Scores: Poor"
                    }    
                ]
            }
        }

        # Dropdown selection for intervention type with an initially empty option
        intervention_type = st.selectbox("Select Intervention Type:", options=[""] + list(parameters.keys()))

        # Display eligibility criteria based on the selected intervention type, only if a valid type is selected
        if intervention_type:
            st.markdown(
                f"<h4 style='background-color: #E0F7FA; padding: 10px; border-radius: 5px;'>{intervention_type} Intervention Eligibility Criteria</h2>",
                unsafe_allow_html=True
            )

            # List to hold average results
            average_results = []

            for criterion in parameters[intervention_type]["eligibility_criteria"]:
                results, non_eligible_households, null_households = show_eligibility_table(filtered_data, criterion)

                # Create two columns to show the table and visualization side by side
                col1, col2 = st.columns(2)

                # Show the table in the first column
                with col1:
                    st.dataframe(results.style.format({"Percentage Eligible": "{:.2f}"}))

                # Show the visualization in the second column
                with col2:
                    visualize_eligibility(results)

                # Display non-eligible households if they exist
                if not non_eligible_households.empty:
                    with st.expander("Non-eligible Households"):
                        st.dataframe(non_eligible_households)

                # Display null households if they exist
                if not null_households.empty:
                    with st.expander("Eligibility Criteria Null Values"):
                        st.dataframe(null_households)

                # Calculate the average percentage of eligible households across all provinces
                avg_percentage_eligible = results['Eligible (%)'].mean()

                # Add to the list of average results
                average_results.append({
                    'Criteria': criterion['criteria_description'],
                    'Average Eligible (%)': avg_percentage_eligible
                })

            # Final section: Show average percentages across all criteria
            if average_results:
                st.markdown(
                        "<h4 style='background-color: #FFEB3B; margin-bottom: 10px; padding: 10px; border-radius: 5px;'>Average Percentage for Each Eligibility Criteria</h4>",
                        unsafe_allow_html=True
                    )
                # Convert the list of averages to a DataFrame
                avg_df = pd.DataFrame(average_results)

                # Create two columns for the table and chart
                col1, col2 = st.columns(2)
                # Display the table in the first column
                with col1:
                    st.dataframe(avg_df.style.format({"Average Eligible (%)": "{:.2f}"}))

                # Show the horizontal bar chart in the second column
                with col2:
                    # Create a horizontal bar chart with random colors
                    chart_data = avg_df.set_index('Criteria')['Average Eligible (%)']
                    st.bar_chart(chart_data, color="#408BBE")
        else:
            st.markdown(
                f"<h4 style='background-color: #E0F7FA; padding: 10px; border-radius: 5px;'>No Intervention type Is Selected</h2>",
                unsafe_allow_html=True
            )
                
        # Call the function
        #fig = visualize_eligibility(filtered_data, parameters)
        #if fig:
         #   st.pyplot(fig)
        
def sideBar():
    with st.sidebar:
        st.image("data/logo.png", use_column_width=True)
        selected = option_menu(
            menu_title="Projects",
            options=["Home", "LTA - Baseline 1", "LTA - Baseline 2", "LTA - Baseline 3", "LTA - PDM", "LTA - IP-PDM", "LTA - PHM"],
            icons=["house", "eye", "eye", "eye", "eye", "eye", "book"],
            menu_icon="cast",
            default_index=0
        )
        st.session_state.selected_option = selected

        if selected in ["LTA - Baseline 1", "LTA - Baseline 2", "LTA - Baseline 3", "LTA - PDM", "LTA - IP-PDM", "LTA - PHM"]:
            st.subheader("Submission Date")
            submitted_after = st.date_input(
                "Select date from which to load data:",
                value=datetime.today(),
                min_value=datetime(2020, 1, 1),
                max_value=datetime.today()
            )
            st.session_state.submitted_after = submitted_after
        else:
            st.session_state.submitted_after = None

        if selected == "LTA - Baseline 1":
            st.info("Baseline type 1 - TPM_Beneficiary_Verif_Final - AACS")
        elif selected == "LTA - Baseline 2":
            st.info("Baseline type 2 - 1. TPM_LTA_Beneficiary_Verif..")
        elif selected == "LTA - Baseline 3":
            st.info("Baseline type 3 - TPM_AACS_BBV_New Interventions_Questionnaire")
        elif selected == "LTA - PDM":
            st.info("Post-distribution Monitoring")
        elif selected == "LTA - PHM":
            st.info("Post-harvest Monitoring")
        elif selected == "LTA - IP-PDM":
            st.info("IP Level Post-distribution Monitoring")

    return selected, st.session_state.submitted_after

selected_option, submitted_after = sideBar()

tab1, tab2, tab3 = st.tabs(["Tracker", "Data Quality Review", "Baseline Eligibility Analysis"])

with tab1:
    if selected_option == "Home":
        home()
    elif selected_option in ["LTA - Baseline 1", "LTA - Baseline 2", "LTA - Baseline 3", "LTA - PDM", "LTA - IP-PDM", "LTA - PHM"]:
        load_data(selected_option, submitted_after)  # Load the dataset
        tracker()  # Now display the loaded data

with tab2:
    if selected_option == "Home":
        home()
    elif selected_option in ["LTA - Baseline 1", "LTA - Baseline 2", "LTA - Baseline 3", "LTA - PDM", "LTA - IP-PDM", "LTA - PHM"]:
        load_data(selected_option, submitted_after)  # Load the dataset
    data_quality_review()

with tab3:
    if selected_option == "Home":
        home()
    elif selected_option in ["LTA - Baseline 1", "LTA - Baseline 2", "LTA - Baseline 3", "LTA - PDM", "LTA - PHM"]:
        load_data(selected_option, submitted_after)  # Load the dataset
        # Run baseline eligibility analysis only for Baseline 1, 2, or 3
        if selected_option in ["LTA - Baseline 1", "LTA - Baseline 2", "LTA - Baseline 3"]:
            baseline_eligibility_analysis()