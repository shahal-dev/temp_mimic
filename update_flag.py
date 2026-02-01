import sys
import json
import helpers

config = helpers.load_config()

if len(sys.argv) != 2:
    print("Usage: python3 update_flag.py <flag>")
    sys.exit(1)

flag = sys.argv[1]
if flag not in config['flags']:
    print(f"Flag {flag} not found in config.json")
    sys.exit(1)

config['flags'][flag] = True
with open(helpers.CONFIG_PATH, 'w') as f:
    json.dump(config, f, indent=4)

print(f"Flag {flag} updated successfully")