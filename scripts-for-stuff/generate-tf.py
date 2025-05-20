import sys
from textwrap import dedent
from math import ceil, log

df_output_file = sys.argv[1]

hubs = {}
with open(df_output_file) as f:
    for line in f:
        parts = line.split()
        hubs[parts[1][2:]] = int(parts[0])

print(hubs)

for hub, size_in_kb in hubs.items():
    # Size in gb, and round up everything under 1GB to 1GB
    size_in_gb = ceil(size_in_kb / 1024 / 1024)

    # round to nearest power of 2 'up'
    dest_size = pow(2, ceil(log(size_in_gb)/log(2)))

    # Round to nearest 'round'ish number
    print(dedent(f"""
    "{hub}" = {{
        size        = {dest_size}
        type        = "gp3"
        name_suffix = "{hub}"
        tags        = {{ "2i2c:hub-name": "{hub}" }}
    }},"""), end="")