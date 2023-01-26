from typing import Any, Dict, Optional
import boto3
from botocove import cove, CoveSession
ALL_REGIONS = [r["RegionName"] for r in boto3.client("ec2").describe_regions()["Regions"]]
def get_region_instances(session: CoveSession, region_name: Optional[str]=None) -> int:
    ec2 = session.client("ec2", region_name=region_name)
    paginator = ec2.get_paginator("describe_instances")
    retries = 3
    for retry in range(retries):
        vms_count = 0
        try:
            for page in paginator.paginate():
                for reservation in page["Reservations"]:
                    vms_count += len(reservation.get("Instances", []))
        except Exception as e:
            continue
        return vms_count
    return 0
@cove(regions=ALL_REGIONS, policy_arns="arn:aws:iam::aws:policy/AdministratorAccess")
def get_cove_region_instances(session: CoveSession) -> int:
    return get_region_instances(session)
def current_account_instance_count(session: boto3.Session) -> int:
    total = 0
    print("getting current account vms")
    for region in ALL_REGIONS:
        ret = get_region_instances(session, region)
        print(f"{region=}, {ret=}")
        total += ret
    print(f"done current account vms: {total}")
    return total
def main():
    # Add the current accounts
    total = current_account_instance_count(boto3.Session())
    account_region_instances = get_cove_region_instances()
    for result in account_region_instances["Results"]:
        total += result["Result"]
    errors = len(account_region_instances["Exceptions"] + account_region_instances["FailedAssumeRole"])
    print(f"Found {total} vms, encountered {errors} errors")
if __name__ == "__main__":
    main()