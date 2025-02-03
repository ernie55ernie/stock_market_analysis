import os
import csv
from datetime import datetime
from chip.models import BrokerData

def update_broker_data(csv_file_path):
    """
    Update the BrokerData table from a CSV file.
    :param csv_file_path: Path to the CSV file
    """
    with open(csv_file_path, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Convert the date string to a Python datetime object
            date = datetime.strptime(row['date'], '%Y/%m/%d').date()
            
            # Check if the record exists (based on the composite key)
            obj, created = BrokerData.objects.update_or_create(
                broker=row['broker'],
                broker_branch=row['branch'],
                code=row['code'],
                date=date,
                defaults={
                    'buy': int(row['buy']),
                    'sell': int(row['sell']),
                    'total': int(row['total']),
                    'net': int(row['net']),
                },
            )
    if created:
        print(f"Created new records.")

def update_broker_data_from_directory(directory, exclude_codes=None):
    """
    Update the BrokerData table from all CSV files in a directory, excluding specified stock codes.
    :param directory: Path to the directory containing CSV files
    :param exclude_codes: List of stock codes to exclude (default: [])
    """
    if exclude_codes is None:
        exclude_codes = []
    
    for filename in os.listdir(directory):
        if filename.startswith("broker_branch_data_") and filename.endswith(".csv"):
            csv_file_path = os.path.join(directory, filename)
            
            with open(csv_file_path, encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Skip excluded stock codes
                    if row['code'] in exclude_codes:
                        continue
                    
                    # Convert the date string to a Python datetime object
                    date = datetime.strptime(row['date'], '%Y/%m/%d').date()
                    
                    # Check if the record exists (based on the composite key)
                    obj, created = BrokerData.objects.update_or_create(
                        broker=row['broker'],
                        broker_branch=row['branch'],
                        code=row['code'],
                        date=date,
                        defaults={
                            'buy': int(row['buy']),
                            'sell': int(row['sell']),
                            'total': int(row['total']),
                            'net': int(row['net']),
                        },
                    )
            print(f"Processed {filename}")
    print("Data update completed.")