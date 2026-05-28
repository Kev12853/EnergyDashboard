import csv
import re

INPUT = "scan.csv"

temp = []

with open(
    INPUT,
    "r",
    newline="",
    encoding="utf-8",
) as f:

    reader = csv.reader(f)

    for row in reader:

        if len(row) >= 4:

            row[3] = re.sub(
                r"^\[(.*)\]$",
                r"\1",
                row[3],
            )

        temp.append(
            row
        )

with open(
    INPUT,
    "w",
    newline="",
    encoding="utf-8",
) as f:

    writer = csv.writer(
        f
    )

    writer.writerows(
        temp
    )

print(
    "Done"
)