from pathlib import Path
import subprocess
import sys
import json
from ruamel.yaml import YAML

yaml = YAML(typ="rt")
yaml.width = 4096

cluster_name = sys.argv[1]
hub_name = sys.argv[2]

config_dir = Path(__file__).parent.parent / "config/clusters"

# Let's make sure no active users
active_users = len([l for l in subprocess.check_output([
    "kubectl", "--namespace", hub_name,
    "get", "pod", "-l", "component=singleuser-server",
    "-o", "name"
]).decode().strip().split("\n") if l.startswith("pod/")])

if active_users != 0:
    print(f"{active_users} users are currently on, kick them out or wait")
    sys.exit(1)

pv_obj = json.loads(subprocess.check_output([
    "kubectl", "get", "pv", f"{hub_name}-home-nfs", "-o", "json"
]).decode())

if pv_obj["spec"]["persistentVolumeReclaimPolicy"] != "Retain":
    print(f"PV {hub_name}-home-nfs doesn't have reclaimpolicy set to retain. Fix that and try again")
    sys.exit(1)

# Setup config
nfs_ip = subprocess.check_output([
    "kubectl", "--namespace", hub_name,
    "get", "svc", f"{hub_name}-nfs-service",
    "-o=jsonpath={.spec.clusterIP}"
]).decode().strip()


hub_config = config_dir / cluster_name / f"{hub_name}.values.yaml"
with open(hub_config, "r+") as f:
    config = yaml.load(f)
    if "basehub" in config:
        basehub_config = config["basehub"]
    else:
        basehub_config = config

    basehub_config.setdefault("nfs", {})["pv"] = {"serverIP": nfs_ip}
    f.seek(0)
    f.truncate(0)
    yaml.dump(config, f)

# Bring the hub down
subprocess.check_call([
    "kubectl", "--namespace", hub_name,
    "delete", "svc", "proxy-public"
])

# Kill the PVC
subprocess.check_call([
    "kubectl", "delete", "pv", f"{hub_name}-home-nfs", "--wait=false"
])

subprocess.check_call([
    "kubectl", "--namespace", hub_name,
    "delete", "pvc", f"home-nfs", "--wait=false"
])

subprocess.check_call([
    "kubectl", "--namespace", hub_name,
    "delete", "pod", "-l", "component=shared-dirsize-metrics"
])