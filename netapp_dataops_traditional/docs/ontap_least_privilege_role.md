# ONTAP Least-Privilege Role for the DataOps Toolkit

This document describes the minimum ONTAP REST API privileges required for a custom role to support the full functionality of the NetApp DataOps Toolkit (Traditional). Following the principle of least privilege, this role grants only the access needed by the toolkit — no more.

> **Note:** NetApp recommends using an SVM-level account rather than a cluster admin account. The role defined here can be scoped to a specific SVM.

## Required API Endpoints

### Volume Management

| Endpoint | Access | Toolkit Operations |
|----------|--------|-------------------|
| `/api/storage/volumes` | `all` | List, create (FlexVol, FlexGroup, FlexClone), and delete volumes |

Operations covered: create volume, clone volume, delete volume, list volumes, mount/unmount volume (junction path), modify export policy, modify snapshot policy, split clone, restore from snapshot.

### Snapshot Management

| Endpoint | Access | Toolkit Operations |
|----------|--------|-------------------|
| `/api/storage/volumes/*/snapshots` | `all` | Create, list, get, and delete snapshots |

> **Note:** Volume restore-from-snapshot is performed via `PATCH /api/storage/volumes/{uuid}` (using the `restore_to` field), which is covered by the Volume Management privilege above.

### SnapMirror Management

| Endpoint | Access | Toolkit Operations |
|----------|--------|-------------------|
| `/api/snapmirror/relationships` | `all` | Create, list, get, update (resync), and delete SnapMirror relationships |
| `/api/snapmirror/relationships/*/transfers` | `all` | Trigger SnapMirror sync/transfer operations |

### FlexCache Management

| Endpoint | Access | Toolkit Operations |
|----------|--------|-------------------|
| `/api/storage/flexcache/flexcaches` | `all` | Create, list, get, update (prepopulate, writeback, sizing, atime-scrub, CIFS notifications), and delete FlexCache volumes |

### Export Policy Management

| Endpoint | Access | Toolkit Operations |
|----------|--------|-------------------|
| `/api/protocols/nfs/export-policies` | `all` | Create and delete export policies (with client-match rules) |

### Snapshot Policies (Read-Only)

| Endpoint | Access | Toolkit Operations |
|----------|--------|-------------------|
| `/api/storage/snapshot-policies` | `readonly` | Validate that a snapshot policy exists before assigning to a volume |

### Qtree Management

| Endpoint | Access | Toolkit Operations |
|----------|--------|-------------------|
| `/api/storage/qtrees` | `all` | Create and list qtrees |

> **Note:** Individual qtrees are accessed via `/api/storage/qtrees/{volume.uuid}/{id}` — the collection-level privilege covers this.

### Qtree Performance Metrics (Read-Only)

| Endpoint | Access | Toolkit Operations |
|----------|--------|-------------------|
| `/api/storage/qtrees/*/*/metrics` | `readonly` | Retrieve qtree IOPS, latency, and throughput metrics |

### CIFS/SMB Share Management

| Endpoint | Access | Toolkit Operations |
|----------|--------|-------------------|
| `/api/protocols/cifs/shares` | `all` | Create and list CIFS shares (with ACLs and properties) |

### SVM (Read-Only)

| Endpoint | Access | Toolkit Operations |
|----------|--------|-------------------|
| `/api/svm/svms` | `readonly` | Validate SVM name during CIFS share operations |

### Job Monitoring (Read-Only)

| Endpoint | Access | Toolkit Operations |
|----------|--------|-------------------|
| `/api/cluster/jobs` | `readonly` | Poll async job status for all create/modify/delete operations |

### CLI Passthrough

| Endpoint | Access | Toolkit Operations |
|----------|--------|-------------------|
| `/api/private/cli/volume` | `read_modify` | Disable SVM-DR protection on cloned volumes (`volume modify -vserver-dr-protection unprotected`) |
| `/api/private/cli/snapmirror` | `read_modify` | Modify SnapMirror policy and schedule (`snapmirror modify -policy ... -schedule ...`) |

> **Note:** The CLI passthrough endpoints are used because the toolkit performs two operations that require CLI-based access: disabling SVM-DR protection on FlexClones and modifying SnapMirror policy/schedule in a single call. The `read_modify` access level (ONTAP 9.11.1+) is sufficient since only PATCH is needed. For ONTAP 9.6–9.10.x, use `all` instead.

## Creating the Role

### Option 1: Using the ONTAP REST API

Create a custom role and add privileges for each endpoint:

```bash
# Create the role
curl -X POST "https://<cluster-mgmt>/api/security/roles" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "dataops_toolkit",
    "owner": {"name": "<svm_name>"},
    "privileges": [
      {"path": "/api/storage/volumes",                          "access": "all"},
      {"path": "/api/storage/volumes/*/snapshots",              "access": "all"},
      {"path": "/api/snapmirror/relationships",                 "access": "all"},
      {"path": "/api/snapmirror/relationships/*/transfers",     "access": "all"},
      {"path": "/api/storage/flexcache/flexcaches",             "access": "all"},
      {"path": "/api/protocols/nfs/export-policies",            "access": "all"},
      {"path": "/api/storage/snapshot-policies",                "access": "readonly"},
      {"path": "/api/storage/qtrees",                           "access": "all"},
      {"path": "/api/storage/qtrees/*/*/metrics",                 "access": "readonly"},
      {"path": "/api/protocols/cifs/shares",                    "access": "all"},
      {"path": "/api/svm/svms",                                 "access": "readonly"},
      {"path": "/api/cluster/jobs",                             "access": "readonly"},
      {"path": "/api/private/cli/volume",                       "access": "read_modify"},
      {"path": "/api/private/cli/snapmirror",                   "access": "read_modify"}
    ]
  }'
```

