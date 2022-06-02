# How-to: Deploy Magma Orchestrator on AWS with Charmed Kubernetes

The goal of this document is to detail how to deploy Magma's Orchestrator on AWS with Charmed
Kubernetes. You will deploy charmed Kubernetes, bootstrap a Juju controller, deploy Magma Orchestrator and configure A
records.

### Pre-requisites

- Ubuntu 20.04 machine with internet access
- A public domain

## 1. Set up your management environment

From a Ubuntu 20.04 machine, install the following tools:

- [Juju](https://juju.is/docs/olm/installing-juju)
- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

Log in to your AWS account via the AWS CLI tool (instructions
[here](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html)).

## 2. Deploy Charmed Kubernetes on AWS using Juju

Follow this [guide](https://ubuntu.com/kubernetes/docs/aws-integration) to deploy charmed Kubernetes
on AWS.

Once you have access to the newly created Kubernetes cluster using `kubectl`, add this new k8s 
endpoint and credentials to Juju:

```bash
juju add-k8s <controller name>
```

Replace `<controller name>` with the name you want for the Juju controller.

Bootstrap the new Kubernetes controller:

```bash
juju bootstrap <controller name>
```

Create a new model (namespace):

```bash
juju add-model <model name>
```

Replace `<model name>` with the Kubernetes namespace you want for the Magma deployment.

## 3. Deploy charmed magma orchestrator

Create an `overlay.yaml` file that contains the following:

```yaml
applications:
  orc8r-certifier:
    options:
      domain: <your domain name>
```

Replace `<your domain name>` with your domain name.

Deploy orchestrator:

```bash
juju deploy magma-orc8r --overlay overlay.yaml --trust --channel=edge
```

The deployment is completed when all services are in the `Active-Idle` state.

## 4. Import the admin operator HTTPS certificate

Retrieve the self-signed certificate:

```bash
juju scp --container="magma-orc8r-certifier" orc8r-certifier/0:/var/opt/magma/certs/..data/admin_operator.pfx admin_operator.pfx
```

> The default password to open the admin_operator.pfx file is `password123`. To choose a different 
> password, re-deploy orc8r-certifier with the `passphrase` juju config.

## 5. Create the orchestrator admin user

Create the user:

```bash
juju run-action orc8r-orchestrator/0 create-orchestrator-admin-user
```

## 6. Setup DNS

To configure Route53, on your Ubuntu machine clone the `charmed-magma` project:

```bash
git clone https://github.com/canonical/charmed-magma.git
```

Navigate to the `route53_integrator` directory and run the main script:

```bash
cd charmed-magma/orchestrator-bundle/tools/route53_integrator
pip3 install -r requirements.txt
python3 main.py --hosted_zone=<your domain> --namespace <your model>
```

Configure DNS records on your managed domain name to use the Route53 nameservers outputted by the
script.

## 7. Verify the deployment

Get the master organization's username and password:

```bash
juju run-action nms-magmalte/0 get-admin-credentials --wait
```

Confirm successful deployment by visiting `https://master.nms.<your domain>` and logging in
with the `admin-username` and `admin-password` outputted here.