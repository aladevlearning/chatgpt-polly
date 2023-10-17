import { AmplifyDDBResourceTemplate, AmplifyProjectInfo } from '@aws-amplify/cli-extensibility-helper';

export function override(resources: AmplifyDDBResourceTemplate, amplifyProjectInfo: AmplifyProjectInfo) {
    delete(resources.dynamoDBTable.provisionedThroughput)
    resources.dynamoDBTable.billingMode = "PAY_PER_REQUEST"
}
