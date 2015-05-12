deploy:
	appcfg.py update frontend

bounce-introducer:
	ssh tahoe-lafs.org "~/tahoeperf-google/ve/bin/tahoe restart ~/tahoeperf-google/introducer"

# to run Datastore-accessing programs from home:
#  set GOOGLE_APPLICATION_CREDENTIALS=
#  set GCLOUD_DATASET_ID=
#  use ve-gcloud/bin/python (has 'pip install gcloud')
