import json

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
        self.cursor.execute(f'INSERT INTO {last_month()} (date, heure, revenus, depenses, description, balance) VALUES (%s, %s, %s, %s, %s, %s)', (date, hour, income, expense, description, balance))

        self.commit_data()

    def update_balance(self, row: str, new_value: str, row_index: str, row_value: str):
        last_value = self.last_value('second_to_last')

        if row.lower() == "revenus":
            balance = int(new_value) + last_value
        elif row.lower() == "depenses":
            balance = last_value - int(new_value)
        
        self.cursor.execute(f"UPDATE {last_month()} SET balance = '{balance}' WHERE {row_index.lower()} = '{row_value}'")
        self.commit_data()
    
    def update_value(self, row: str, new_value: str, row_index: str, row_value):
        if row.lower() == "description":
            new_value = f"{new_value.upper()} --> UPDATED"

        elif row_index.lower() == "description":
            row_value = row_value.upper()

        # Update and commit selected row
        self.cursor.execute(f"UPDATE {last_month()} SET {row.lower()} = '{new_value}' WHERE {row_index.lower()} = '{row_value}'")
        # Update and commit balance
        self.update_balance(row, new_value, row_index, row_value)

    def delete_value(self, row: str, value: str):
        if row.lower() == "description" or "heure":
            # Une petite erreur que je dois corrigé ici.
            self.cursor.execute(f"DELETE FROM {last_month()} WHERE {row.lower()} = '{value}'")
            self.commit_data()
        else:
            raise ValueError("Name of column not match")

    def last_value(self, row: str):
        self.cursor.execute(f"SELECT balance FROM {last_month()}")
        last = [i[0] for i in self.cursor.fetchall()]
        if row == "balance":
            # return last value
            return last[-1]
        else:
            # Get second to last value
            return last[-2]

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

    print(d.last_value("balance"))
    print(d.last_value("last_second_value"))
