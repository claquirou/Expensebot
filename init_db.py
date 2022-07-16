import json
import os

from db import Databases


def _write_data():
    if not os.path.exists("month.json"):
        with open("month.json", mode='w') as f:
            json.dump([], f, indent=4)

    return


def add_month(month: str):
    _write_data()
    with open("month.json", mode='r') as f:
        data = json.load(f)

    data.append(month)
    with open("month.json", mode='w') as f:
        json.dump(data, f, indent=4)

    d = Databases()
    d.save_data(date=0, hour=0, income=0, expense=0, description="0", balance=0)
