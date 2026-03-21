python3.8+ required to run this file properly due to type hinting usage.
import csv
from dataclasses import dataclass
class Player:
    def __init__(self, name, bankroll=1000):
        self.name = name
        self.bankroll = bankroll
        self.balance = 0.0

    def add_balance(self, amount):
        if amount < 0:
            print("Invalid balance update: cannot deposit negative value")
        else:
            self.balance += amount
            self.save_to_csv()

    def remove_balance(self, amount):
        if amount > self.balance or amount > self.bankroll:
            print("Insufficient funds for this operation.")
        else:
            self.balance -= amount
            self.save_to_csv()

    @classmethod
    def load_from_csv(cls, filename='players.csv'):
        with open(filename, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row['name']
                bankroll = int(row['bankroll'])
                balance = float(row['balance'])
                yield cls(name=name, bankroll=bankroll)

    def save_to_csv(self):
        with open('players.csv', 'a') as file:
            writer = csv.writer(file)
            if not any(row[0] == self.name for row in reader(file)):
                writer.writerow([self.name, self.bankroll, str(self.balance)]).
