import json
import boto3

bedrock = boto3.client(
    service_name='bedrock', 
    region_name='us-east-1'
)
  
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime', 
    region_name='us-east-1'
)

def handler(event, context):
  print('received event:')
  print(event)
  
  print(boto3.__version__)
   

  foundation_models = bedrock.list_foundation_models()
  
 
  matching_model = next((model for model in  foundation_models["modelSummaries"] if model.get("modelName") == "Jurassic-2 Ultra"), None)


  print("Matching model")
  print(matching_model)
   

  accept = 'application/json'
  contentType = 'application/json'
  
  prompt = json.loads(event.get("body")).get("input").get("question")


  body = json.dumps(
      {"prompt": prompt, 
       "maxTokens": 200,
       "temperature": 0.7,
       "topP": 1,
      }
  )
  
  response = bedrock_runtime.invoke_model(
      body=body, 
  	modelId=matching_model["modelId"], 
  	accept=accept, 
  	contentType=contentType
  )

  response_body = json.loads(response.get('body').read())
  answer = response_body.get('completions')[0].get('data').get('text')
  
  return {
      'statusCode': 200,
      'headers': {
          'Access-Control-Allow-Headers': '*',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
      },
      'body': json.dumps({ "Answer": answer })
  }