# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

AWS CDK (Python) infrastructure for a BreezyConf demo/presentation: a VPC, an EKS cluster,
cluster add-ons, and the dependencies of a "Mysfits" demo application. Infra lives in its own
repo, deliberately decoupled from the application code that is built and deployed separately
(the app is delivered onto the cluster by ArgoCD, which this repo installs).

There is no CI configuration and no linter config in the repo; `cdk` itself is the main tool.

## Commands

Environment setup (the CDK CLI must be installed separately per AWS docs):

```
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirements-dev.txt   # pytest, for the test dir
aws sso login                                    # account uses IAM Identity Center
```

Synth / diff / deploy — stacks must be deployed in dependency order, since each passes
constructs to the next:

```
cdk synth
cdk diff
cdk deploy VpcStack
cdk deploy EksStack
cdk deploy EksAddonStack
cdk deploy AppStack
```

Tests: `python3 -m pytest`, single test: `python3 -m pytest tests/unit/test_breezyconf_infra_stack.py::test_sqs_queue_created`.
Note the only test file is the unmodified `cdk init` template and imports
`breezyconf_infra.breezyconf_infra_stack`, a module that does not exist — so the suite
currently fails at collection. Fix or replace it (with `aws_cdk.assertions.Template`
assertions against the real stacks) rather than assuming the suite is meant to pass as-is.

Post-deploy kubectl access:

```
aws eks update-kubeconfig --name breezyconf-cluster
kubectl config use-context arn:aws:eks:eu-west-1:ACCOUNT_ID:cluster/breezyconf-cluster
```

## Architecture

`app.py` is the CDK app and the only place stacks are wired together. Cross-stack references
are passed as **construct objects through constructor arguments**, not via SSM/exports:

- `VpcStack` (`vpc_stack.py`) — exposes `self.vpc`. 10.11.0.0/16 across three hardcoded
  eu-west-1 AZs, `nat_gateways=1` (comment marks 3 for production). Tags public subnets with
  `kubernetes.io/role/elb` and private ones with `kubernetes.io/role/internal-elb`, which is
  what lets the AWS Load Balancer Controller discover subnets.
- `EksStack` (`eks_stack.py`) — consumes `vpc`, exposes `self.cluster`. EKS 1.30, nodes in
  `PRIVATE_WITH_EGRESS` subnets, `default_capacity=0` with an explicit `t3.large` AL2023
  nodegroup (`breezyconf-ng2`, 3–6 nodes). `authentication_mode=API_AND_CONFIG_MAP` plus
  `grant_access` for a hardcoded IAM Identity Center SSO role ARN. Also creates the private ECR
  repo (immutable tags, scan on push) and an IAM **user** whose credentials GitHub Actions uses
  to push images — a comment flags GitHub OIDC as the production approach.
  The kubectl Lambda layer version (`KubectlV30Layer`) must stay in step with
  `eks.KubernetesVersion`, and the layer package is pinned in `requirements.txt`.
- `EksAddonStack` (`eks_addon_stack.py`) — consumes `cluster`. Installs only the Helm charts
  needed before ArgoCD takes over deployments: ArgoCD itself and the AWS Load Balancer
  Controller. The controller chart expects a pre-existing service account named
  `aws-load-balancer-controller` in `kube-system` (`serviceAccount.create: "false"`).
- `AppStack` (`app_stack.py`) — consumes `vpc` and `cluster`. Application dependencies:
  DynamoDB `MysfitsTable` (partition key `MysfitId`, GSIs `LawChaosIndex` and `GoodEvilIndex`,
  provisioned 5/5), a private S3 bucket for the frontend, an internet-facing ALB with an
  IP-target-type target group **intended to be bound by the Load Balancer Controller via a
  `TargetGroupBinding`** (so nothing registers targets from CDK), and a CloudFront distribution
  with S3 as default origin and the ALB behind the `/mysfits*` behavior. IRSA is set up for
  service account `default/mysfits-sa`, which gets read/write on the table. Outputs the table
  name and the distribution domain.

## Conventions and known rough edges

- Account `200562504897` and region `eu-west-1` are hardcoded in `app.py`; change both when
  deploying elsewhere, and also `cdk.context.json` (cached AZ lookup keyed by account+region).
- `AppStack`'s IRSA trust policy hardcodes the OIDC provider ID in its `StringEquals`
  conditions (`TODO` in the file). That value changes whenever the cluster is recreated, so
  `AppStack` breaks after an `EksStack` replacement until it is updated; prefer deriving it
  from `cluster.open_id_connect_provider` / the created `service_account` when touching this.
- Demo-grade settings that are intentionally not production-ready, flagged by inline comments:
  `RemovalPolicy.DESTROY` + `auto_delete_objects` on the bucket and table, HTTP-only
  CloudFront→ALB origin, single NAT gateway, the IAM user for GitHub Actions. Keep the
  comments when editing; don't silently "harden" them.
- The `/mysfits*` behavior has `cache_policy=CACHING_DISABLED` commented out; dynamic API
  responses are cached by default as written.
- Stack variables in `app.py` shadow the imported class names (`VpcStack = VpcStack(...)`);
  a second instantiation of the same class in that file would fail.
