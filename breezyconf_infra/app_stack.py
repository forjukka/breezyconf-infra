from aws_cdk import (
    RemovalPolicy,
    CfnOutput,
    Stack,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_eks as eks,
    aws_dynamodb as dynamodb,
    aws_s3_deployment as s3deploy,
)
from constructs import Construct

class AppStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.IVpc, cluster: eks.ICluster, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here


        # Create IAM role and Service Account so that the app can query its DynamoDB Table
        # TODO: switch hardcoded condition values to dynamic ones

        sa_role = iam.Role(self, "MysfitsRole",
            assumed_by=iam.WebIdentityPrincipal(
                cluster.open_id_connect_provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        "oidc.eks.eu-west-1.amazonaws.com/id/20C4F9A9C21E778A0306C74393AE5A98:aud": "sts.amazonaws.com",
                        "oidc.eks.eu-west-1.amazonaws.com/id/20C4F9A9C21E778A0306C74393AE5A98:sub": "system:serviceaccount:default:mysfits-sa"
                    }
                }
            )
        )

        # Create a Kubernetes service account and associate it with the IAM role
        service_account = cluster.add_service_account("MysfitsServiceAccount",
            name="mysfits-sa",
            namespace="default"
        )

        # S3 bucket for the frontend

        bucket = s3.Bucket(self, "MysfitsBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            auto_delete_objects=True,
            enforce_ssl=True,
            minimum_tls_version=1.2
        )

        # You can copy static content to the S3 bucket from CDK if
        # you don't want to use the shell script in this repo

        #s3deploy.BucketDeployment(self, "MysfitsDeployment",
        #    sources=[s3deploy.Source.asset("./web")],
        #    destination_bucket=bucket,
        #    retain_on_delete=False,
        #)

        # Create ALB for the application

        alb = elbv2.ApplicationLoadBalancer(self, "ALB",
            vpc=vpc,
            internet_facing=True
        )
        # This target group will be managed by the AWS Load Balancer Controller
        # https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.5/guide/targetgroupbinding/targetgroupbinding/

        target_group = elbv2.ApplicationTargetGroup(self, "TargetGroup",
            vpc=vpc,
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
            health_check=elbv2.HealthCheck(path="/",port="traffic-port")
        )
        listener = alb.add_listener("Listener",
            port=80,
            open=True,
            default_target_groups=[target_group]
        )

        # CloudFront in front of the static content bucket and the ALB that serves the application API

        distribution = cloudfront.Distribution(self, "MysfitsDistribution",
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(bucket),
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
            ),
            additional_behaviors={
                "/mysfits*": cloudfront.BehaviorOptions(
                    origin=origins.LoadBalancerV2Origin(alb,protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY), # switch to HTTPS in production
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                )
            }
        )

        # DynamoDB table for the application

        table = dynamodb.Table(self,
            "MysfitsTable",
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            partition_key=dynamodb.Attribute(name="MysfitId",type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PROVISIONED,
            read_capacity=5,
            write_capacity=5
        )
        table.add_global_secondary_index(
            index_name="LawChaosIndex",
            partition_key=dynamodb.Attribute(name="LawChaos",type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="MysfitId",type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
            read_capacity=5,
            write_capacity=5
        )
        table.add_global_secondary_index(
            index_name="GoodEvilIndex",
            partition_key=dynamodb.Attribute(name="GoodEvil",type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="MysfitId",type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
            read_capacity=5,
            write_capacity=5
        )

        # Grant the Mysfits IAM role access to the DynamoDB table
        table.grant_read_write_data(sa_role)

        table_output = CfnOutput(self,'DynamoTable',value=table.table_name)
        distribution_output = CfnOutput(self,'Distribution',value=distribution.distribution_domain_name)


