import pandas as pd
from koboextractor import KoboExtractor
import streamlit as st

KOBO_TOKEN = "56c593b9e6f398524c3941c15b21c41ba49be72a"
kobo = KoboExtractor(KOBO_TOKEN, 'https://eu.kobotoolbox.org/api/v2')

@st.cache_data(ttl=600)
def load_dataset(option, submitted_after):
    asset_uids = {
        "AfghanAid CARL Baseline": "aPykjh6GrHZr4SEdkWCHE3",  # Household Survey Form
        "AfghanAid Observation Checklist": "aAGhH3cyoF59wFK3gHiRxg",  # Obs Checklist Survey Form
    }

    asset_uid = asset_uids.get(option)
    if asset_uid is None:
        return None

    # Load data from KoBoToolbox
    new_data = kobo.get_data(asset_uid, submitted_after=submitted_after)
    df = pd.DataFrame(new_data['results'])

    return df