./netapp_dataops_cli sync snapmirror-relationship --cluster-name=bru-cluster --svm=prd-svmdr --name=vol1 --wait
./netapp_dataops_cli clone volume --cluster-name=bru-cluster --name=clone11 --source-volume=vol1 --source-svm=prd-svmdr --target-svm=drpclone --source-snapshot=snap* --export-hosts 10.5.5.3:host1:10.6.4.0/24 -refresh
./netapp_dataops_cli clone volume --cluster-name=tlv-cluster --name=clone11 --source-volume=vol1 --source-svm=prd --target-svm=prdclone --source-snapshot=snap* --export-hosts 10.5.5.3:host1:10.6.4.0/24 -refresh 
./netapp_dataops_cli create snapmirror-relationship --cluster-name=tlv-cluster --source-svm=drpclone --target-svm=prdclone --source-vol=clone11 --target-vol=clone11 --schedule daily --policy MirrorAllSnapshots --action=resync 
./netapp_dataops_cli sync snapmirror-relationship  --cluster-name=tlv-cluster --svm=prdclone --name=clone11 -w
