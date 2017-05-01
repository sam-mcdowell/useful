from git import Repo
import shutil
import tempfile
import yaml
import os

BEFORE = "Wed Oct 21 11:21:59 2015 -0700"

temp_dir = tempfile.mkdtemp()
reqs = yaml.load(open("requirements.yml",'r').read())
pinned_reqs = []

try:
	for req in reqs:
		print("parsing: {}".format(req['name']))
		repo_dir = os.path.join(temp_dir, req['name'])
		repo = Repo.clone_from(req['src'], repo_dir, branch='master')
		git = repo.git
		pinned_version = git.rev_list("-n 1", "--before='{}'".format(BEFORE), req['version'])
		pinned_req = req
		pinned_req['version'] = str(pinned_version)
		pinned_reqs.append(pinned_req)
finally:
	shutil.rmtree(temp_dir)

with open("pinned_requirements.yml", 'w') as stream:
	stream.write(yaml.dump(pinned_reqs))