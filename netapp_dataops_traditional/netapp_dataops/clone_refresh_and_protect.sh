
##################################################################################################################################################
# create rw vol 
##################################################################################################################################################
./netapp_dataops_cli.py create volume --cluster-name=cluster1 --svm=svm_a --name=vol1 --size=100GB --type=flexvol --aggregate=cluster1_01_SSD_1
# Creating volume 'vol1' on svm 'svm_a'
# Volume created successfully.

##################################################################################################################################################
# create dp vol 
##################################################################################################################################################
./netapp_dataops_cli.py create volume --cluster-name=cluster2 --svm=svm_b --name=vol1 --size=100GB --type=flexvol --aggregate=cluster2_01_SSD_1 --dp
# Creating volume 'vol1' on svm 'svm_b'
# Volume created successfully.

##################################################################################################################################################
# create snapmirror relationship between volumes created 
##################################################################################################################################################
./netapp_dataops_cli create snapmirror-relationship --cluster-name=cluster2 --source-svm=svm_a --target-svm=svm_b --source-vol=vol1 --target-vol=vol1 --schedule=hourly --policy=MirrorAllSnapshots --action=initialize
# Creating snapmirror relationship: svm_a:vol1 -> svm_b:vol1
# Setting snapmirror policy as: MirrorAllSnapshots schedule:hourly
# Setting state to snapmirrored, action:initialize

##################################################################################################################################################
# creating snapshot with retention, snapshots prefixed with daily will be deleted if they are older than 2d  
##################################################################################################################################################
 ./netapp_dataops_cli.py create snapshot --cluster=cluster1 --svm=svm_a --volume=vol1 --name=daily --retention=2d
# Creating snapshot 'daily.2022-04-23_153257'.
# Snapshot created successfully.

./netapp_dataops_cli.py create snapshot --cluster=cluster1 --svm=svm_a --volume=vol1 --name=daily --retention=2d
# Creating snapshot 'daily.2022-04-23_153304'.
# Snapshot created successfully.

./netapp_dataops_cli.py create snapshot --cluster=cluster1 --svm=svm_a --volume=vol1 --name=daily --retention=2d
# Creating snapshot 'daily.2022-04-23_153307'.
# Snapshot created successfully.

##################################################################################################################################################
# creating snapshot with retention, snapshots prefixed with daily will be deleted if they are more than 2 of them   
##################################################################################################################################################
./netapp_dataops_cli.py create snapshot --cluster=cluster1 --svm=svm_a --volume=vol1 --name=daily --retention=2
# Creating snapshot 'daily.2022-04-23_153434'.
# Snapshot created successfully.
# Deleting snapshot 'daily.2022-04-23_153257'.
# Snapshot deleted successfully.
# Deleting snapshot 'daily.2022-04-23_153304'.
# Snapshot deleted successfully.

##################################################################################################################################################
# issue snapmirror sync based on svm and vol name
##################################################################################################################################################
./netapp_dataops_cli.py sync snapmirror-relationship  --cluster-name=cluster2 --svm=svm_b --name=vol1 --wait
# Triggering sync operation for SnapMirror relationship (UUID = aa91b2e5-c319-11ec-bdba-005056b08a86).
# Sync operation successfully triggered.
# Waiting for sync operation to complete.
# Status check will be performed in 10 seconds...
# Success: Sync operation is complete.

##################################################################################################################################################
# clone volume (no pre clone exists) between svms base snapshot will be the newest prefixed with daily (daily*)
##################################################################################################################################################
./netapp_dataops_cli.py clone volume --cluster-name=cluster1 --source-svm=svm_a --target-svm=svm_a_clones --source-volume=vol1 --source-snapshot=daily* --name=vol1_clone --export-hosts host1:host2:host3 --refresh
# Creating clone volume 'svm_a_clones:vol1_clone' from source volume 'svm_a:vol1'.
# Warning: Cannot apply uid of '0' when creating clone; uid of source volume will be retained.
# Warning: Cannot apply gid of '0' when creating clone; gid of source volume will be retained.
# Snapshot 'daily.2022-04-23_153434' will be used to create the clone.
# Clone volume created successfully.
# Creating export-policy:netapp_dataops_vol1_clone
# Setting export-policy:netapp_dataops_vol1_clone snapshot-policy:default

##################################################################################################################################################
# clone volume (no pre clone exists) between svms base snapshot will be the newest prefixed with daily (daily*) - base vol is dp replication copy of the production base
##################################################################################################################################################
 ./netapp_dataops_cli.py clone volume --cluster-name=cluster2 --source-svm=svm_b --target-svm=svm_b_clones --source-volume=vol1 --source-snapshot=daily* --name=vol1_clone --export-hosts host1:host2:host3 --refresh
