import json
import boto3
from urllib.parse import unquote
from opensearchpy import OpenSearch, RequestsHttpConnection, exceptions
from requests_aws4auth import AWS4Auth

endpoint = "iojcjjtuooek7hjf1uhh.us-east-1.aoss.amazonaws.com"
service = 'aoss'
region = "us-east-1"

credentials = boto3.Session().get_credentials()

awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                   region, service, session_token=credentials.token)
  
s3 = boto3.client('s3')

ops_client = OpenSearch(
        hosts=[{'host': endpoint, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300
    )
 
bedrock_client = boto3.client("bedrock-runtime", region_name=region)
bedrock_model_id = "ai21.j2-ultra-v1"
bedrock_embedding_model_id = "amazon.titan-embed-text-v1"

    
def handler(event, context):
  #print('received event:')
  #print(event)
  
  print("question ==========>")       
  question = json.loads(event.get("body")).get("input").get("question")
  print(question)
  embedding = get_vector_embedding(question)
  
  vector_query = {
                "size": 5,
                "query": {"knn": {"vector_field": {"vector": embedding, "k": 5}}}
            }
            
  response = ops_client.search(body=vector_query, index="ix_documents")
  
  context = ''
  for data in response["hits"]["hits"]:
      if context is None:
          context = data['_source']['text']
      else:
          context = context + ' ' + data['_source']['text']
     
  print("CONTEXT ==========>")                   
  print(context)

                
                  
  prompt = f""" You must answer this question"{question}".
                    If pertinent, use the following context information provided between ## when needed "
                            #{context}# 
                            """
  body = json.dumps(
   {
      "prompt": prompt, 
      "maxTokens": 200,
      "temperature": 0.7,
      "topP": 1,
   }
 )
 
  responseLlm = bedrock_client.invoke_model(
      body=body,
      modelId=bedrock_model_id,
      accept='application/json',
      contentType='application/json'
  )
  
  response_body = json.loads(responseLlm.get('body').read())

  answer = response_body.get('completions')[0].get('data').get('text')
  
  print("ANSWER ==========>")      
  print(answer)
  
  return {
      'statusCode': 200,
      'headers': {
          'Access-Control-Allow-Headers': '*',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
      },
      'body': json.dumps({ "Answer": answer })
  }
  
def get_vector_embedding(question):
 
    response = bedrock_client.invoke_model(
        body=json.dumps({"inputText": question}), 
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
                    "id": {"type": "integer"},
                    "text": {"type": "text"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 1536,
                    },
                }
            },
        }
        res = ops_client.indices.create(index, body=settings, ignore=[400])
        print(res)