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
from langchain.vectorstores import OpenSearchVectorSearch

from opensearchpy import RequestsHttpConnection
from requests_aws4auth import AWS4Auth

service = 'aoss'
region = "us-east-1"
                    
bedrock_model_id = "ai21.j2-ultra-v1"
bedrock_embedding_model_id = "amazon.titan-embed-text-v1"

ssm = boto3.client('ssm')
endpoint = ssm.get_parameter(Name='/opensearch/serverless/endpoint')["Parameter"]["Value"]

def handler(event, context):
  print('received event:')
  print(event)

  # The Bedrock Runtime client, used to invoke the AI21Labs Jurassic model
  bedrock_client = get_bedrock_runtime_client(region)
    
  # The Bedrock invokation of the model
  bedrock_llm = get_bedrock_llm(bedrock_client, bedrock_model_id)
  
  # The Bedrock Embedding client, used to invoke the Amazon Titan embedding time
  bedrock_embeddings_client = get_bebdrock_embedding_client(bedrock_client, bedrock_embedding_model_id)
    

  opensearch_vector_search_client = create_opensearch_vector_search_client(bedrock_embeddings_client)
  

  documents = [
    Document(
        page_content="Antonio is an AWS Community Builder"
    ),
    Document(
        page_content="You are a bot helping speakers in public talks"
    )
  ]
  
  print("before add_documents ======>")
  opensearch_vector_search_client.add_documents(documents)
  print("after add_documents ======>")
  
  # Query the vector store
  query = "who is Antonio?"
  results = opensearch_vector_search_client.similarity_search(query)
  
  print("DOCUMENTS results ======>")
  print(results)
  
  
  
  prompt_template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer. don't include harmful content

  {context}

  Question: {question}
  Answer:"""
  PROMPT = PromptTemplate(
      template=prompt_template, input_variables=["context", "question"]
  )
  
  print(f"Starting the chain with KNN similarity using OpenSearch, Bedrock FM {bedrock_model_id}, and Bedrock embeddings with {bedrock_embedding_model_id}")
  qa = RetrievalQA.from_chain_type(llm=bedrock_llm, 
                                   chain_type="stuff", 
                                   retriever=opensearch_vector_search_client.as_retriever(),
                                   return_source_documents=True,
                                   chain_type_kwargs={"prompt": PROMPT, "verbose": True},
                                   verbose=True)
  
  response = qa(query, return_only_outputs=False)
  
  print("This are the similar documents from OpenSearch based on the provided query")
  source_documents = response.get('source_documents')
  print("response ===>")
  print(response)
  
  return {
      'statusCode': 200,
      'headers': {
          'Access-Control-Allow-Headers': '*',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
      },
      'body': json.dumps({ "Answer": response.get('result') })
  }
  
def get_bebdrock_embedding_client(bedrock_client, bedrock_embedding_model_id):
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
  message_history = DynamoDBChatMessageHistory(table_name="memories-dev", session_id="1")
  
  return ConversationBufferMemory(
    memory_key="history", chat_memory=message_history, return_messages=True,ai_prefix="A",human_prefix="H",
    input_key="question"
  )

def create_opensearch_vector_search_client(bedrock_embeddings_client):
    
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                   region, service, session_token=credentials.token)
                   
    docsearch = OpenSearchVectorSearch(
        index_name="ix_documents",
        embedding_function=bedrock_embeddings_client,
        opensearch_url=endpoint,
        http_auth=awsauth,
        is_aoss=True,
        timeout = 300,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    

    return docsearch

    


