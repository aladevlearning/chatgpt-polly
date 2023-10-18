import json
import boto3
from urllib.parse import unquote
from opensearchpy import OpenSearch, RequestsHttpConnection, exceptions
from requests_aws4auth import AWS4Auth

service = 'aoss'
region = "us-east-1"

credentials = boto3.Session().get_credentials()

awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                   region, service, session_token=credentials.token)
                 
s3 = boto3.client('s3')
ssm = boto3.client('ssm')

endpoint = ssm.get_parameter(Name='/opensearch/endpoint')["Parameter"]["Value"].replace("https://", "")

ops_client = OpenSearch(
    hosts=[{'host': endpoint, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=300
)
 
bedrock_client = boto3.client("bedrock-runtime", region_name=region)
 
    
def handler(event, context):
  #print('received event:')
  #print(event)
  
  s3_key = unquote(event["Records"][0]["s3"]["object"]["key"]);
  bucket_name = event["Records"][0]["s3"]["bucket"]["name"];

  try:
        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        content = response['Body'].read().decode('utf-8')
        
        index = "ix_documents"
        
        embedding = get_vector_embedding(content, index, bedrock_client)

        create_index(index)
        print(f'Got an index, now posting')
        
        doc = {
          'vector_field' : embedding,
          'text': content
        }
            
        # Index the document
        responseIndex = ops_client.index(index, body=doc)
        print(f'Got a response')
        print(responseIndex)
        
        
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
      'body': json.dumps(responseIndex)
  }
  
def get_vector_embedding(text, name, bedrock_client):
  
    response = bedrock_client.invoke_model(
        body=json.dumps({ "inputText": text }), 
        modelId="amazon.titan-embed-text-v1", 
        accept="application/json", 
        contentType="application/json"
    )
    
    response_body = json.loads(response.get("body").read())
  
    return response_body.get("embedding")
    
def create_index(index) :
    print(f'In create index')
    if not ops_client.indices.exists(index):
    # Create indicies
        settings = {
            "settings": {
                "index": {
                    "knn": True,
                }
            },
            "mappings": {
                "properties": {
                    "text": {"type": "text"},
                    "vector_field": {
                        "type": "knn_vector",
                        "dimension": 1536,
                    },
                }
            },
        }
        res = ops_client.indices.create(index, body=settings, ignore=[400])
        print(res)