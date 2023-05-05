import json
import logging
import requests
from jinja2 import Environment, FileSystemLoader
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError

from vars import *


def call_unomi_api(url, payload):
    """
    Calls the unomi endpoint to create an unomi object
    :param url: unomi endpoint url
    :param payload: definition for the new object
    :return: response object
    """
    auth_token = os.getenv(AUTH_TOKEN, default=None)
    REQUEST_HEADERS[API_KEY_HEADER] = auth_token
    response = requests.post(url=url,
                             headers=REQUEST_HEADERS,
                             auth=HTTPBasicAuth(KARAF_USER, KARAF_PASS),
                             data=json.dumps(payload))
    return response


def get_source_target_mapping(args: dict) -> dict:
    """
    Update data dictionary with source and target information
    :param args: data dictionary
    :return: updated data dictionary with source and target information
    """
    obj = args.get(OBJECTS)
    env_var = args.get(ENVIRONMENT)
    args[SRC_TYPE] = None

    if obj == SCHEMA_IDENTIFIER:
        args[SRC_PATH] = f"{USER_API_URL.format(env=env_var)}{USER_API_SCHEMA_ENDPOINT}"
        args[TGT_ENDPOINT] = UNOMI_SCHEMA_ENDPOINT
        args[SRC_TYPE] = USER_API_SRC
    elif obj == RULE_IDENTIFIER:
        args[SRC_PATH] = RULES_DIR
        args[TGT_ENDPOINT] = UNOMI_RULE_ENDPOINT
        args[SRC_TYPE] = FILE_SRC
    elif obj == PROFILE_PROPERTIES_IDENTIFIER:
        args[SRC_PATH] = f"{USER_API_URL.format(env=env_var)}{USER_ATTRIBUTES_ENDPOINT}"
        args[TGT_ENDPOINT] = UNOMI_PROFILE_ENDPOINT
        args[SRC_TYPE] = USER_API_SRC
    elif obj == SCOPES_IDENTIFIER:
        args[SRC_PATH] = RULES_DIR
        args[TGT_ENDPOINT] = UNOMI_SCOPE_ENDPOINT
    return args


def get_required_variables(args: dict):
    """
    Parse the required variables from the runtime arguments
    :param args: runtime arguments' dictionary
    :return: data dict
    """
    required_attr = dict()
    required_attr[ENVIRONMENT] = "local" if args.env is None else args.env
    required_attr[OBJECTS] = args.object
    required_attr[SCRIPTS] = "all" if args.script is None else args.script
    required_attr[DOMAINS] = args.domain
    final_attr = get_source_target_mapping(required_attr)
    return final_attr


def datatype_mapping(datatype):
    """
    This function is used to map profile datatypes defined in user API to unomi supported datatypes
    :param datatype: datatype defined in user API for a profile
    :return: unomi mapped datatype
    """
    if datatype.startswith("[]"):
        return datatype_mapping(datatype[2:].strip())
    return UNOMI_DATATYPE_MAPPING.get(datatype, datatype)


def update_key_mapping(mapping):
    """
    This function creates a mapping to replace variables from the template file
    :param mapping:
    :return:
    """
    profile_id = mapping.get("rfk_mapping").get("unomi")
    profile_datatype = datatype_mapping(mapping.get("datatype"))
    if not profile_datatype:
        return None
    profile_merge_strategy = DEFAULT_MERGE_STRATEGY

    if profile_id.split(".")[0].lower().strip() == "properties":
        profile_id = ".".join(profile_id.split(".")[1:])

    if "merge_strategy" in mapping.keys() and len(mapping.get("merge_strategy")) > 0:
        profile_merge_strategy = mapping.get("merge_strategy")

    return {
        "profile_id": profile_id,
        "profile_name": mapping.get("name"),
        "profile_description": mapping.get("description"),
        "profile_datatype": profile_datatype,
        "profile_mergeStrategy": profile_merge_strategy
    }


def read_config_file_system(args):
    """
    Read config file from a file system
    :param args: data dictionary
    :return: json object
    Sample return Object:
     {
        "rules":
        {
            "defaultVisitorAttribute":
            {
                "metadata": {
                    "id": "defaultVisitorAttributes",
                    "name": "default visitor attribute rule",
                    "description": "Updates various visitor properties for all the events",
                    "tags": ["generic"],
                    "systemTags" : ["sitecoreRule"]
                },
                ...
                ...
            },
            "productOrderEvent": {...}
        }
     }
    """
    object_dir = args.get(SRC_PATH)
    content_data = dict()
    for file in os.listdir(object_dir):
        file_path = os.path.join(object_dir, file)
        with open(file_path) as fs:
            content = fs.read()
        content_json = json.loads(content)
        content_data[content_json.get("metadata").get("id")] = content_json

    return {args.get(OBJECTS): content_data}


