import csv

def load_bankroll(file_path):
    bankrolls = {}
    try:
        with open(file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row['name']
                try:
                    bankroll = float(row['bankroll'])
                except ValueError:
                    bankroll = 0.0  # or handle the error appropriately
                bankrolls[name] = bankroll
    except FileNotFoundError:
        # Handle the case where the file does not exist
        pass
    return bankrolls
