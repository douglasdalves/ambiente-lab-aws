#!/usr/bin/env python3

import boto3, os, json
import dateutil.parser
import csv

from sys import argv
from botocore.exceptions import ClientError, BotoCoreError
from datetime import datetime, timedelta

aws_profile = argv[1]
role_name = argv[2]
aws_regions = "us-east-1"

def sso_login(aws_profile):

  if aws_profile == "comp-interno" or aws_profile == "comp-diveo":
    dir = os.path.expanduser('~/.aws/sso/cache')

    json_files = [pos_json for pos_json in os.listdir(dir) if pos_json.endswith('.json')]

    for json_file in json_files :
      path = dir + '/' + json_file
      with open(path) as file :
        data = json.load(file)
        if 'accessToken' in data:
          accessToken = data['accessToken']
          return accessToken

def organizations(aws_profile):

  session = boto3.session.Session(profile_name=aws_profile)
  org = session.client('organizations')
  return org

def list_account(aws_profile, role_name):

  org = organizations(aws_profile)
  desc_org = org.describe_organization().get('Organization')
  master_account_id = desc_org.get('MasterAccountId')

  list_accounts = org.get_paginator('list_accounts')
  page_iterator = list_accounts.paginate()
  for acc in page_iterator:
    for account in acc['Accounts']:
      if (account['Status'] == 'ACTIVE'):
        account_id = account['Id']
        account_name = account['Name']
        account_email = account['Email']
        account_status = account['Status']
        account_join = account['JoinedMethod']
        account_join_date = account['JoinedTimestamp'].date()

        if aws_profile == 'edpayer' or aws_profile == 'b2w' or aws_profile == 'cs' or aws_profile == 'prev' or aws_profile == 'pague' or aws_profile == 'printlaser':
          boto3.setup_default_session(profile_name='comp-divo')
          sts_client = boto3.client('sts')

          role_info = {
            'RoleArn': f'arn:aws:iam::{account_id}:role/{role_name}',
            'RoleSessionName': role_name
          }

          try:
            credentials = sts_client.assume_role(**role_info)
          except ClientError as err:
            if err.response['Error']['Code'] == 'AccessDenied':
              r = [
                master_account_id, account_id, account_name, account_email,
                account_join, account_join_date, account_status, f'Unidentified by {role_name}'
              ]
              yield r
              pass
          else:
            session = boto3.session.Session(
              aws_access_key_id=credentials['Credentials']['AccessKeyId'],
              aws_secret_access_key=credentials['Credentials']['SecretAccessKey'],
              aws_session_token=credentials['Credentials']['SessionToken'] 
            )
            try:
              support = session.client('support')
              support.describe_cases()
            except ClientError as err:
              if err.response['Error']['Code'] == 'SubscriptionRequiredException':
                r = [
                  master_account_id, account_id, account_name, account_email,
                  account_join, account_join_date, account_status, "AWS Support Basic"
                ]
                yield r
                pass
            else:
                r = [
                  master_account_id, account_id, account_name, account_email,
                  account_join, account_join_date, account_status, "AWS Support Enterprise"
                ]
                yield r

        if aws_profile == 'pagseguro':
          boto3.setup_default_session(profile_name=aws_profile)
          sts_client = boto3.client('sts')

          role_info = {
            'RoleArn': f'arn:aws:iam::{account_id}:role/{role_name}',
            'RoleSessionName': role_name
          }

          try:
            credentials = sts_client.assume_role(**role_info)
          except ClientError as err:
            if err.response['Error']['Code'] == 'AccessDenied':
              r = [
                master_account_id, account_id, account_name, account_email,
                account_join, account_join_date, account_status, f'Unidentified by {role_name}'
              ]
              yield r
              pass
          else:
            session = boto3.session.Session(
              aws_access_key_id=credentials['Credentials']['AccessKeyId'],
              aws_secret_access_key=credentials['Credentials']['SecretAccessKey'],
              aws_session_token=credentials['Credentials']['SessionToken'] 
            )
            try:
              support = session.client('support')
              support.describe_cases()
            except ClientError as err:
              if err.response['Error']['Code'] == 'SubscriptionRequiredException':
                r = [
                  master_account_id, account_id, account_name, account_email,
                  account_join, account_join_date, account_status, "AWS Support Basic"
                ]
                yield r
                pass
            else:
                r = [
                  master_account_id, account_id, account_name, account_email,
                  account_join, account_join_date, account_status, "AWS Support Enterprise"
                ]
                yield r

