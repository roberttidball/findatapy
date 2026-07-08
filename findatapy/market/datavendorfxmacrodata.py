__author__ = "saeedamen"  # Saeed Amen

#
# Copyright 2016 Cuemacro
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on a "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
#

import requests

import pandas as pd

from findatapy.market.datavendor import DataVendor
from findatapy.util import DataConstants, LoggerManager


class DataVendorFXMacroData(DataVendor):
    """Reads daily FX spot rates from FXMacroData into findatapy."""

    def __init__(self):
        super(DataVendorFXMacroData, self).__init__()

    def load_ticker(self, md_request):
        logger = LoggerManager().getLogger(__name__)

        if md_request.freq != "daily":
            logger.warning("FXMacroData currently supports daily FX spot rates")
            return None

        tickers = md_request.vendor_tickers or md_request.tickers
        fields = md_request.fields or ["close"]

        if tickers is None:
            logger.warning("No FXMacroData tickers specified")
            return None

        data_frames = []

        for library_ticker, vendor_ticker in zip(md_request.tickers, tickers):
            frame = self._download_fx_pair(md_request, vendor_ticker, fields)

            if frame is None or frame.empty:
                continue

            frame.columns = [
                f"{library_ticker}.{field}" for field in frame.columns
            ]
            data_frames.append(frame)

        if len(data_frames) == 0:
            return None

        data_frame = pd.concat(data_frames, axis=1).sort_index()
        data_frame.index.name = "Date"

        logger.info(
            f"Completed request from FXMacroData for {list(data_frame.columns)}")

        return data_frame

    def _download_fx_pair(self, md_request, ticker, fields):
        base, quote = self._split_pair(ticker)
        constants = DataConstants()
        url = (
            f"{constants.fxmacrodata_base_url}/forex/"
            f"{base.lower()}/{quote.lower()}"
        )
        params = {
            "start_date": self._format_date(md_request.start_date),
            "end_date": self._format_date(md_request.finish_date),
        }

        if md_request.fxmacrodata_api_key:
            params["api_key"] = md_request.fxmacrodata_api_key

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        rows = response.json().get("data", [])

        if len(rows) == 0:
            return None

        data_frame = pd.DataFrame(rows)
        data_frame["Date"] = pd.to_datetime(data_frame["date"])
        data_frame = data_frame.set_index("Date").sort_index()

        field_map = {}

        for field in fields:
            field_map[field] = (
                data_frame["val"]
                if field in ["open", "high", "low", "close"]
                else data_frame.get(field)
            )

        return pd.DataFrame(field_map, index=data_frame.index)

    @staticmethod
    def _split_pair(ticker):
        clean_ticker = ticker.replace("/", "").replace("-", "").upper()

        if len(clean_ticker) != 6:
            raise ValueError(
                "FXMacroData tickers should be six-letter FX pairs "
                "such as EURUSD"
            )

        return clean_ticker[:3], clean_ticker[3:]

    @staticmethod
    def _format_date(value):
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d")

        return str(value)
