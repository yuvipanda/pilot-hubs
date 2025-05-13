from pathlib import Path
import sys
import json
from ruamel.yaml import YAML

yaml = YAML(typ="rt")
yaml.width = 4096

tf_outputs = json.load(sys.stdin)

ebs_map = tf_outputs["ebs_volume_id_map"]["value"]

ebs_vols = {k.split("-")[-1]: v for k, v in ebs_map.items()}

cluster_name = sys.argv[1]

config_dir = Path(__file__).parent.parent / "config/clusters"

for hub, vol_id in ebs_vols.items():
    hub_config = config_dir / cluster_name / f"{hub}.values.yaml"
    with open(hub_config, "r+") as f:
        config = yaml.load(f)
        if "basehub" in config:
            basehub_config = config["basehub"]
        else:
            basehub_config = config
        if "staging" not in hub:
            basehub_config["jupyterhub-home-nfs"] = {
                "quotaEnforcer": {
                    "resources": {
                        "requests": {"cpu": 0.02, "memory": "20M"},
                        "limits": {"cpu": 0.04, "memory": "30M"},
                    }
                },
                "nfsServer": {
                    "resources": {
                        "requests": {"cpu": 0.2, "memory": "2G"},
                        "limits": {"cpu": 0.4, "memory": "6G"},
                    }
                },
                "prometheusExporter": {
                    "resources": {
                        "requests": {"cpu": 0.02, "memory": "15M"},
                        "limits": {"cpu": 0.04, "memory": "20M"},
                    }
                },
            }

        basehub_config.setdefault("jupyterhub-home-nfs", {})["eks"] = {"volumeId": vol_id}
        f.seek(0)
        f.truncate(0)
        yaml.dump(config, f)

common_config = config_dir / cluster_name / "common.values.yaml"

with open(common_config, "r+") as f:
    config = yaml.load(f)
    if "basehub" in config:
        basehub_config = config["basehub"]
    else:
        basehub_config = config
    basehub_config["jupyterhub-home-nfs"] = {"enabled": True, "eks": {"enabled": True}}
    f.seek(0)
    f.truncate(0)
    yaml.dump(config, f)