def list_account_with_sso(aws_profile, role_name):

  accessToken = sso_login(aws_profile)
  if accessToken:
    if aws_profile == "com-interno" or aws_profile == "comp-diveo":

      org = organizations(aws_profile)
      desc_org = org.describe_organization().get('Organization')
      master_account_id = desc_org.get('MasterAccountId')

      client = boto3.client('sso',region_name=aws_regions)
      response = client.get_role_credentials(
        roleName=role_name,
        accountId=master_account_id,
        accessToken=accessToken
      )

      session = boto3.Session(
        aws_access_key_id=response['roleCredentials']['accessKeyId'],
        aws_secret_access_key=response['roleCredentials']['secretAccessKey'],
        aws_session_token=response['roleCredentials']['sessionToken'],
        region_name=aws_regions
      )

      c_org = session.client('organizations')
      paginator = c_org.get_paginator('list_accounts')
      list_accounts = paginator.paginate()

      for acc in list_accounts:
        for account in acc['Accounts']:

          if (account['Status'] == 'ACTIVE'):
              account_id = account['Id']
              account_name = account['Name']
              account_email = account['Email']
              account_status = account['Status']
              account_join = account['JoinedMethod']
              account_join_date = account['JoinedTimestamp'].date()

              try:
                response = client.get_role_credentials(
                  roleName=role_name,
                  accountId=account_id,
                  accessToken=accessToken
                )
              except ClientError as err:
                if err.response['Error']['Code'] == "ForbiddenException":
                  r = [
                    master_account_id, account_id, account_name, account_email,
                    account_join, account_join_date, account_status, f'Unidentified by {role_name}'
                  ]
                  yield r
                  pass
              else:
                session = boto3.Session(
                  aws_access_key_id=response['roleCredentials']['accessKeyId'],
                  aws_secret_access_key=response['roleCredentials']['secretAccessKey'],
                  aws_session_token=response['roleCredentials']['sessionToken'],
                  region_name=aws_regions
                )

                try:
                  support = session.client('support')
                  support.describe_cases()
                except ClientError as err:
                  if err.response['Error']['Code'] == "SubscriptionRequiredException":
                    r = [
                      master_account_id, account_id, account_name, account_email,
                      account_join, account_join_date, account_status, "AWS Support Basic"
                    ]
                    yield r
                    pass
                else:
                    r = [
                      master_account_id, account_id, account_name, account_email,
                      account_join, account_join_date, account_status, "AWS Support Enterprise"
                    ]
                    yield r


def writer_csv(aws_profile):

  dt = datetime.now().date()
  header = [ 
    "AWS_Master_Account_Id", "AWS_Account_Id", "AWS_Account_Name", "AWS_Account_Email",
    "AWS_Account_Join", "AWS_Account_Join_Date", "AWS_Account_Status", "AWS_Support_Plans"
  ]

  with open(f'{aws_profile}-list-accounts-{dt}.csv', 'w', encoding='UTF8', newline='') as file:
    writer = csv.writer(file, delimiter=';')
    writer.writerow(header)

    if list_account_with_sso(aws_profile, role_name):
      for l_acc in list_account_with_sso(aws_profile, role_name):
        master_id = l_acc[0]
        acc_id = l_acc[1]
        acc_name = l_acc[2]
        acc_email = l_acc[3]
        acc_join = l_acc[4]
        acc_join_dt = l_acc[5]
        acc_status = l_acc[6]
        acc_sup_plans = l_acc[7]
        row = [
          master_id, acc_id, acc_name, acc_email, acc_join, acc_join_dt,
          acc_status, acc_sup_plans
        ]
        writer.writerow(row)

    if list_account(aws_profile, role_name):
      for l_acc in list_account(aws_profile, role_name):
        master_id = l_acc[0]
        acc_id = l_acc[1]
        acc_name = l_acc[2]
        acc_email = l_acc[3]
        acc_join = l_acc[4]
        acc_join_dt = l_acc[5]
        acc_status = l_acc[6]
        acc_sup_plans = l_acc[7]
        row = [
          master_id, acc_id, acc_name, acc_email, acc_join, acc_join_dt,
          acc_status, acc_sup_plans
        ]
        writer.writerow(row)

if __name__ == "__main__":
  writer_csv(aws_profile)
