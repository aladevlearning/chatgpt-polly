/*
Use the following code to retrieve configured secrets from SSM:

const aws = require('aws-sdk');

const { Parameters } = await (new aws.SSM())
  .getParameters({
    Names: ["OPENAI_API_KEY"].map(secretName => process.env[secretName]),
    WithDecryption: true,
  })
  .promise();

Parameters will be of the form { Name: 'secretName', Value: 'secretValue', ... }[]
*/
import { SSMClient, GetParameterCommand } from "@aws-sdk/client-ssm"; 
import { Configuration, OpenAIApi } from "openai";

const config = {
    region : "eu-west-1"
};

export const handler = async (event) => {

    const client = new SSMClient(config);
    const command = new GetParameterCommand({
        Name: "/amplify/d3d42w42r85bwr/dev/AMPLIFY_askByVoice_OPENAI_API_KEY",
        WithDecryption: true
    });

    const {Parameter} = await client.send(command);

    const configuration = new Configuration({
        apiKey: Parameter.Value,
    });
    

    const openai = new OpenAIApi(configuration);


    const completion = await openai.createCompletion({
        model: "text-davinci-003",
        prompt: JSON.parse(event.body).input.question,
        temperature: 0.6,
        echo: false,
        max_tokens: 2048
    });

    return {
        statusCode: 200,
        headers: {
            "Access-Control-Allow-Headers" : "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
        body: JSON.stringify({ "Answer": completion.data.choices[0].text }),
    }
};