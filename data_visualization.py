import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random
import matplotlib.pyplot as plt
import seaborn as sns
from data_analysis import identify_outliers

def apply_filters(df):
    filter_columns = st.multiselect("Select columns to filter", df.columns.tolist())
    filtered_df = df.copy()

    for col in filter_columns:
        unique_values = df[col].unique().tolist()
        filter_value = st.selectbox(f"Filter {col}", unique_values)
        filtered_df = filtered_df[filtered_df[col] == filter_value]

    return filtered_df

def group_by_visualize_and_download(df_selection):
    with st.expander("GROUP BY AND VISUALIZE"):
        group_by_columns = st.multiselect("Select Columns for Grouping:", df_selection.columns.tolist())

        if group_by_columns:
            grouped_data = df_selection.groupby(group_by_columns).size().reset_index(name='Count')
            total_count = grouped_data['Count'].sum()
            st.write(f"**Total Count:** {total_count}")

            num_bars = len(grouped_data)
            colors = [f'rgb({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)})' for _ in range(num_bars)]

            fig = px.bar(
                grouped_data,
                y=group_by_columns[0],
                x='Count',
                color=group_by_columns[1] if len(group_by_columns) > 1 else None,
                title=f'{group_by_columns}',
                orientation='h',
                color_discrete_sequence=colors
            )

            fig.update_layout(
                xaxis_title="Count",
                yaxis_title=group_by_columns[0],
                plot_bgcolor="rgba(0,0,0,0)"
            )

            st.plotly_chart(fig, use_container_width=True)

            excel_file = "grouped_data.xlsx"
            grouped_data.to_excel(excel_file, index=False)

            with open(excel_file, "rb") as f:
                st.download_button(
                    label="Download Grouped Data as Excel",
                    data=f,
                    file_name=excel_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

def display_group_by_table(df_selection):
    with st.expander("GROUP BY TABLE"):
        group_by_columns = st.multiselect("Select Columns for Table Grouping:", df_selection.columns.tolist())

        if group_by_columns:
            grouped_data_table = df_selection.groupby(group_by_columns).size().reset_index(name='Total')
            st.write(grouped_data_table)

            total_count = grouped_data_table['Total'].sum()
            st.write(f"**Total Count Across All Groups:** {total_count}")

def plot_boxplot(df, column):
    """
    Function to plot a box-plot for a selected numeric column with enhanced design and readability.
    """
    if column:
        plt.figure(figsize=(12, 6))  # Set the figure size
        sns.set(style="whitegrid")  # Set the style

        # Create the boxplot
        ax = sns.boxplot(x=df[column], color='skyblue', fliersize=5, linewidth=1.5)

        # Overlay a jittered scatter plot
        sns.stripplot(x=df[column], color='black', alpha=0.6, size=4, jitter=True)

        ax.set_title(f'Box-plot for {column}', fontsize=16, fontweight='bold')
        ax.set_xlabel(column, fontsize=14)
        ax.set_ylabel('Values', fontsize=14)

        # Add grid for better readability
        ax.grid(True, linestyle='--', alpha=0.7)

        # Customize ticks
        ax.tick_params(axis='both', which='major', labelsize=12)

        # Rotate x-axis labels if necessary
        plt.xticks(rotation=45)

        # Display the plot in Streamlit
        st.pyplot(plt)

        # Clear the plot to avoid overlapping plots on subsequent calls
        plt.clf()

        # Identify outliers
        outliers_df = identify_outliers(df, column)

        # Display the outliers in Streamlit
        if not outliers_df.empty:
            st.write(f"Detected Outliers in '{column}':")
            st.dataframe(outliers_df)  # Display the outliers DataFrame
        else:
            st.write(f"No outliers detected in '{column}'.")

    else:
        st.warning("Please select a numeric column for the box-plot.")

def plot_time_series(data):
    with st.expander("TIME SERIES VISUALIZATION"):
        # Ensure '_submission_time' is in datetime format
        data['_submission_time'] = pd.to_datetime(data['_submission_time'], errors='coerce')

        # Drop rows with invalid or missing datetime entries
        data = data.dropna(subset=['_submission_time'])

        # Set the datetime column as the index
        data.set_index('_submission_time', inplace=True)

        # Resample the data to get counts of submissions per day
        daily_counts = data.resample('D').size()

        # Plot the time series chart
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(daily_counts, marker='o', linestyle='-', color='blue')

        ax.set_title('Survey Submissions Over Time', fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=14)
        ax.set_ylabel('Number of Submissions', fontsize=14)

        # Add grid for better readability
        ax.grid(True, linestyle='--', alpha=0.7)

        # Display the plot in Streamlit
        st.pyplot(fig)


####################################################
def visualize_eligibility(filtered_data, parameters):
    # Extract eligibility column and range from parameters
    eligibility_column = parameters.get("eligibility_column")
    eligibility_range = parameters.get("eligibility_range", (2, 5))  # Default to (2, 5) if not provided
    criteria_description = parameters.get("criteria_description", "")

    if eligibility_column not in filtered_data.columns:
        print(f"Error: Column '{eligibility_column}' not found in the data.")
        return  # Exit if column is missing

    # Convert the specified eligibility column to numeric
    filtered_data[eligibility_column] = pd.to_numeric(
        filtered_data[eligibility_column].astype(str), errors='coerce'
    )

    # Determine eligibility based on the range
    min_eligible, max_eligible = eligibility_range
    filtered_data['eligibility'] = (
        (filtered_data[eligibility_column] >= min_eligible) &
        (filtered_data[eligibility_column] <= max_eligible)
    )

    # Count eligible and non-eligible households by district
    district_counts = filtered_data.groupby(['gen_info/district', 'eligibility']).size().unstack(fill_value=0)
    district_counts = district_counts.reset_index()
    district_counts.columns = ['gen_info/district', 'Non-Eligible', 'Eligible']

    # Set up the figure with subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Horizontal Bar Chart for Eligible and Non-Eligible Households by District
    district_counts_melted = district_counts.melt(id_vars='gen_info/district', 
                                                  value_vars=['Eligible', 'Non-Eligible'], 
                                                  var_name='Eligibility Status', 
                                                  value_name='Count')
    sns.barplot(data=district_counts_melted, x='Count', y='gen_info/district', hue='Eligibility Status', ax=axes[0])
    axes[0].set_title('Eligible and Non-Eligible Households by District')
    axes[0].set_xlabel('Number of Households')
    axes[0].set_ylabel('District')
    axes[0].legend(title='Eligibility Status')

    # Pie Chart for total household counts
    total_counts = filtered_data['eligibility'].value_counts()
    axes[1].pie(total_counts, labels=total_counts.index.map({True: 'Eligible', False: 'Not Eligible'}),
                autopct='%1.1f%%', startangle=90)
    axes[1].axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    axes[1].set_title('Total Households by Eligibility (Pie Chart)')

    # Adding eligibility criteria description below pie chart
    axes[1].text(0.5, -0.1, criteria_description, ha='center', va='center', fontsize=10, transform=axes[1].transAxes)

    # Histogram of irrigated land distribution
    sns.histplot(filtered_data[eligibility_column], bins=10, ax=axes[2], kde=True)
    axes[2].set_title('Distribution of Cultivable Irrigated Land')
    axes[2].set_xlabel('Cultivable Irrigated Land (Jeribs)')
    axes[2].set_ylabel('Frequency')

    plt.tight_layout()

    # Display the plot in Streamlit
    st.pyplot(fig)

# Method to safely convert values
def safe_convert(value):
    # Try to convert the value to numeric; if it can't be converted, it will return NaN
    converted_value = pd.to_numeric(value, errors='coerce')
    
    # If the conversion results in NaN, keep the original string
    if pd.isna(converted_value):
        return value
    else:
        return converted_value

def show_eligibility_table(data, parameters):
    # Unpack parameters
    eligibility_column = parameters['eligibility_column']
    eligibility_value = parameters.get('eligibility_value')
    eligibility_range = parameters.get('eligibility_range')
    criteria_description = parameters['criteria_description']

    # If eligibility_column is a list, sum the values after converting them to numeric
    if isinstance(eligibility_column, list):
        # Convert columns to numeric, handling cases where values are stored as strings
        data['eligibility_sum'] = data[eligibility_column].apply(pd.to_numeric, errors='coerce').sum(axis=1)
        column_to_check = 'eligibility_sum'
    else:
        # Convert a single column using the safe_convert method
        data[eligibility_column] = data[eligibility_column].apply(safe_convert)
        column_to_check = eligibility_column

    # Create a list to hold the results for each province and district
    results_list = []
    
    # Group by province and district
    grouped_data = data.groupby(['gen_info/province', 'gen_info/district'])
    
    # Initialize DataFrames for non-eligible households and null values
    non_eligible_households = pd.DataFrame()
    null_households = pd.DataFrame()

    # Calculate metrics for each group
    for (province, district), group in grouped_data:
        total_households = len(group)

        # Strip leading and trailing spaces from the eligibility column
        if isinstance(eligibility_column, list):
            for col in eligibility_column:
                if group[col].dtype == 'object':  # Check if column is of type object (string)
                    group[col] = group[col].str.strip()  # Strip spaces
        else:
            if group[column_to_check].dtype == 'object':
                group[column_to_check] = group[column_to_check].str.strip()

        # Determine null values
        null_group = group[group[column_to_check].isnull()]
        non_null_group = group[~group[column_to_check].isnull()]
        
        # Determine eligible and non-eligible households based on eligibility_value or eligibility_range
        if eligibility_value is not None:
            eligible_households = non_null_group[
                non_null_group[column_to_check].astype(str).str.lower() == eligibility_value.lower()
            ].shape[0]
            non_eligible_group = non_null_group[
                non_null_group[column_to_check].astype(str).str.lower() != eligibility_value.lower()
            ]
        elif eligibility_range is not None:
            eligible_households = non_null_group[
                (non_null_group[column_to_check] >= eligibility_range[0]) & 
                (non_null_group[column_to_check] <= eligibility_range[1])
            ].shape[0]
            non_eligible_group = non_null_group[
                (non_null_group[column_to_check] < eligibility_range[0]) | 
                (non_null_group[column_to_check] > eligibility_range[1])
            ]
        else:
            eligible_households = 0
            non_eligible_group = non_null_group  # If no eligibility criteria are specified, all are non-eligible

        # Calculate the percentages
        percentage_eligible = (eligible_households / total_households) * 100 if total_households > 0 else 0
        percentage_not_eligible = ((len(non_eligible_group) / total_households) * 100) if total_households > 0 else 0
        percentage_null = ((len(null_group) / total_households) * 100) if total_households > 0 else 0
        
        # Append results to the list
        results_list.append({
            'Province': province,
            'District': district,
            'Total HHs': total_households,
            'Eligible (%)': round(percentage_eligible, 2),
            'Not Eligible (%)': round(percentage_not_eligible, 2),
            'Null Values (%)': round(percentage_null, 2)
        })

        # Append non-eligible and null households for each group
        non_eligible_households = pd.concat([non_eligible_households, non_eligible_group], ignore_index=True)
        null_households = pd.concat([null_households, null_group], ignore_index=True)

    # Create a DataFrame from the results list
    results = pd.DataFrame(results_list)

    # Display the criteria description with styled background and text color
    st.markdown(
        f"<h4 style='background-color: #228B22; color: white; margin-top: 10px; margin-bottom: 10px; padding: 5px; border-radius: 5px;'>{criteria_description}</h4>",
        unsafe_allow_html=True
    )

    # Return the results, non-eligible households, and null households for further use
    return results, non_eligible_households, null_households

def visualize_eligibility(results):
    # Aggregate results by Province
    province_summary = results.groupby('Province').agg(
        Total_HHs=('Total HHs', 'sum'),
        Eligible_Percentage=('Eligible (%)', 'mean'),
        Not_Eligible_Percentage=('Not Eligible (%)', 'mean')
    ).reset_index()

    # Generate random colors for the bars
    eligible_color = np.random.rand(3,)
    not_eligible_color = np.random.rand(3,)

    # Visualize the eligibility data using Matplotlib
    fig, ax = plt.subplots(figsize=(10, 6))

    # Create horizontal bar charts for eligible and not eligible households
    ax.barh(province_summary['Province'], province_summary['Eligible_Percentage'], 
            color=eligible_color, label='Eligible (%)')
    ax.barh(province_summary['Province'], province_summary['Not_Eligible_Percentage'], 
            left=province_summary['Eligible_Percentage'], 
            color=not_eligible_color, alpha=0.5, label='Not Eligible (%)')

    ax.set_xlabel('Percentage of Households')
    ax.set_title('Household Eligibility Visualization by Province')
    ax.legend()

    st.pyplot(fig)  # Render the plot in Streamlit
