import json
import logging
import sys


def get_domain_mapping(file_name):
    with open(file_name) as f:
        ud = f.read()
    domain_mapping = json.loads(ud)
    return domain_mapping


def write_domain_mapping(file_name, unomi_domains):
    with open(file_name, 'w') as fp:
        json.dump(unomi_domains, fp, indent=4)


def main(domain_hash, all_domain_mapping_file, unomi_domain_mapping_file):
    all_domains = get_domain_mapping(all_domain_mapping_file)
    unomi_domains = get_domain_mapping(unomi_domain_mapping_file)

    # Check if the domain_hash is present in all domains file and if present, fetch the corresponding information and
    # add it to unomi domain mapping file
    if domain_hash in all_domains['domain_hash']:
        domain = all_domains['domain_hash'][domain_hash]
        unomi_domains['domain_hash'][domain_hash] = domain
    else:
        logging.error("No domain {domain_hash} found".format(domain_hash=domain_hash))

    write_domain_mapping(unomi_domain_mapping_file, unomi_domains)


if __name__ == '__main__':
    """
    Add a domain to unomi config file. This ensures that the events coming from this domain are not filtered out.
    """
    domain_hash = sys.argv[1]
    # Since we can't access msapi endpoint from github actions, we fetch the relevant information about domain from
    # existing domain_mapping file. Given domain_hash, we fetch all the relevant information like ckey, account,
    # and domain name.
    all_domain_mapping_file = sys.argv[2]
    unomi_domain_mapping_file = sys.argv[3]
    main(domain_hash, all_domain_mapping_file, unomi_domain_mapping_file)
