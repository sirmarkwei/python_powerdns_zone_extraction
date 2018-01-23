# python_powerdns_zone_extraction

## Simple Python Extraction Scripts to interact with PowerDNS and setup Terraform files to be run in Gitlab

Pre-requisites
1. PowerDNS must be setup for API Access
2. Gitlab must have API Access
3. Remote State locations for Terraform
4. AWS profile that has ability to create Route53 zones

Extractzone.py will:
1. Take in your PowerDNS hosted zone as argument
2. Login to PowerDNS
3. Extract Zone's Record, Answer, Type
4. Write a terraform file with zone setup
5. Write a terraform file with all of the records
6. Write a gitlab CI file to perform a validate/plan/apply
