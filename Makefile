deploy:
	appcfg.py update .

bounce-introducer:
	ssh tahoe-lafs.org "~/tahoeperf-google/ve/bin/tahoe restart ~/tahoeperf-google/introducer"
