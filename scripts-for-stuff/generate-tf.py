import sys
from textwrap import dedent

df_output_file = sys.argv[1]

hubs = {}
with open(df_output_file) as f:
    for line in f:
        parts = line.split()
        hubs[parts[1][2:]] = int(parts[0])

print(hubs)

for hub, size_in_kb in hubs.items():
    size_in_gb = size_in_kb / 1024 / 1024

    # Round to nearest 'round'ish number
    print(dedent(f"""
    "{hub}" = {{
        size        = {size_in_gb}
        type        = "gp3"
        name_suffix = "{hub}"
        tags        = {{ "2i2c:hub-name": "{hub}" }}
    }}
    """))