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

endpoint = "https://6hvwxeseal2dy8pby1y8.us-east-1.aoss.amazonaws.com"
service = 'aoss'
region = "us-east-1"
                    
bedrock_model_id = "ai21.j2-ultra-v1"
bedrock_embedding_model_id = "amazon.titan-embed-text-v1"

def handler(event, context):
  print('received event:')
  print(event)
  
  question = json.loads(event.get("body")).get("input").get("question")
  identity_id = json.loads(event.get("body")).get("input").get("identityId")

  bedrock_client = get_bedrock_runtime_client(region)
  bedrock_llm = get_bedrock_llm(bedrock_client, bedrock_model_id)
  bedrock_embeddings_client = create_langchain_vector_embedding_using_bedrock(bedrock_client, bedrock_embedding_model_id)
  memory = get_memory_from_dynamo(identity_id)
  
  prompt_template = """Use the following pieces of context to answer the question at the end, if provided.

    {context}

    Question: {question}
    Answer:"""
    
  PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
  )
    
  docs = [
    Document(
        page_content=question
    )
  ]

  opensearch_vector_search_client = create_opensearch_vector_search_client(docs, bedrock_embeddings_client)
  
  documents = opensearch_vector_search_client.similarity_search(question, k=5)

  print("DOCUMENTS ======>")
  print(documents)
  
  qa_chain = load_qa_chain(
    llm=bedrock_llm, 
    chain_type="stuff", 
    prompt=PROMPT
  )
  
    
  answer = qa_chain.run(input_documents=documents, question=question)
  
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
  
def get_memory_from_dynamo(session_id):
  message_history = DynamoDBChatMessageHistory(table_name="memories-dev", session_id="1")
  
  return ConversationBufferMemory(
    memory_key="history", chat_memory=message_history, return_messages=True,ai_prefix="A",human_prefix="H"
  )

def create_opensearch_vector_search_client(docs, embeddings):
    
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                   region, service, session_token=credentials.token)
                   

    docsearch = OpenSearchVectorSearch.from_documents(
        docs,
        embeddings,
        opensearch_url=endpoint,
        http_auth=awsauth,
        timeout = 300,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection,
        index_name="ix_documents"
    )

    return docsearch
    
def create_langchain_vector_embedding_using_bedrock(bedrock_client, bedrock_embedding_model_id):
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
        "temperature": 0, 
        "topP": 0.5, 
        "stopSequences": ["Human:"], 
        "countPenalty": {"scale": 0 }, 
        "presencePenalty": {"scale": 0 }, 
        "frequencyPenalty": {"scale": 0 } 
    }
    bedrock_llm = Bedrock(
        model_id=model_version_id, 
        client=bedrock_client,
        model_kwargs=model_kwargs
        )
    return bedrock_llm
    


