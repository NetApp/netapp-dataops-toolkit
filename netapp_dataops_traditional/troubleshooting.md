# Troubleshooting

## Common Errors

### SSL Error: self-signed certificate

#### Error

```sh
Error: ONTAP Rest API Error: Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate (_ssl.c:1029)'))
```

You will encounter this error if your ONTAP cluster uses a self-signed certificate and no SSL certificate file path has been configured (i.e. `sslCertPath` is blank in your config).

#### Resolution

Download the ONTAP cluster's certificate and reconfigure the toolkit to use it.

1. Download the certificate (replace `<ONTAP_HOST>` with your management LIF hostname or IP):

```sh
echo | openssl s_client -connect <ONTAP_HOST>:443 -showcerts 2>/dev/null \
  | openssl x509 > ~/.netapp_dataops/ontap_cert.pem
```

2. Re-run configuration and provide the certificate path when prompted:

```sh
netapp_dataops_cli.py config
```

See the [SSL Certificate Configuration](docs/ontap_readme.md#ssl-certificate-configuration) section for full details.

### SSL Error: no appropriate subjectAltName fields were found

#### Error

```sh
Error: ONTAP Rest API Error: Caused by SSLError(CertificateError('no appropriate subjectAltName fields were found'))
```

You may encounter this error when using an older version of the toolkit (or a custom `verify` configuration) where the ONTAP certificate does not contain Subject Alternative Name (SAN) entries. This is common with default ONTAP self-signed certificates.

#### Resolution

Upgrade to the latest version of the toolkit and download the ONTAP certificate. When a certificate file path is configured, the toolkit verifies the certificate chain against the pinned cert while automatically skipping hostname/SAN checks.

1. Download the certificate:

```sh
echo | openssl s_client -connect <ONTAP_HOST>:443 -showcerts 2>/dev/null \
  | openssl x509 > ~/.netapp_dataops/ontap_cert.pem
```

2. Re-run configuration and provide the certificate path when prompted:

```sh
netapp_dataops_cli.py config
```

See the [SSL Certificate Configuration](docs/ontap_readme.md#ssl-certificate-configuration) section for full details.

### SSL Error: hostname mismatch

#### Error

```sh
Error: ONTAP Rest API Error: Caused by SSLError(SSLCertVerificationError(1, "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for '<hostname>' (_ssl.c:1029)"))
```

You may encounter this error when the ONTAP certificate's Common Name (CN) or Subject Alternative Names (SANs) do not match the hostname or IP address used to connect.

#### Resolution

Same as the "subjectAltName" error above — download the ONTAP certificate and configure its path. The toolkit will verify the certificate chain while skipping hostname matching.

### Mounting within Container

#### Error

```sh
Mounting volume 'project' at '/workspace/project'.
mount: /workspace/project: permission denied.
Error: Error running mount command:  Command '['mount', '10.61.188.49:/project', '/workspace/project']' returned non-zero exit status 32.
```

You will receive this or a similar error if you attempt to locally mount a data volume while operating within a container. It is not possible to mount a volume using the NetApp Data Science Toolkit while operating within a container. Mount operations are generally not permitted wtihin unprivileged containers.

#### Resolution

If you are using `docker run` to launch your container, you can locally mount your data volume on the host (prior to launching your container) and then bind mount it to your container using the `-v` option.

For example, if you want to mount the data volume 'project1' at '/workspace/project1' within a TensorFlow container, then run the following commands:

1. Mount data volume on host.

```sh
sudo -E ./netapp_dataops_cli.py mount volume --name=project1 --mountpoint=~/project1
[sudo] password for user:
Mounting volume 'project1' at '~/project1'.
Volume mounted successfully.
```

2. Launch container; bind mount data volume to container using `-v` option.

```sh
docker run -it --rm -v ~/project1:/workspace/project1 nvcr.io/nvidia/tensorflow:20.11-tf2-py3
```

### NFS Utilities not Installed

#### Error

```sh
Mounting volume 'project' at '/home/jovyan/project'.
mount: /home/jovyan/project: bad option; for several filesystems (e.g. nfs, cifs) you might need a /sbin/mount.<type> helper program.
Error: Error running mount command:  Command '['mount', '10.61.188.49:/project', '/home/jovyan/project']' returned non-zero exit status 32.
```

You may encounter this error when attempting to locally mount a data volume.

#### Resolution

To resolve this error, install the NFS utilities on your local host.

For Ubuntu hosts, you can install the NFS utilities using the following command:

```sh
apt update
apt install nfs-common
```

For Red Hat or CentOS hosts, you can install the NFS utilities using the following command:

```sh
yum install nfs-utils
```

### No Assigned Aggregates

#### Error

```sh
Error: ONTAP Rest API Error:  Job failed: Cannot create volume. Reason: aggregate ai_vsim97_01_FC_1 is not in aggr-list of Vserver ai_data.
```

You may encounter this error if you specify a SVM (Storage VM) admin account as the 'ONTAP API Username' and/or a SVM management interface as the 'ONTAP management interface hostname or IP address' in your config file.

#### Resolution

To resolve this error, you or your storage admin must assign the aggregate mentioned in the error message to the SVM mentioned in the error message (note that the SVM is referred to as the vserver in the error message). Using the above error message as an example, the aggregate 'ai_vsim97_01_FC_1' needs to be assigned to the SVM 'ai_data'. This action can be performed using the ONTAP CLI by running the following coommand:

```sh
vserver modify -vserver ai_data -aggr-list ai_vsim97_01_FC_1
```

### Volume Not Exported

#### Error

```sh
AttributeError: The 'nas' field has not been set on the Volume. Try refreshing the object by calling get().
```

You may encounter this error when using v1.0 of the toolkit if there is a volume within the SVM that you are using that has not been exported as an NFS share (i.e. that has not been mounted to a junction path on the storage system). 

#### Resolution

The easiest solution is to upgrade to v1.1. If you must continue using v1.0, then you or your storage admin must export the offending volume as an NFS share. This can be done using the ONTAP CLI as demonstrated in the following example for a volume named 'project1'.

```sh
volume mount -volume project1 -junction-path /project1
```