# Creating clone volume 'svm_b_clones:vol1_clone' from source volume 'svm_b:vol1'.
# Warning: Cannot apply uid of '0' when creating clone; uid of source volume will be retained.
# Warning: Cannot apply gid of '0' when creating clone; gid of source volume will be retained.
# Snapshot 'daily.2022-04-23_153434' will be used to create the clone.
# Clone volume created successfully.
# Creating export-policy:netapp_dataops_vol1_clone
# Setting export-policy:netapp_dataops_vol1_clone snapshot-policy:default

##################################################################################################################################################
# create snapmirror between clones and issue resync 
##################################################################################################################################################
./netapp_dataops_cli create snapmirror-relationship --cluster-name=cluster2 --source-svm=svm_a_clones --target-svm=svm_b_clones --source-vol=vol1_clone --target-vol=vol1_clone --schedule=hourly --policy=MirrorAllSnapshots --action=resync
# Creating snapmirror relationship: svm_a_clones:vol1_clone -> svm_b_clones:vol1_clone
# Setting snapmirror policy as: MirrorAllSnapshots schedule:hourly
# Setting state to snapmirrored, action:resync


##################################################################################################################################################
# create new daily snapshot on the clone base 
##################################################################################################################################################
./netapp_dataops_cli.py create snapshot --cluster=cluster1 --svm=svm_a --volume=vol1 --name=daily --retention=2d
# Creating snapshot 'daily.2022-04-23_154633'.
# Snapshot created successfully.

##################################################################################################################################################
# sync snapmirror for clone base to make the new dily snapshot avaialble in the dr 
##################################################################################################################################################
./netapp_dataops_cli.py sync snapmirror-relationship  --cluster-name=cluster2 --svm=svm_b --name=vol1 --wait
# Triggering sync operation for SnapMirror relationship (UUID = aa91b2e5-c319-11ec-bdba-005056b08a86).
# Sync operation successfully triggered.
# Waiting for sync operation to complete.
# Status check will be performed in 10 seconds...
# Success: Sync operation is complete.

##################################################################################################################################################
# refresh the prod and dr clones, this will delete the older clone and recreate it based on the new snapshot (--refresh )
##################################################################################################################################################
./netapp_dataops_cli.py clone volume --cluster-name=cluster1 --source-svm=svm_a --target-svm=svm_a_clones --source-volume=vol1 --source-snapshot=daily* --name=vol1_clone --export-hosts host1:host2:host3 --refresh
# Deleting volume 'svm_a_clones:vol1_clone'.
# release relationship: svm_a_clones:vol1_clone -> svm_b_clones:vol1_clone
# Volume deleted successfully.
# Creating clone volume 'svm_a_clones:vol1_clone' from source volume 'svm_a:vol1'.
# Warning: Cannot apply uid of '0' when creating clone; uid of source volume will be retained.
# Warning: Cannot apply gid of '0' when creating clone; gid of source volume will be retained.
# Snapshot 'daily.2022-04-23_154633' will be used to create the clone.
# Clone volume created successfully.
# Creating export-policy:netapp_dataops_vol1_clone
# Setting export-policy:netapp_dataops_vol1_clone snapshot-policy:default

./netapp_dataops_cli.py clone volume --cluster-name=cluster2 --source-svm=svm_b --target-svm=svm_b_clones --source-volume=vol1 --source-snapshot=daily* --name=vol1_clone --export-hosts host1:host2:host3 --refresh
# Deleting volume 'svm_b_clones:vol1_clone'.
# Deleting snapmirror relationship: svm_b_clones:vol1_clone
# Volume deleted successfully.
# Creating clone volume 'svm_b_clones:vol1_clone' from source volume 'svm_b:vol1'.
# Warning: Cannot apply uid of '0' when creating clone; uid of source volume will be retained.
# Warning: Cannot apply gid of '0' when creating clone; gid of source volume will be retained.
# Snapshot 'daily.2022-04-23_154633' will be used to create the clone.
# Clone volume created successfully.
# Creating export-policy:netapp_dataops_vol1_clone
# Setting export-policy:netapp_dataops_vol1_clone snapshot-policy:default

##################################################################################################################################################
# protect new clone
##################################################################################################################################################
./netapp_dataops_cli create snapmirror-relationship --cluster-name=cluster2 --source-svm=svm_a_clones --target-svm=svm_b_clones --source-vol=vol1_clone --target-vol=vol1_clone --schedule=hourly --policy=MirrorAllSnapshots --action=resync
# Creating snapmirror relationship: svm_a_clones:vol1_clone -> svm_b_clones:vol1_clone
# Setting snapmirror policy as: MirrorAllSnapshots schedule:hourly
# Setting state to snapmirrored, action:resync


