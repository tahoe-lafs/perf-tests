deploy:
	appcfg.py update frontend

bounce-introducer:
	ssh tahoe-lafs.org "~/tahoeperf-google/ve/bin/tahoe restart ~/tahoeperf-google/introducer"

# to run Datastore-accessing programs from home:
#  set GOOGLE_APPLICATION_CREDENTIALS=
#  set GCLOUD_DATASET_ID=
#  use ve-gcloud/bin/python (has 'pip install gcloud')

# gcloud compute project-info add-metadata --metadata introducer-furl=FURL perf-rootcap=ROOTCAP

# for each download trial:
#  when we use a new set of client/server instances:
#   python add_grid_config.py --notes NOTES --server-instance-type S --client-instance-type S
#  python download --max-time 1800 --notes NOTES -g GRID_CONFIG_ID MODE
#   probably MODE=partial-100MB
