import os

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth


def call_freshservice_api_to_df(endpoint: str) -> pd.DataFrame:
    """
    Call a Freshservice API endpoint and return the response as a DataFrame.

    Parameters
    ----------
    endpoint : str
        The Freshservice v2 API endpoint (e.g., '/departments').

    Returns
    -------
    pd.DataFrame
        DataFrame containing the API response.
    """
    api_key = os.getenv("FRESHSERVICE_API_KEY")
    domain = os.getenv("FRESHSERVICE_DOMAIN")
    if not api_key or not domain:
        raise ValueError(
            "FRESHSERVICE_API_KEY and FRESHSERVICE_DOMAIN must be set in environment."
        )

    url = f"https://{domain}/api/v2{endpoint}"
    print(f"[DEBUG] Requesting Freshservice API at: {url}")

    headers = {"Content-Type": "application/json"}
    auth = HTTPBasicAuth(api_key, "X")

    response = requests.get(url, headers=headers, auth=auth)
    print(f"[DEBUG] Response status code: {response.status_code}")
    response.raise_for_status()

    data = response.json()
    print(f"[DEBUG] Number of items returned: {len(data)}")

    return pd.DataFrame(data)
