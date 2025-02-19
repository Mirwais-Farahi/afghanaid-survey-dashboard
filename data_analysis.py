import pandas as pd

def filter_data(df, selected_columns):
    filters = {}
    if selected_columns:
        for column in selected_columns:
            unique_values = df[column].dropna().unique().tolist()
            filters[column] = unique_values
    return filters

def apply_filters(df, filters):
    for column, values in filters.items():
        df = df[df[column].isin(values)]
    return df

def calculate_statistics(df_selection, selected_columns):
    total_2_mean = total_2_median = total_3_min = total_3_max = total_4 = 0

    if selected_columns:
        # Convert the first selected column to numeric before calculating mean and median
        col_data = pd.to_numeric(df_selection[selected_columns[0]].str.strip(), errors='coerce')
        
        total_2_mean = float(col_data.mean())
        total_2_median = float(col_data.median())

        if len(selected_columns) > 1:
            # Convert the second selected column to numeric for min and max
            col_data_2 = pd.to_numeric(df_selection[selected_columns[1]].str.strip(), errors='coerce')
            total_3_min = float(col_data_2.min())
            total_3_max = float(col_data_2.max())

        if len(selected_columns) > 2:
            # Convert the third selected column to numeric for outlier calculation
            col_data_3 = pd.to_numeric(df_selection[selected_columns[2]].str.strip(), errors='coerce')
            q1 = col_data_3.quantile(0.25)
            q3 = col_data_3.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            total_4 = ((col_data_3 < lower_bound) | (col_data_3 > upper_bound)).sum()

    return total_2_mean, total_2_median, total_3_min, total_3_max, total_4

def identify_outliers(df, column):
    """
    Function to identify outliers in a given numeric column using the IQR method.
    Returns a DataFrame containing the outlier rows.
    """
    # Convert data to numeric, coercing errors to NaN
    numeric_data = pd.to_numeric(df[column].str.strip(), errors='coerce')

    # Calculate Q1 (25th percentile) and Q3 (75th percentile), ignoring NaN values
    Q1 = numeric_data.quantile(0.25)
    Q3 = numeric_data.quantile(0.75)
    IQR = Q3 - Q1

    # Define bounds for outliers
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # Identify outliers based on the index alignment
    outliers = df[(numeric_data < lower_bound) | (numeric_data > upper_bound)].copy()

    return outliers

def filter_short_surveys(df, start_column, end_column):
    """
    Filters surveys that took less than 20 minutes.

    Parameters:
    df (DataFrame): The DataFrame containing survey data.
    start_column (str): The name of the column with start times.
    end_column (str): The name of the column with end times.

    Returns:
    DataFrame: A filtered DataFrame.
    """

    # Ensure columns exist
    if start_column not in df.columns or end_column not in df.columns:
        raise ValueError(f"Columns '{start_column}' or '{end_column}' not found in DataFrame.")

    # Convert to datetime with proper timezone handling
    df[start_column] = pd.to_datetime(df[start_column], errors='coerce', utc=True)
    df[end_column] = pd.to_datetime(df[end_column], errors='coerce', utc=True)

    # Check if conversion was successful
    if df[start_column].isna().all():
        raise ValueError(f"Column '{start_column}' could not be converted to datetime. Check data for invalid formats.")
    if df[end_column].isna().all():
        raise ValueError(f"Column '{end_column}' could not be converted to datetime. Check data for invalid formats.")

    # Convert to local timezone (remove UTC awareness)
    df[start_column] = df[start_column].dt.tz_convert(None)
    df[end_column] = df[end_column].dt.tz_convert(None)

    # Calculate duration in minutes (use absolute value to correct negative durations)
    df['duration'] = abs((df[end_column] - df[start_column]).dt.total_seconds() / 60.0)

    # Filter surveys that took less than 20 minutes
    short_surveys = df[df['duration'] < 30]

    # Remove columns that contain only null values
    filtered_df = short_surveys.dropna(axis=1, how='all')

    return filtered_df

# Function to get unique responses for a selected question
def get_unique_responses(df, question):
    return df[question].unique()

# Function to filter responses
def filter_responses(df, first_question, second_question, first_response, second_response):
    return df[(df[first_question] == first_response) & (df[second_question] == second_response)].dropna(axis=1, how='all')
