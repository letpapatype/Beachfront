import { Construct } from 'constructs';
import { App, TerraformStack } from 'cdktf';
import {
    AwsProvider,
    ApiGatewayAccount,
    ApiGatewayDeployment,
    ApiGatewayIntegration,
    ApiGatewayMethod,
    ApiGatewayResource,
    ApiGatewayRestApi,
    CloudwatchLogGroup,
    DataAwsEcrRepository,
    IamRole,
    IamRolePolicyAttachment,
    LambdaFunction,
    LambdaPermission,
} from './.gen/providers/aws';

class MyStack extends TerraformStack {
    constructor(scope: Construct, name: string) {
        super(scope, name);

        const region = 'us-west-2'; // Replace with your desired region

        new AwsProvider(this, 'aws', {
            region,
        });

        // reference an existing container repository
        const ecrRepository = new DataAwsEcrRepository(this, 'example', {
            name: 'example',
        });

        const lambdaRole = new IamRole(this, 'lambda', {
            name: 'lambda',
            assumeRolePolicy: JSON.stringify({
                Version: '2012-10-17',
                Statement: [
                    {
                        Action: 'sts:AssumeRole',
                        Effect: 'Allow',
                        Principal: {
                            Service: 'lambda.amazonaws.com',
                        },
                    },
                ],
            }),
        });

        const lambdaRolePolicyAttachment = new IamRolePolicyAttachment(
            this,
            'lambda',
            {
                policyArn:
                    'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                role: lambdaRole.name,
                dependsOn: [lambdaRole],
            }
        );

        const lambdaFunction = new LambdaFunction(this, 'example', {
            functionName: 'example',
            role: lambdaRole.arn,
            handler: 'index.handler',
            runtime: 'provided.al2',
            timeout: 10,
            imageUri: ecrRepository.repositoryUrl,
            dependsOn: [lambdaRole],
            environment: [
                {
                    variables: {
                        FOO: 'bar',
                    },
                },
            ],
        });

        const apiGatewayRestApi = new ApiGatewayRestApi(this, 'example', {
            name: 'example',
        });

        const apiGatewayAccount = new ApiGatewayAccount(this, 'example', {
            cloudwatchRoleArn: lambdaRole.arn,
        });

        const apiGatewayResource = new ApiGatewayResource(this, 'example', {
            restApiId: apiGatewayRestApi.id,
            parentId: apiGatewayRestApi.rootResourceId,
            pathPart: 'example',
        });

        const apiGatewayMethod = new ApiGatewayMethod(this, 'example', {
            restApiId: apiGatewayRestApi.id,
            resourceId: apiGatewayResource.id,
            httpMethod: 'GET',
            authorization: 'NONE',
        });

        const apiGatewayIntegration = new ApiGatewayIntegration(this, 'example', {
            restApiId: apiGatewayRestApi.id,
            resourceId: apiGatewayResource.id,
            httpMethod: apiGatewayMethod.httpMethod,
            type: 'AWS_PROXY',
            uri: lambdaFunction.invokeArn,
        });

        const apiGatewayDeployment = new ApiGatewayDeployment(this, 'example', {
            restApiId: apiGatewayRestApi.id,
            stageName: 'prod',
            dependsOn: [apiGatewayIntegration],
        });

        const lambdaPermission = new LambdaPermission(this, 'example', {
            statementId: 'AllowAPIGatewayInvoke',
            action: 'lambda:InvokeFunction',
            functionName: lambdaFunction.functionName,
            principal: 'apigateway.amazonaws.com',
            sourceArn: `${apiGatewayDeployment.executionArn}/*/${apiGatewayMethod.httpMethod}/${apiGatewayResource.pathPart}`,
        });

        const cloudwatchLogGroup = new CloudwatchLogGroup(this, 'example', {
            name: `/aws/lambda/${lambdaFunction.functionName}`,
            retentionInDays: 14,
        });

        // Use the output URL of the API Gateway to update the Slack application's interactivity URL using the Slack Bolt TypeScript SDK
        // Please note that I cannot provide the code for this as it requires access to your specific Slack application credentials and settings
        const apiGatewayUrl = apiGatewayDeployment.invokeUrl;
        console.log(apiGatewayUrl);
    }
}

const app = new App();
new MyStack(app, 'my-stack');
app.synth();

// # take apiGatewayUrl and update Slack application's interactivity URL