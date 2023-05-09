const { OpenAI } = require("langchain/llms/openai");
const { TextLoader } = require("langchain/document_loaders/fs/text");
const { loadQAStuffChain } = require("langchain/chains");
//const { RecursiveCharacterTextSplitter }  = require("langchain/text_splitter");
//const { HNSWLib } = require("langchain/vectorstores");
//const { OpenAIEmbeddings }= require("langchain/embeddings");
const { S3Client, GetObjectCommand, ListObjectsV2Command} = require("@aws-sdk/client-s3");
const { Document } = require("langchain/document");
const { SSMClient, GetParameterCommand } = require("@aws-sdk/client-ssm");

const config = {
    region : "eu-west-1"
};


exports.handler = async (event) => {

    const ssmClient = new SSMClient(config);
    const command = new GetParameterCommand({
        Name: "/amplify/d3d42w42r85bwr/dev/AMPLIFY_askByVoice_OPENAI_API_KEY",
        WithDecryption: true
    });

    const {Parameter} = await ssmClient.send(command);

    let client = new S3Client(config);

    const identityId =  JSON.parse(event.body).input.identityId;


    const bucketName =  "amplify-chatgpt-documents222215-dev";

    const s3ObjectList = await client.send(new ListObjectsV2Command({
        Bucket: bucketName
    }));

    let corpus = "";

    for(const object of s3ObjectList.Contents) {
      console.log("Key: ", object.Key);
      if (object.Key && object.Key.startsWith(`private/${identityId}`)) {
        const response = await client.send(new GetObjectCommand({Bucket:bucketName,Key: object.Key}));
        corpus += `${await streamToString(response.Body)} `;
      }
    }

    console.log("Corpus data: ", corpus || 'N/A')
    const document = new Document({ pageContent: corpus });

    const question =  JSON.parse(event.body).input.question;

    const model = new OpenAI({ openAIApiKey: Parameter.Value, temperature: 0.9, max_tokens: 2048 });

    const chainA = loadQAStuffChain(model);
    const answer = await chainA.call({
        input_documents: [document],
        question: question
        }
    )

    return {
        statusCode: 200,
        headers: {
            "Access-Control-Allow-Headers" : "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
        body: JSON.stringify({ "Answer": answer.text })
    };
};

async function streamToString (stream) {
  const chunks = [];
  return new Promise((resolve, reject) => {
    stream.on('data', (chunk) => chunks.push(Buffer.from(chunk)));
    stream.on('error', (err) => reject(err));
    stream.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
  })
}