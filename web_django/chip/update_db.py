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