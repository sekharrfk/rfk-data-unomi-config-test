import os
import sys

import jinja2
import yaml
from jinja2 import FileSystemLoader
from yaml import FullLoader


def write_to_file(file_name, rendered_template):
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    output_file = open(file_name, "w")
    output_file.write(rendered_template)
    output_file.close()


def add_kustomization(env, domain_hash):
    environment = jinja2.Environment(loader=FileSystemLoader("templates/"))
    template = environment.get_template("kustomization.j2")
    rendered_template = template.render(env=env, domain_hash=domain_hash)
    file_name = "../infra/k8s/kustomize/overlays/{env}/{domain_hash}/kustomization.yaml".format(env=env,
                                                                                          domain_hash=domain_hash)
    write_to_file(file_name, rendered_template)


def add_ingress(env, domain_hash):
    environment = jinja2.Environment(loader=FileSystemLoader("templates/"))
    template = environment.get_template("ingress.j2")
    # hack - If region is us, ignore the region suffix
    if 'us' in env:
        rendered_template = yaml.load(template.render(env=env.split('-')[0], domain_hash=domain_hash), FullLoader)
    else:
        rendered_template = yaml.load(template.render(env=env, domain_hash=domain_hash), FullLoader)

    file_name = "../infra/k8s/kustomize/overlays/{env}/ingress/ingress.yaml".format(env=env)
    input_file = open(file_name)
    ingress_file = yaml.load(input_file, Loader=FullLoader)
    ingress_file['spec']['rules'].append(rendered_template)

    out_file = file_name
    with open(out_file, 'w') as f:
        yaml.dump(ingress_file, f)


def add_argo_cd_application(env, domain_hash, branch):
    environment = jinja2.Environment(loader=FileSystemLoader("templates/"))
    template = environment.get_template("argocd_application.j2")
    rendered_template = template.render(env=env, domain_hash=domain_hash, branch=branch)
    file_name = "../infra/k8s/argocd/{env}/child-applications/{domain_hash}.yaml".format(env=env, domain_hash=domain_hash)
    os.makedirs(os.path.dirname("../infra/k8s/argocd/{env}/child-applications".format(env=env)), exist_ok=True)
    write_to_file(file_name, rendered_template)


def main(env, domain_hash, branch):
    add_kustomization(env, domain_hash)
    add_argo_cd_application(env, domain_hash, branch)
    add_ingress(env, domain_hash)


if __name__ == '__main__':
    env = sys.argv[1]
    domain_hash = sys.argv[2]
    branch = sys.argv[3]
    region = None
    if len(sys.argv) > 4:
        region = sys.argv[4]
    if env != 'staging':
        env = env + "-" + region
    main(env, domain_hash, branch)
