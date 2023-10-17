import * as cdk from 'aws-cdk-lib';
import * as AmplifyHelpers from '@aws-amplify/cli-extensibility-helper';
import { AmplifyDependentResourcesAttributes } from '../../types/amplify-dependent-resources-ref';
import { Construct } from 'constructs';
import * as ops from 'aws-cdk-lib/aws-opensearchserverless';
import * as ssm from 'aws-cdk-lib/aws-ssm';

export class cdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps, amplifyResourceProps?: AmplifyHelpers.AmplifyResourceProps) {
    super(scope, id, props);
    /* Do not remove - Amplify CLI automatically injects the current deployment environment in this input parameter */
    new cdk.CfnParameter(this, 'env', {
      type: 'String',
      description: 'Current Amplify CLI env name',
    });

    const amplifyProjectInfo = AmplifyHelpers.getProjectInfo();
    
    const collection = new ops.CfnCollection(this, `DocumentCollection-${amplifyProjectInfo.projectName}`, {
      name: 'document-collection',
      type: 'VECTORSEARCH',
    });
    
    // Encryption policy is needed in order for the collection to be created
    const encPolicy = new ops.CfnSecurityPolicy(this, `DocumentSecurityPolicy-${amplifyProjectInfo.projectName}`, {
      name: 'document-collection-policy',
      policy: '{"Rules":[{"ResourceType":"collection","Resource":["collection/document-collection"]}],"AWSOwnedKey":true}',
      type: 'encryption'
    });

    collection.addDependency(encPolicy);

    // Network policy is required so that the dashboard can be viewed!
    const netPolicy = new ops.CfnSecurityPolicy(this, `DocumentNetworkPolicy-${amplifyProjectInfo.projectName}`, {
      name: 'document-network-policy',
      policy: '[{"Rules":[{"ResourceType":"collection","Resource":["collection/document-collection"]}, {"ResourceType":"dashboard","Resource":["collection/document-collection"]}],"AllowFromPublic":true}]',
      type: 'network'
    });
    

    collection.addDependency(netPolicy);
    
    const accessPolicy = [
     {
        "Description": "Rule 1",
        "Rules":[
           {
              "ResourceType":"collection",
              "Resource":[
                 "collection/document-collection"
              ],
              "Permission":[
                 "aoss:*"
              ]
           },
           {
              "ResourceType":"index",
              "Resource":[
                 "index/document-collection/*"
              ],
              "Permission":[
                 "aoss:*"
              ]
           }
        ],
        "Principal":[
           "arn:aws:iam::663838754385:role/bedrockassistantLambdaRoledc0e45e1-dev",
           "arn:aws:iam::663838754385:role/bedrockassistantLambdaRolef56b9054-dev",
           "arn:aws:iam::663838754385:role/bedrockassistantLambdaRolea97c4145-dev",
           "arn:aws:iam::663838754385:user/alatech"
        ]
      }
    ]

    const cfnAccessPolicy = new ops.CfnAccessPolicy(this, `DocumentAccessPolicy-${amplifyProjectInfo.projectName}`, {
      name: 'document-access-policy',
      policy: JSON.stringify(accessPolicy),
      type: 'data'
    });
    
    collection.addDependency(cfnAccessPolicy);
    
    new cdk.CfnOutput(this, 'CollectionEndpoint', {
      value: collection.attrCollectionEndpoint,
    });
    
    new ssm.StringParameter(this, `OpenSearchParameter-${amplifyProjectInfo.projectName}`, {
      parameterName: "/opensearch/serverless/endpoint",
      description: "OpenSearch Serverless endpoint",
      stringValue: collection.attrCollectionEndpoint,
    });
    
  }
}