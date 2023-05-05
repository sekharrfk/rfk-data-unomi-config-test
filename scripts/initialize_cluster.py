"""
    initialize_cluster.py
    ~~~~~~~~~~~~~~~~~
    :date:       2022-11-16
    :author:     Shivam / Saran
    Purpose of this script is to deploy the json rules, schema and profile-properties
    for unomi to a given environment.The rules configuration is defined in
    rfk-data-unomi/rules directory in a json format.
    The profile-properties and schema configurations are obtained via UserAPI.

    Parameters:
        env     :   environment name (valid values 'dev', 'staging', 'prod', 'local'). Default value 'local'
        object  :   object to deploy (valid values 'schemas', 'rules', 'profile-properties').
        domain  :   comma separated multiple domain id or id's to be deployed
        script  :   comma separated multiple script or script's to deploy. Default value 'all'
                    This is expected to be the metadata id.

    Working directory:  rfk-data-unomi/
    Sample python execution:
        python3 scripts/deployment/initialize_cluster.py -e local -o rules -d 123131,32421
        python3 scripts/deployment/initialize_cluster.py -e local -o rules -d 1231231 -s defaultVisitorAttributes
        python3 scripts/deployment/initialize_cluster.py --env local --domain 1234,2342 --object profile-properties --script all
        python3 scripts/deployment/initialize_cluster.py --env local --domain 1234,2342 --object rules
                                                    --script defaultVisitorAttributes, productOrderSplitEvent
    Execution Steps are:
    1. Parse the parameters
    2. Read the json rule, schema, profile-properties present in the file or from UserAPI
    3. Pass it as payload to call_unomi_api function
    3. Call the unomi api to create rules, schema, profile-properties using the requests module

    changelog:
    :date        :issue     :assignee    :description
"""

import json
import sys
import argparse
from vars import ENVIRONMENT, DOMAINS, OBJECTS, LOGGING_FORMAT, VALID_STATUS, VALID_OBJECTS_LIST
import logging
from utils import get_required_variables, deploy_objects

logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)


def validate_required_runtime_args(args: dict):
    """
    Validated the runtime arguments
    1. Checks if 'object' and 'domain' is passed in runtime argument
    2. Check if 'object' is a supported object type by the script
    :param args: runtime arguments' dictionary
    :return: 'valid' if check passed, otherwise error message
    """
    status = VALID_STATUS
    # Checking if required fields are passed
    if args.object is None or args.domain is None:
        status = "Required attribute domains/objects is missing. Terminating the script"

    # Checking if object type is a supported object
    if args.object not in VALID_OBJECTS_LIST:
        status = f"Object Type '{args.object}' is not supported yet."
    return status


def parse_runtime_args():
    """
    Parse all the runtime argument, validate them
    :return: data dictionary with all the required parameters
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--env", help="environment name (valid values 'dev', 'staging', 'prod', 'local'). "
                                            "Default value 'local'")
    parser.add_argument("-d", "--domain", help="Comma separated multiple domain id/'s to be deployed")
    parser.add_argument("-o", "--object", help="object to deploy (valid values 'schemas', 'rules', "
                                               "'profile-properties')")
    parser.add_argument("-s", "--script", help="Deploy all the objects or specific object. Default value 'all'")
    args = parser.parse_args()

    # Exit if invalid runtime arguments are passed
    status = validate_required_runtime_args(args)
    if status != VALID_STATUS:
        logging.error(status)
        logging.error("Deployment Failed")
        sys.exit(status)

    return get_required_variables(args)


if __name__ == '__main__':
    data_dict = parse_runtime_args()
    domains = data_dict.get(DOMAINS).split(",")
    environ = data_dict.get(ENVIRONMENT)
    failed_tracker = dict()
    for domain in domains:
        logging.info("====== Starting deployment for '{}' domain ======".format(domain))
        failed_requests = deploy_objects(domain, data_dict)
        if len(failed_requests) > 0:
            failed_tracker[domain] = failed_requests
        logging.info("====== Completed deployment for '{}' domain ======".format(domain))

    if len(failed_tracker.keys()) == 0:
        logging.info("Successful deployment for '{}' of '{}' domains to '{}' environment".
                     format(data_dict.get(OBJECTS), domains, data_dict.get(ENVIRONMENT)))
    else:
        logging.error("Failed Deployment mapping: {}".format(json.dumps(failed_tracker)))
        logging.error("Failed deployment for '{}' to '{}' environment".
                      format(data_dict.get(OBJECTS), data_dict.get(ENVIRONMENT)))

        logging.error("Deployment failed")
        sys.exit(1)
