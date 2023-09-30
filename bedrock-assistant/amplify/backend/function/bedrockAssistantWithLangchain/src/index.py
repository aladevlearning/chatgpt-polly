import json
import boto3
from langchain.document_loaders import S3DirectoryLoader
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import Bedrock

bedrock = boto3.client(
    service_name='bedrock', 
    region_name='us-east-1'
)
  
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime', 
    region_name='us-east-1'
)

bucket_name = "bedrockassistantd9ae4478d21f46f99c63703086a936a111837-dev"

s3_client = boto3.client('s3')


def handler(event, context):
  print('received event:')
  print(event)
  
  #corpus = find_s3_corpus(event)

  identity_id = json.loads(event.get("body")).get("input").get("identityId")
  
  loader = S3DirectoryLoader(bucket_name, prefix="private/" + identity_id)
  input_documents = loader.load()

  foundation_models = bedrock.list_foundation_models()
  print(foundation_models)
  
  matching_model = next((model for model in  foundation_models["modelSummaries"] if model.get("modelName") == "Jurassic-2 Ultra"), None)


  print("Matching model: ")
  print(matching_model)
   
  llm = Bedrock(model_id=matching_model.get("modelId"))


  prompt = json.loads(event.get("body")).get("input").get("question")

  
  chain = load_qa_chain(llm, chain_type="stuff")
  

  output = chain.run(input_documents=input_documents, question=prompt)

  
  return {
      'statusCode': 200,
      'headers': {
          'Access-Control-Allow-Headers': '*',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
      },
      'body': json.dumps({ "Answer": output })
  }

  
def find_s3_corpus(event):
  identity_id = json.loads(event.get("body")).get("input").get("identityId")
  
  response = s3_client.list_objects_v2(Bucket=bucket_name)

  corpus = ""

  for s3_object in response.get('Contents', []):
      print("Key: ", s3_object['Key'])
      if s3_object['Key'] and s3_object['Key'].startswith(f"private/{identity_id}"):
          object_response = s3_client.get_object(Bucket=bucket_name, Key=s3_object['Key'])
          corpus += f"{object_response['Body'].read().decode('utf-8')} "
  
  print("Corpus data: ", corpus if corpus else 'N/A')
  return corpus
