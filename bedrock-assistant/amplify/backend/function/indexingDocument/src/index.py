import json
import boto3
import os
from urllib.parse import unquote
from langchain.schema import Document
from opensearchpy import OpenSearch, RequestsHttpConnection, exceptions
from requests_aws4auth import AWS4Auth
from langchain.vectorstores import OpenSearchVectorSearch
from langchain.embeddings import BedrockEmbeddings

service = "aoss"
region = os.environ.get('REGION')  
index_name = os.environ.get('INDEX_NAME') # Index used to store documents
bedrock_embedding_model_id = "amazon.titan-embed-text-v1"

# SSM Boto client used to fetch the OpenSearch collection generated from CDK
ssm = boto3.client('ssm')
endpoint = ssm.get_parameter(Name='/opensearch/serverless/endpoint')["Parameter"]["Value"]

def handler(event, context):
  
  s3_key = unquote(event["Records"][0]["s3"]["object"]["key"]);
  bucket_name = event["Records"][0]["s3"]["bucket"]["name"];

  print(event)
  print(s3_key)
  
  try:
        # Retrieve S3 document content
        response = boto3.client('s3').get_object(Bucket=bucket_name, Key=s3_key)
        content = response['Body'].read().decode('utf-8')

        bedrock_client = get_bedrock_runtime_client(region)
        
        bedrock_embeddings_client = get_bebdrock_embedding_client(bedrock_client, bedrock_embedding_model_id)
        
        opensearch_vector_search_client = create_opensearch_vector_search_client(bedrock_embeddings_client)
  
        documents = [
            Document(
                page_content=content
            )
        ]
          
        print("before add_documents ======>")
        opensearch_vector_search_client.add_documents(documents)
        print("after add_documents ======>")
       
  except Exception as e:
        print(f"An error occurred: {e}")
        return None
        
  return {
      'statusCode': 200,
      'headers': {
          'Access-Control-Allow-Headers': '*',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
      },
      'body': json.dumps("Ok")
  }
  
def create_opensearch_vector_search_client(embedding_function):
    
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                   region, service, session_token=credentials.token)
      
    docsearch = OpenSearchVectorSearch(
        index_name=index_name,
        embedding_function=embedding_function,
        opensearch_url=endpoint,
        http_auth=awsauth,
        is_aoss=True,
        timeout = 300,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    
    return docsearch
    
def get_bedrock_runtime_client(region):
    bedrock_client = boto3.client("bedrock-runtime", region_name=region)
    return bedrock_client
    
def get_bebdrock_embedding_client(bedrock_client, bedrock_embedding_model_id):
    bedrock_embeddings_client = BedrockEmbeddings(
        client=bedrock_client,
        model_id=bedrock_embedding_model_id)
    return bedrock_embeddings_client
