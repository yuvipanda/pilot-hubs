region = "us-west-2"

cluster_name = "nasa-cryo"

cluster_nodes_location = "us-west-2a"

user_buckets = {
    "scratch-staging": {
        "delete_after" : 7
    },
    "scratch": {
        "delete_after": 7
    },
}


hub_cloud_permissions = {
  "staging" : {
    requestor_pays: true,
    bucket_admin_access: ["scratch-staging"],
    extra_iam_policy: ""
  },
  "prod" : {
    requestor_pays: true,
    bucket_admin_access: ["scratch"],
    extra_iam_policy: ""
  },
}

# Sarah added this value because terraform asked for it to be provided on the
# command line when she executed `tf plan`
db_instance_identifier = "nasa-cryo"