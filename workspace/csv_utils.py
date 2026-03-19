import csv
import os

class CsvUtils:
    @staticmethod
    def load_bankroll(name: str) -> float:
        """
        Loads a player's bankroll from a CSV file.

        Args:
            name (str): The player's name.

        Returns:
            float: The loaded bankroll amount.
        """
        filename = f"{name}_bankroll.csv"
        if os.path.exists(filename):
            with open(filename, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    return float(row['amount'])
        else:
            print(f"File {filename} not found.")
            return 0

    @staticmethod
    def save_bankroll(name: str, amount: float) -> None:
        """
        Saves a player's bankroll to a CSV file.

        Args:
            name (str): The player's name.
            amount (float): The bankroll amount to be saved.
        """
        filename = f"{name}_bankroll.csv"
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['amount']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({'amount': str(amount)})
