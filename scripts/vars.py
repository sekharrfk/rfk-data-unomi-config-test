import os

WORKING_DIR = os.getcwd()  # Better way to access this location. Shall we copy schema and rules to base directory

LOGGING_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

UNOMI_URL = "https://unomi-pub.{env}.rfksrv.com/{domain_hash}/cxs"
UNOMI_LOCALHOST = "http://localhost:8181/cxs"
KARAF_USER = "karaf"
KARAF_PASS = "karaf"
REQUEST_HEADERS = {"Content-Type": "application/json"}

UNOMI_SCHEMA_ENDPOINT = "jsonSchema"
UNOMI_RULE_ENDPOINT = "rules"
UNOMI_PROFILE_ENDPOINT = "profiles/properties"
UNOMI_SCOPE_ENDPOINT = "scopes"
UNOMI_DATATYPE_MAPPING = {
                            "map": None,
                            "int": "integer",
                            "double": "float",
                            "bool": "boolean",
                            "datetime": "date"
                        }

USER_API_URL = "https://data-user-api.{env}.rfksrv.com/v1/config"
USER_API_SCHEMA_ENDPOINT = "/schemas"
USER_ATTRIBUTES_ENDPOINT = "/user-attributes"

RULES_DIR = "scripts/rules"
TEMPLATES_DIR = "scripts/templates/"
PROFILE_PROPERTY_TEMPLATE_FILE = "profile-property.j2"
SCOPES_TEMPLATE_FILE = "scopes.j2"

ALL_IDENTIFIER = "all"
DEFAULT_MERGE_STRATEGY = "mostRecentMergeStrategy"

ENVIRONMENT = "environment"
OBJECTS = "objects"
SCRIPTS = "scripts"
DOMAINS = "domains"
SRC_PATH = "src_path"
TGT_ENDPOINT = "tgt_endpoint"
SRC_TYPE = "src_type"

USER_API_SRC = "userAPI"
FILE_SRC = "fileSystem"

SCHEMA_IDENTIFIER = "schemas"
RULE_IDENTIFIER = "rules"
SCOPES_IDENTIFIER = "scopes"
PROFILE_PROPERTIES_IDENTIFIER = "profile-properties"
VALID_OBJECTS_LIST = [SCHEMA_IDENTIFIER, RULE_IDENTIFIER, PROFILE_PROPERTIES_IDENTIFIER, SCOPES_IDENTIFIER]

VALID_STATUS = "valid"
INVALID_STATUS = "invalid"

AUTH_TOKEN = "auth_token"
API_KEY_HEADER = 'x-api-key'
