#!/usr/bin/env python3
from datetime import datetime, timedelta
from pathlib import Path
from kubespawner import slugs
import json
import subprocess
import sys
from ruamel.yaml import YAML
from deployer.infra_components.cluster import Cluster
from deployer.utils.file_acquisition import get_all_cluster_yaml_files

yaml = YAML(typ="safe", pure=True)

# hours_prior = int(sys.argv[1])
# cluster_name = sys.argv[2]
# hub_name = sys.argv[3]

def get_hub_pod_name(namespace: str):
    cmd = [
        "kubectl",
        "--namespace", namespace,
        "get", "pod",
        "-o", "name",
        "-l", "component=hub"
    ]
    return subprocess.check_output(cmd).decode().strip().split("/")[-1]


def exec_in_pod(namespace: str, pod_name: str, container_name: str, command: list[str]) -> str:
    cmd = [
        "kubectl",
        "--namespace", namespace,
        "exec", pod_name,
        "-c", container_name,
        "--",
    ] + command
    return subprocess.check_output(cmd).decode().strip()

def get_modified_user_dirs(cluster_name, hub_name, hours_prior: int):

    time_cutoff = datetime.utcnow() - timedelta(hours=hours_prior)
    query = f"""
        SELECT name, last_activity
        FROM users
        WHERE name != 'deployment-service-check'
            AND last_activity >= '{time_cutoff.isoformat()}'
    """
    sqlite_command = ["sqlite3", "jupyterhub.sqlite", "-json", query]

    users_to_sync = []
    cluster = Cluster.from_name(cluster_name)

    with cluster.auth():

        hub = next((hub for hub in cluster.hubs if hub.spec["name"] == hub_name), None)
        if hub is None:
            print(f"No hub named {hub_name} in {cluster_name}")
            sys.exit(1)
        hub_pod = get_hub_pod_name(hub.spec['name'])
        info_text = exec_in_pod(hub.spec["name"], hub_pod, "hub", sqlite_command)
        print(cluster.spec['name'], hub.spec['name'], info_text)
        if not info_text:
            print("No users found in given time frame")
            return []
            sys.exit(0)
        else:
            info = json.loads(info_text)
            for i in info:
                users_to_sync.append(i["name"])
    dirs_to_sync = [slugs.escape_slug(u) for u in users_to_sync]
    return dirs_to_sync