import os
import json
import boto3
from langchain.llms.bedrock import Bedrock
from langchain.schema import Document
from langchain.chains import ConversationChain
from langchain.memory.chat_message_histories import DynamoDBChatMessageHistory
from langchain.vectorstores import OpenSearchVectorSearch
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain.embeddings import BedrockEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain

from opensearchpy import RequestsHttpConnection
from requests_aws4auth import AWS4Auth

service = 'aoss'
region = os.environ.get('REGION')  
index_name = os.environ.get('INDEX_NAME')        

bedrock_model_id = "ai21.j2-ultra-v1"
bedrock_embedding_model_id = "amazon.titan-embed-text-v1"

ssm = boto3.client('ssm')
endpoint = ssm.get_parameter(Name='/opensearch/serverless/endpoint')["Parameter"]["Value"]

def handler(event, context):
  print('received event:')
  print(event)
  
  # The question input of the end user
  question = json.loads(event.get("body")).get("input").get("question")
  
  # The Cognito Identity, used to associate past conversations for the logged user
  identity_id = json.loads(event.get("body")).get("input").get("identityId")

  # The Bedrock Runtime client, used to invoke the AI21Labs Jurassic model
  bedrock_client = get_bedrock_runtime_client(region)
    
  # The Bedrock invocation of the model
  bedrock_llm = get_bedrock_llm(bedrock_client, bedrock_model_id)
  
  # The Bedrock Embedding client, used to invoke the Amazon Titan embedding model
  bedrock_embeddings_client = get_bedrock_embedding_client(bedrock_client, bedrock_embedding_model_id)
    
  # 1) The past interaction with the user, aka memories
  memory = get_memory_from_dynamo(identity_id)
  
  # 2) Initialize the Vector database hosting all knowledge documents
  opensearch_vector_search_client = create_opensearch_vector_search_client(bedrock_embeddings_client)
  
  # 3) Build prompt to be used by Langchain chain
  PROMPT = build_prompt_template()
    
  # 4) The Langchain mergin LLMs, Vector database and memory, if provided  
  qa = RetrievalQA.from_chain_type(
    llm=bedrock_llm, 
    chain_type="stuff", 
    retriever=opensearch_vector_search_client.as_retriever(),
    return_source_documents=False,
    chain_type_kwargs={"prompt": PROMPT, "verbose": True},
    memory= memory,
    verbose=True
  )
    
  # The response may contain a few information, such as source documents if needed. 
  # In this case we are interested in the LLM reply, aka the result
  response = qa(question, return_only_outputs=False)
  answer = response.get('result')      
    
  print(f"The answer from Bedrock {bedrock_model_id} is: {response.get('result')}")
  
  return {
      'statusCode': 200,
      'headers': {
          'Access-Control-Allow-Headers': '*',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
      },
      'body': json.dumps({ "Answer": answer })
  }
  
def get_bedrock_embedding_client(bedrock_client, bedrock_embedding_model_id):
    bedrock_embeddings_client = BedrockEmbeddings(
        client=bedrock_client,
        model_id=bedrock_embedding_model_id)
    return bedrock_embeddings_client
    
def get_bedrock_runtime_client(region):
    bedrock_client = boto3.client("bedrock-runtime", region_name=region)
    return bedrock_client
    
def get_bedrock_llm(bedrock_client, model_version_id):
    
    model_kwargs =  {
        "maxTokens": 1024, 
        "temperature": 0.8, 
        "topP": 1
    }
    
    bedrock_llm = Bedrock(
        model_id=model_version_id, 
        client=bedrock_client,
        model_kwargs=model_kwargs
    )
    
    return bedrock_llm

def get_memory_from_dynamo(session_id):
  message_history = DynamoDBChatMessageHistory(table_name="memories-dev", session_id=session_id)
  
  return ConversationBufferMemory(
    memory_key="history", 
    chat_memory=message_history, 
    return_messages=True,
    ai_prefix="A",
    human_prefix="H"
  )

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

    
def build_prompt_template():
  prompt_template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer. don't include harmful content

    {context}

    Question: {question}
    Answer:"""
    
  return PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
  )