def read_config_user_api(args):
    """
    Read src config from a user API
    :param args: data dictionary
    :return: json object
    """
    url = args.get(SRC_PATH)
    logging.info("Deployment URL: {}".format(url))

    try:
        response = requests.get(url)
        response.raise_for_status()
    except HTTPError as http_err:
        logging.error(f"Error while calling '{url}' statuscode: '{response.status_code}'")
        raise Exception(f'HTTP error occurred: {http_err}')
    except Exception as err:
        logging.error(f"Error occurred: {err}")
        raise Exception(f'Error occurred: {err}')

    return json.loads(response.text)


def get_filtered_config(args, config, valid_objects):
    """
    Filter the source configuration for the required scripts to be deployed
    :param args: data dictionary
    :param config: source config dictionary
    :param valid_objects: list of valid objects
    :return: list of filtered source config dictionary
    """
    valid_scripts = args.get(SCRIPTS)
    obj_type = args.get(OBJECTS)
    if valid_scripts == ALL_IDENTIFIER or obj_type == SCOPES_IDENTIFIER:
        return config.get(obj_type)
    obj = config.get(obj_type)
    final_dict = dict()
    config_keys = obj.keys()
    for key in valid_objects:
        if key in config_keys:
            final_dict[key] = obj.get(key)
    return final_dict


def log_response(response, file_name, failed_request):
    """
    Function to log the response and track the failed requests
    :param response: Response to an api request using 'requests' module
    :param failed_request: list of failed requests
    :param file_name: current file
    :return: appends file name to the failed_request if response status is not valid
    """
    if response.status_code not in [200, 202, 204]:
        logging.error("'{}' deployment failed ({}): {}".format(file_name,
                                                               response.status_code,
                                                               response.text if len(
                                                                   response.text) > 0 else response.reason
                                                               ))
        failed_request.append(file_name)
    else:
        logging.info("'{}' deployment succeeded".format(file_name))
    return failed_request


def get_profile_properties_body(user_api_response):
    """
    For profile-properties, read the source config and convert it to a specific format
    template directory path: scripts/deployment/templates/profile-property.j2
    :param user_api_response: source config dictionary
    :return: updated configuration
    """
    profile_context = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    profile_template = profile_context.get_template(PROFILE_PROPERTY_TEMPLATE_FILE)
    profile_mappings = user_api_response.get("user_attributes")
    content_data = dict()
    for mapping in profile_mappings:
        profile_name = mapping.get("name")
        mapping_key = update_key_mapping(mapping)
        if not mapping_key:
            logging.info("Profile '{}' is of 'map' type, hence skipping it".format(profile_name))
            continue
        payload = profile_template.render(mapping_key)
        content_data[mapping_key.get("profile_id")] = json.loads(payload)
    return {PROFILE_PROPERTIES_IDENTIFIER: content_data}


def get_scopes_body(domain_hash):
    """
    template directory path: scripts/deployment/templates/scopes.j2
    :param domain_hash: domain hash
    :return: updated configuration
    """
    scopes_context = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    scopes_template = scopes_context.get_template(SCOPES_TEMPLATE_FILE)
    template_mapping = {"domain_hash": domain_hash}
    payload = scopes_template.render(template_mapping)
    return {
        SCOPES_IDENTIFIER: {
            domain_hash: json.loads(payload)
        }
    }


def get_src_config(args):
    """
    Get the source config based on the different source types (UserAPI/ FileSystem)
    :param args: data dictionary
    :return: source config dictionary
    """
    if args.get(SRC_TYPE) == USER_API_SRC:
        config = read_config_user_api(args)
    elif args.get(SRC_TYPE) == FILE_SRC:
        config = read_config_file_system(args)

    # create body for profile-properties or scopes (using templates)
    if args.get(OBJECTS) == PROFILE_PROPERTIES_IDENTIFIER:
        config = get_profile_properties_body(config)
    elif args.get(OBJECTS) == SCOPES_IDENTIFIER:
        config = get_scopes_body(args.get(DOMAINS))

    return config


def deploy_objects(domain_hash, args):
    """
    Function to deploy profiles
    :param domain_hash: domain to deploy objects for
    :param args: data dictionary
    :return: list of failed components
    """
    env = args.get(ENVIRONMENT)
    endpoint = args.get(TGT_ENDPOINT)
    url = "{base_url}/{endpoint}".format(
        base_url=UNOMI_LOCALHOST if env == "local" else UNOMI_URL.format(env=env, domain_hash=domain_hash),
        endpoint=endpoint)
    try:
        config = get_src_config(args)
    except Exception as e:
        return [str(e)]

    # filter the config if needed
    init_objects = list(map(lambda x: x.strip(), args.get(SCRIPTS).split(",")))
    filtered_conf = get_filtered_config(args, config, init_objects)
    valid_objects = list(filtered_conf.keys()) if args.get(SCRIPTS) == ALL_IDENTIFIER else init_objects
    failed_request = []
    for obj in filtered_conf.keys():
        logging.info("'{}' deployment started".format(obj))
        response = call_unomi_api(url, filtered_conf.get(obj))
        valid_objects.remove(obj)
        failed_request = log_response(response, obj, failed_request)

    if len(valid_objects) > 0:
        failed_request.append(f"\'{','.join(valid_objects)}\' objects not found")
    return failed_request
