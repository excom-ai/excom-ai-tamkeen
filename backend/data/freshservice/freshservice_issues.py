import os

import pandas as pd

FRESHSERVICE_TICKETS_CACHE = "fresh_service_tickets.parquet"


def get_freshservice_tickets(force_refresh: bool = False) -> pd.DataFrame | None:
    if not force_refresh and os.path.exists(FRESHSERVICE_TICKETS_CACHE):
        return pd.read_parquet(FRESHSERVICE_TICKETS_CACHE)


if __name__ == "__main__":
    # Example usage
    tickets_df = get_freshservice_tickets()
    if tickets_df is not None:
        print(tickets_df.head())
    else:
        print("No tickets found or error occurred.")
        