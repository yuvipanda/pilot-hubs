import time
import sys
import subprocess
import shlex
from active import get_modified_user_dirs

cluster_name = sys.argv[1]
hub_name = sys.argv[2]
hours_prior = int(sys.argv[3])

# If 0 is specified, copy everything
# If not, copy only users who were active in last X minutes
full_copy = hours_prior == 0

nfs_ip = subprocess.check_output([
    "kubectl", "--namespace", hub_name,
    "get", "svc", f"{hub_name}-nfs-service",
    "-o=jsonpath={.spec.clusterIP}"
]).decode().strip()

print(nfs_ip)

shell_pod_name = f"{cluster_name}-root-home-shell"
def shell_pod_exists():
    proc = subprocess.run([
        "kubectl", "--namespace", hub_name,
        "wait", "--for=condition=Ready",
        "pod", shell_pod_name
    ])
    return proc.returncode == 0

if not shell_pod_exists():
    start_pod = subprocess.Popen([
        "deployer",
        "exec",
        "root-homes",
        cluster_name,
        hub_name,
        f"--additional-nfs-server={nfs_ip}",
        "--additional-nfs-base-path=/",
        "--additional-nfs-mount-path=dest-fs",
        "--persist"
    ])
    while True:
        print("waiting for pod to start")
        if shell_pod_exists():
            start_pod.kill()
            start_pod.wait()
            break
        else:
            time.sleep(1)

def k_exec(command: list):
    subprocess.check_call([
        "kubectl", "--namespace", hub_name,
        "exec", shell_pod_name,
        "--"
    ] + command)

def k_get_output(command: list):
    return subprocess.check_output([
        "kubectl", "--namespace", hub_name,
        "exec", shell_pod_name,
        "--"
    ] + command).decode()

k_exec(["apt-get", "update", "--yes"])
k_exec(["apt-get", "install", "--yes", "rsync", "parallel", "screen"])

try:
    screen_sessions = k_get_output(["screen", "-ls"])
    if "copy" not in screen_sessions:
        start_screen = True
    else:
        start_screen = False
except subprocess.CalledProcessError:
    # No screen sessions running
    start_screen = True

if start_screen:
    k_exec(["screen", "-S", "copy", "-d", "-m", "--", "/bin/bash"])

def exec_in_screen(name: str, window_number: int, command: str):
    k_exec([
        "screen", "-S", name,
        "-p", str(window_number),
        "-X", "stuff", f"{command}^M"
    ])

ps_auxf = k_get_output(["ps", "auxf"])
if "parallel" not in ps_auxf:
    parallelization_factor = 96
    cmd_parts = [
        f"ls /root-homes/{hub_name}"
    ]

    if full_copy:
        command = f"cp -a /root-homes/{hub_name}/ /dest-fs/"
        # cmd_parts.append(f"parallel -j{parallelization_factor} cp -av /root-homes/{hub_name}/{{}} /dest-fs/{hub_name}/")
    else:
        dir_names = get_modified_user_dirs(cluster_name, hub_name, hours_prior)
        grep_param = "|".join(dir_names)
        cmd_parts.append(f"grep -P '{grep_param}'")

    cmd_parts.append(f"parallel -j{parallelization_factor} rsync -ah --progress --inplace /root-homes/{hub_name}/{{}} /dest-fs/{hub_name}/")

    command =  " | ".join(cmd_parts)

    exec_in_screen("copy", 0, command)