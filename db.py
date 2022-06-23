import psycopg2
from crendential import DATABASE_URL


class Databases:
    def __init__(self):
        self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS juin(
            date VARCHAR(10),
            heure VARCHAR(10),
            revenus VARCHAR(10),
            depenses VARCHAR(10),
            description VARCHAR(255) NOT NULL,
            balance INT)
        """
        )
        

    def save_data(self, date, hour, income=None, expense=None, description="", balance=0):
        self.cursor.execute('INSERT INTO juin (date, heure, revenus, depenses, description, balance) VALUES (%s, %s, %s, %s, %s, %s)', (date, hour, income, expense, description, balance))

        self.commit_data()

    # def update_value(self):
    #     self.cursor.execute("UPDATE juin SET {row} = () WHERE {row} = ()")

    #     self.commit_data()

    def last_value(self, row: str):
        self.cursor.execute(f"SELECT {row.lower()} from juin")
        last = [i[0] for i in self.cursor.fetchall()]
        return last[-1]


    def get_income_expense(self, row: str):
        self.cursor.execute(f"SELECT {row.lower()} from juin")
        records = self.cursor.fetchall()
        total = sum([int(i[0]) for i in records if i[0] != None])
        
        return total

    def commit_data(self):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()


if __name__ == "__main__":
    d = Databases() 

    print(d.last_value("revenus"))
    print(d.last_value("depenses"))
    print(d.last_value("description"))
    print(d.last_value("balance"))