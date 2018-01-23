# 1 - Take in variables (zoneName)
# 2 - Use zone name to seed to extract api
# 3 - Launch connection to API - get zone json_data
# 4 - Parse the data received to extract the records and short_answers
# 5 - Create terraform with parsed json_data
# 6 - Create Gitlab Files

import json, os, requests, re, subprocess, gitlab
from sys import argv
def setup_gitlab_repo(zone):
    gl = gitlab.Gitlab('https://<GITLAB URL>','<YOUR GITLAB API KEY>')
    gl.auth()
    groups = gl.groups.get(587)
    project = gl.projects.create({'name':'%s' % zone,'namespace_id':587,'visibility_level':20,'request_access_enabled':True,'only_allow_merge_if_build_succeeds':True,'approvals_before_merge':1,'only_allow_merge_if_all_discussions_are_resolved':True,'web_url':'<HTTP URL OF PARENT REPO>' % zone,'path_with_namespace':'csg/dns/public/%s' % zone,'name_with_namespace':'csg / dns / public / %s' % zone,'ssh_url_to_repo':'<SSH URL OF REPO>' % zone,'path':'%s' % zone,})
    var1 = project.variables.create({'key': 'AWS_ACCESS_KEY_ID', 'value': '<SETUP ACCESS KEY>'})
    var2 = project.variables.create({'key': 'AWS_SECRET_ACCESS_KEY', 'value': '<SETUP SECRET KEY>'})
    return url

def extract_ans(api):
    return_data = []
    data = {}
    for x in api['rrsets']:
        data['type'] = x['type']
        data['name'] = x['name']
        data['ans'] = x['records'][0]['content']
        return_data.append(data)
        data = {}
    return return_data

# Setup of a main.tf file for the particular DNS Domain
def setup_main(domain):
	with open('%s-main.tf' % domain, 'w') as tf:
		tf.write('''
        # Setup Provider
		terraform {
		  backend "s3" {
		    bucket                  = "aws-foundation"
		    key                     = "csg/dns/private/%s.tfstate"
		    region                  = "us-east-1"
            shared_credentials_file = <IF YOU'RE USING A CREDS FILE IT GOES HERE>
            profile                 = "default"
		  }
		}
		provider "aws" {
            region      = "us-east-1"
            shared_credentials_file = <IF YOU'RE USING A CREDS FILE IT GOES HERE>
            profile                 = "dev"

        }

		# Create %s zone
		resource "aws_route53_zone" "primary" {
		  name = "%s"
		  vpc_id = "<YOUR VPC ID HERE>"
          tags = {
            bu  = "<IF YOU WANT>"
            env = "<IF YOU WANT>"
            }
		}
		''' % (domain, domain, domain))
	print 'Setting up main.tf for %s' % (domain)

def clean_tf_record(type,record):
    output = type.lower()+"."+record.strip('*')
    output = re.sub('\.+','.',output).replace(".","_")
    output = re.sub('\_+','_',output)
    output = output[:-1]
    return output

def create_tf_file(zone, data):
    count = 0
    with open('%s.tf' % (zone.lower()),'w') as tf:
        print 'Setting up %s.tf file' % (zone)
        print 'Processing %s records' % (len(data))
        for r in data:
            tf.write('''resource "aws_route53_record" "%s" {
            zone_id = "${aws_route53_zone.primary.zone_id}"
            name = "%s"
            type = "%s"
            ttl = "86400"
            records = ["%s"]

            ''' % (clean_tf_record(r['type'],r['name']), r['name'], r['type'], r['ans']))
            tf.write('}\n\n')

def setup_gitlab_ci(domain):
	with open('.gitlab-ci.yml','w') as yml:
		compose = '''image: <GITLAB URL>:4443/library/terraform:latest #THIS IS WHERE YOUR IMAGE LIVES

stages:
- validate
- plan
- apply

before_script:
- scripts/creds.sh

#
# terraform stage templates
#

validate_%s:
  stage: validate
  script:
  - terraform get
  - terraform validate
  only:
  - branches
  except:
  - master

plan_%s:
  stage: plan
  script:

  - terraform init
  - terraform plan
  only:
  - tags@csg/dns/private/%s
  - master@csg/dns/private/%s

apply_%s:
  stage: apply
  script:
  - terraform init
  - terraform apply -refresh
  only:
  - tags@csg/dns/private/%s

		''' % (domain.replace(".","_"), domain.replace(".","_"), domain, domain, domain.replace(".","_"), domain)
		compose = compose.strip('\t')
		yml.write(compose)
		print "Setup Gitlab CI yml"

def main():
    script, zone = argv
    setup_main(zone)
    setup_gitlab_ci(zone)
    apikey = "<API KEY OF POWERDNS>"
    headers = {'X-API-Key': apikey }
    url = 'http://<IP ADDRESS OR URL OF POWERDNS SERVER:THE PORT API IS RESPONDING TO>/api/v1/servers/localhost/zones/%s.' % (zone)
    r = requests.get(url, headers=headers)
    data = extract_ans(r.json())
    create_tf_file(zone,data)
    subprocess.call(["terraform","fmt"])
    create_repo = raw_input("Do you want to setup Gitlab Repo? (y/n): ")
    if create_repo == "yes" or create_repo == "y" or create_repo == "Y":
        print 'Creating Repo...'
        repo = setup_gitlab_repo(zone)
        print 'Gitlab Repo Created: %s' % repo
    else:
        print "Not creating repo"
    print "Finished"

if __name__ == '__main__':
    main()
