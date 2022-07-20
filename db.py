import json
import os

import psycopg2
import psycopg2.errors

from credential import DATABASE_URL


def last_month():
    with open("month.json", mode='r') as f:
        data = json.load(f)

    return data[-1]


class Databases:
    def __init__(self):
        self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        self.cursor = self.conn.cursor()
        self._create_table()

        self.column = self._get_columns()

    def _create_table(self):
        self.cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {last_month()}(
            date VARCHAR(10),
            heure VARCHAR(10),
            revenus VARCHAR(10),
            depenses VARCHAR(10),
            description VARCHAR(255) NOT NULL,
            balance INT)
        """
        )

    def _get_columns(self):
        self.cursor.execute(f"Select * FROM {last_month()} LIMIT 0")
        colnames = [desc[0] for desc in self.cursor.description]
        return colnames

    def save_data(self, date, hour, income=None, expense=None, description="", balance=0):
        self.cursor.execute(
            f'INSERT INTO {last_month()} (date, heure, revenus, depenses, description, balance) VALUES (%s, %s, %s, %s, %s, %s)',
            (date, hour, income, expense, description, balance))

        self.commit_data()

    def update_value(self, row: str, new_value: str, row_index: str, row_value):
        if row.lower() == "description":
            new_value = f"{new_value.upper()} --> UPDATED"

        elif row_index.lower() == "description":
            row_value = row_value.upper()

        self.cursor.execute(f"UPDATE {last_month()} SET {row.lower()} = '{new_value}' WHERE {row_index.lower()} = '{row_value}'")
        self.commit_data()

    def delete_value(self, row: str, value: str):
        if row.lower() == "description":
            self.cursor.execute(f"DELETE FROM {last_month()} WHERE {row.lower()} = '{value}'")
            self.commit_data()
        else:
            raise ValueError("Name of column not match")

    def last_value(self, row: str):
        self.cursor.execute(f"SELECT {row.lower()} FROM {last_month()}")
        last = [i[0] for i in self.cursor.fetchall()]
        return last[-1]

    def get_income_expense(self, row: str):
        self.cursor.execute(f"SELECT {row.lower()} FROM {last_month()}")
        records = self.cursor.fetchall()
        total = sum([int(i[0]) for i in records if i[0] is not None])

        return total

    def commit_data(self):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()


if __name__ == "__main__":
    d = Databases()

    # d.update_value("description", "Yango taxi", "heure", "15:42:59")
    # print(d.column)
