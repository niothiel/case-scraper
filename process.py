"""Post-process a case csv file with more specific information."""
import csv
import re
import sys


INPUT = sys.argv[1]


def parse_dollars(col):
    if m := re.search(r'\d+.\d+', col):
        return m.group(0)

    return col


with open(INPUT) as fin:
    reader = csv.DictReader(fin)
    entry = next(iter(reader))
    columns = list(entry.keys()) + ['actual_speed', 'speed_limit']


with open(INPUT) as fin:
    with open('cases-parsed.csv', 'w') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=columns)
        writer.writeheader()

        for entry in reader:
            match = re.search(r'(\d\d)/(\d\d)', entry['charge'])
            actual_speed = ''
            speed_limit = ''
            if match:
                actual_speed = int(match.group(1))
                speed_limit = int(match.group(2))

                entry['actual_speed'] = actual_speed
                entry['speed_limit'] = speed_limit

            entry['fine'] = parse_dollars(entry['fine'])
            entry['costs'] = parse_dollars(entry['costs'])
            writer.writerow(entry)