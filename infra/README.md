# Deployment

## Directory Structure
```
infra/
├── README_new.md
├── k8s
└── scripts
```

## k8s
`k8s` directory acts as a root for all the Kubernetes manifests.

### Directory Structure
```
k8s/
├── argocd
└── kustomize
```

### argocd
`argocd` directory contains all the [Argo CD](https://argo-cd.readthedocs.io/en/stable/) application manifests.
Each manifest represents an ArgoCD application. Each application corresponds to a single Unomi cluster. 

When an application manifest is added to the corresponding environment directory in the `argocd` directory shown below, 
argo cd notices the change and applies(deploy if domain is added for the first time/modify if the configuration is changed) 
to the cluster.
#### Directory Structure
```
argocd/
├── prod-ap       
├── prod-eu
├── prod-us
└── staging                                    # contains all the argo cd application manifests for an environment
    ├── child-applications                     # contains the argo cd application manifests for all the domains.
    │   ├── 162537903.yaml
    │   ├── 43081656.yaml
    │   └── ingress.yaml
    └── root-application                       # contains the argo cd application manifest for maintaining all the applications defined in ../child-applicaitons/ directory
        └── unomi_application.yaml
```

Each environment has two additional directories 
1. child-applications
2. root-application

`child-applications` directory contains all the argo cd application manifests for each application that is to be deployed in the cluster - mainly unomi cluster for a domain and the corresponding ingress.

`root-application` directory contains the argo cd application that maintains all the applications defined in the `child-applications` directory. This follows the commonly used argo cd deployment pattern - [app of apps](https://argo-cd.readthedocs.io/en/stable/operator-manual/cluster-bootstrapping/#app-of-apps-pattern).


### kustomize
kustomize directory contains all the manifests required for deployment. 
These manifests are maintained using kustomize tool and follow the directory structure specified [here](https://github.com/kubernetes-sigs/kustomize/blob/master/examples/helloWorld/README.md). 

#### Directory structure
```
kustomize/
├── base                                       # contains all the common configuration
│   ├── prod-ap-root
│   ├── prod-eu-root
│   ├── prod-us-root
│   ├── root                                   # contains all the configuration that is common across environments and domains
│   │   ├── deployment.yaml
│   │   ├── kustomization.yaml
│   │   └── service.yaml
│   └── staging-root                           # contains all the configuration that is common across all the domains in an evironment
│       └── kustomization.yaml
└── overlays                                   # contains all the specific configuration. 
    ├── prod-ap
    ├── prod-eu
    ├── prod-us
    └── staging                                # contains all the domain specific configuration for an environment
        ├── 162537903
        │   └── kustomization.yaml
        ├── 43081656
        │   └── kustomization.yaml
        └── ingress
            ├── ingress.yaml
            └── kustomization.yaml
```

## scripts
`scripts` directory contains the scripts for adding new kubernetes manifests for a domain.

### Directory Structure
```
scripts/
├── add_domain.py                              # script to add all the required configuration files for a new domain
└── templates                                  # contains all the templates for a domain
```

`add_domain.py` script creates configuration files for a domain when added for the first time.
#### Usage
```shell
cd infra/scripts
python add_domain.py <env> <domain_hash> <git_branch> <region>
```
**NOTE**:\
valid values for env - `staging`, `prod`, `prod`, `prod`\
valid values for region - `us`, `eu`, `ap`
