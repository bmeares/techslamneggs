#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
Fetch economic data from FRED.
"""

from typing import Any, Dict, Optional, List
import meerschaum as mrsm
from datetime import datetime

API_BASE_URL: str = 'https://fred.stlouisfed.org/graph/api/series/'
CSV_BASE_URL: str = 'https://fred.stlouisfed.org/graph/fredgraph.csv'

required = ['pandas']

def register(pipe: mrsm.Pipe) -> Dict[str, Any]:
    """
    Return the expected, default parameters.
    This is optional but recommended (helps with documentation).

    Parameters
    ----------
    pipe: mrsm.Pipe
        The pipe to be registered.

    Returns
    -------
    The default value of `pipe.parameters`.
    """
    return {
        'fred': {
            'series_id': None,
        },
        'columns': {
            'datetime': 'DATE',
        },
    }


def fetch(
        pipe: mrsm.Pipe,
        begin: Optional[datetime] = None,
        end: Optional[datetime] = None,
        **kwargs: Any
    ) -> 'pd.DataFrame':
    """
    Fetch the newest data from FRED.

    Parameters
    ----------
    pipe: mrsm.Pipe
        The pipe being synced.

    begin: Optional[datetime], default None
        If specified, fetch data from this point onward.
        Otherwise use `pipe.get_sync_time()`.

    end: Optional[datetime], default None
        If specified, fetch data older than this point.

    Returns
    -------
    A DataFrame to be synced.
    """
    import pandas as pd
    series_id = pipe.parameters.get('fred', {}).get('series_id', None)
    if not series_id:
        raise Exception(f"No series ID was set for {pipe}.")

    url = f"{CSV_BASE_URL}?id={series_id}"
    df = pd.read_csv(url)
    if series_id in df.columns:
        df['PRICE'] = pd.to_numeric(df[series_id], errors='coerce')
        del df[series_id]

    return df