### Option 2: Using the ONTAP CLI

```
security login role create -vserver <svm_name> -role dataops_toolkit -cmddirname "volume"              -access all
security login role create -vserver <svm_name> -role dataops_toolkit -cmddirname "volume snapshot"     -access all
security login role create -vserver <svm_name> -role dataops_toolkit -cmddirname "snapmirror"          -access all
security login role create -vserver <svm_name> -role dataops_toolkit -cmddirname "volume flexcache"    -access all
security login role create -vserver <svm_name> -role dataops_toolkit -cmddirname "vserver export-policy" -access all
security login role create -vserver <svm_name> -role dataops_toolkit -cmddirname "volume snapshot policy" -access readonly
security login role create -vserver <svm_name> -role dataops_toolkit -cmddirname "volume qtree"        -access all
security login role create -vserver <svm_name> -role dataops_toolkit -cmddirname "vserver cifs share"  -access all
security login role create -vserver <svm_name> -role dataops_toolkit -cmddirname "vserver"             -access readonly
```

> **Note:** The CLI-based role definition maps to the equivalent REST API privileges. The exact command directory names may vary by ONTAP version.

### Creating the User Account

After creating the role, create a user account that uses it:

```bash
# REST API
curl -X POST "https://<cluster-mgmt>/api/security/accounts" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "dataops_user",
    "owner": {"name": "<svm_name>"},
    "role": {"name": "dataops_toolkit"},
    "applications": [{"application": "http", "authentication_methods": ["password"]}]
  }'
```

```
# CLI
security login create -vserver <svm_name> -user-or-group-name dataops_user -application http -authmethod password -role dataops_toolkit
```

## Subset Roles

If you don't need the full feature set, you can create a more restrictive role. Here are common subsets:

### Dataset Manager

The [Dataset Manager](dataset_manager_readme.md) uses volumes, snapshots, and export/snapshot policy validation only — no SnapMirror, FlexCache, Qtrees, or CIFS.

```json
{
  "privileges": [
    {"path": "/api/storage/volumes",              "access": "all"},
    {"path": "/api/storage/volumes/*/snapshots",  "access": "all"},
    {"path": "/api/protocols/nfs/export-policies", "access": "readonly"},
    {"path": "/api/storage/snapshot-policies",    "access": "readonly"},
    {"path": "/api/cluster/jobs",                 "access": "readonly"}
  ]
}
```

> **Note:** The Dataset Manager only needs `readonly` access to export policies (to validate they exist) — it inherits the root volume's policy when creating child datasets but does not create or delete policies itself.

### Volume + Snapshot Only (No SnapMirror, FlexCache, or CIFS)

```json
{
  "privileges": [
    {"path": "/api/storage/volumes",              "access": "all"},
    {"path": "/api/storage/volumes/*/snapshots",  "access": "all"},
    {"path": "/api/protocols/nfs/export-policies", "access": "all"},
    {"path": "/api/storage/snapshot-policies",    "access": "readonly"},
    {"path": "/api/cluster/jobs",                 "access": "readonly"},
    {"path": "/api/svm/svms",                     "access": "readonly"},
    {"path": "/api/private/cli/volume",           "access": "read_modify"}
  ]
}
```

> **Note:** The `/api/private/cli/volume` privilege is needed only if you use the `svm_dr_unprotect` option when cloning volumes.

### Read-Only (List/Get Only)

```json
{
  "privileges": [
    {"path": "/api/storage/volumes",              "access": "readonly"},
    {"path": "/api/storage/volumes/*/snapshots",  "access": "readonly"},
    {"path": "/api/snapmirror/relationships",     "access": "readonly"},
    {"path": "/api/storage/flexcache/flexcaches", "access": "readonly"},
    {"path": "/api/storage/snapshot-policies",    "access": "readonly"},
    {"path": "/api/storage/qtrees",              "access": "readonly"},
    {"path": "/api/storage/qtrees/*/*/metrics",    "access": "readonly"},
    {"path": "/api/protocols/cifs/shares",        "access": "readonly"},
    {"path": "/api/protocols/nfs/export-policies", "access": "readonly"},
    {"path": "/api/svm/svms",                     "access": "readonly"},
    {"path": "/api/cluster/jobs",                 "access": "readonly"}
  ]
}
```

## Additional Notes

- **ONTAP version compatibility:** The toolkit requires ONTAP 9.7+. FlexCache prepopulate requires ONTAP 9.8+. The `read_modify` access level requires ONTAP 9.11.1+ (use `all` for earlier versions). Qtree performance metrics require ONTAP 9.16+.
- **Cluster admin vs SVM admin:** This role is designed for SVM-scoped accounts. If you use a cluster-level account, the `/api/svm/svms` and `/api/cluster/jobs` endpoints are accessible by default.
- **SSL verification:** The toolkit connects to the ONTAP management LIF over HTTPS. Ensure the account has API (HTTP) access enabled.
- **Wildcard paths:** The `*` in endpoint paths (e.g., `/api/storage/volumes/*/snapshots`) represents any UUID. This is standard ONTAP RBAC path syntax for sub-resource access.
- **Export policy rules:** The toolkit creates export policies with inline rules (in the POST body), so no separate privilege for the `/api/protocols/nfs/export-policies/*/rules` sub-endpoint is needed.

## References

- [ONTAP REST API Documentation](https://docs.netapp.com/us-en/ontap-restapi/getting_started_with_the_ontap_rest_api.html)
- [netapp_ontap Python Library Documentation](https://library.netapp.com/ecmdocs/ECMLP3364865/html/index.html)
- [ONTAP Security Roles and Accounts](https://docs.netapp.com/us-en/ontap/authentication/index.html)
