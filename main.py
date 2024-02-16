from elasticsearch import Elasticsearch
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from fastapi.middleware.cors import CORSMiddleware
import vertexai
from vertexai.language_models import TextGenerationModel, TextEmbeddingModel
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryMemory, ConversationTokenBufferMemory, CombinedMemory, ConversationBufferWindowMemory, ConversationBufferMemory
from fastapi import FastAPI, Request
import uvicorn
from langchain_openai import ChatOpenAI
from openai import OpenAI
openai_client = OpenAI()

from elastic_pipe import *
from prompt import *
from rag_pipe import *
from langchain_community.vectorstores import FAISS
from chat_memory import *

app = FastAPI()
origins = [
    "http://localhost:3000",  # Allow frontend origin
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specified origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

ELASTIC_PASSWORD = "YOUR ELASTIC PASSWORD"

CLOUD_ID = "YOUR ELASTIC CLOUD_ID"

client = Elasticsearch(
    cloud_id=CLOUD_ID,
    basic_auth=("elastic", ELASTIC_PASSWORD),
)

# Vertex AI credentials
KEY_PATH = "Credentials/rag-nick-7605da0e108b.json"
CREDENTIALS = Credentials.from_service_account_file(
    KEY_PATH,
    scopes = ['https://www.googleapis.com/auth/cloud-platform']
)
if CREDENTIALS.expired:
  CREDENTIALS.refresh(Request())
PROJECT_ID = "rag-nick"
REGION = "us-central1"
vertexai.init(project = PROJECT_ID,
              location = REGION,
              credentials = CREDENTIALS)
generation_model = TextGenerationModel.from_pretrained("text-bison@001")


# Langchain and Chroma and openai setup
vector_db = None
embedding = OpenAIEmbeddings()
llm_name = "gpt-3.5-turbo-0125"
openai.api_key  = os.environ['OPENAI_API_KEY']
embedding = OpenAIEmbeddings()
llm = ChatOpenAI(model_name=llm_name, temperature=0.2)

from langchain.chains import ConversationChain
from langchain.memory import (
    CombinedMemory,
    ConversationBufferMemory,
    ConversationSummaryMemory,
    ConversationBufferWindowMemory
)
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAI

conv_memory = ConversationBufferMemory(
    memory_key="chat_history_lines", input_key="input"
)

summary_memory = ConversationSummaryMemory(llm=OpenAI(), input_key="input")
# Combined
memory = CombinedMemory(memories=[conv_memory, summary_memory])
_DEFAULT_TEMPLATE = get_default_template()
PROMPT = PromptTemplate(
    input_variables=["history", "input", "chat_history_lines"],
    template=_DEFAULT_TEMPLATE,
)
llm = OpenAI(temperature=0.2)
conversation = ConversationChain(llm=llm, memory=memory, prompt=PROMPT)
#TODO: remove it as we will upload new links
vector_db = None


@app.post("/update-link")
async def update_link(request: Request):
    # load the input
    body = await request.json()
    url = body.get("url")
    if not url:
        return {"detail": "URL is required"}
    docs = data_loader(url)
    load_to_elastic(docs, client)
    global vector_db
    vector_db = vectorizor(docs, embedding)
    print("Link updated successfully")

    # refreshed
    global summary_memory
    summary_memory = ConversationSummaryMemory(llm=OpenAI(), input_key="input")
    global conv_memory
    conv_memory = ConversationBufferWindowMemory(memory_key="chat_history_lines", input_key="input", k=2)
    global memory
    memory = CombinedMemory(memories=[conv_memory, summary_memory])
    global _DEFAULT_TEMPLATE
    _DEFAULT_TEMPLATE = _DEFAULT_TEMPLATE
    global PROMPT
    PROMPT = PromptTemplate(input_variables=["history", "input", "chat_history_lines"],template=_DEFAULT_TEMPLATE)
    global conversation
    conversation = ConversationChain(llm=llm, memory=memory, prompt=PROMPT)

    return {"message": "Link updated successfully"}

@app.post("/chat")
async def chat(request: Request):
    # load the input
    body = await request.json()
    query = body.get("query")
    if not query:
        return {"detail": "Hello, how can I help you?"}
    
    question = query
    # check whether this query need to do a search or chathistory can answer it
    # no_need = openai_client.chat.completions.create(model=llm_name, messages=check_no_need_search(query)).choices[0].message.content
    query_messages = query_rewriter(query)
    query = openai_client.chat.completions.create(model="gpt-4", messages=query_messages).choices[0].message.content
    resp = search(client, query)

    search_content = ""
    for i in range(min(3, resp["hits"]["total"]["value"])):
        search_content += resp["hits"]["hits"][i]["_source"]['content'] + "```"

    llm_processed = openai_client.chat.completions.create(model=llm_name, messages=get_summary_messages(search_content[:10000])).choices[0].message.content

        # using vertex ai model
        # vertexiai_output = generation_model.predict(prompt=get_summary(resp["hits"]["hits"][0]["_source"]['content']), temperature=0).text

        # the retrievd information from Chroma
    retrieval = vector_db.similarity_search_with_score(question)
    
    # ranker
    top1, top1_score = retrieval[0]
    top2, top2_score = retrieval[1]
    top3, top3_score = retrieval[2]

    # print(top1_score, top2_score, top3_score)

    cutof = 0.5
    top_ranked = ""
    if top1_score < cutof:
        top_ranked += top1.page_content + "```"
    if top2_score < cutof:
        top_ranked += top2.page_content + "```"
    if top3_score < cutof:
        top_ranked += top3.page_content + "```"

    # top_ranked = top1.page_content + "```" + top2.page_content + "```" + top3.page_content
    retrival_result = openai_client.chat.completions.create(model=llm_name, messages=get_summary_messages(top_ranked[:10000])).choices[0].message.content

    # TODO: rewrite this, not use langchain module, use openai directly, context is in the assistant role, prompt is the user role,
    # System: You are a helpful technical assistant, use the context to answer to the user's question.
    # prompt = add_context_history(query, llm_processed, retrival_result, chat_memory.get_summary())
    # response = openai_client.chat.completions.create(model=llm_name, messages=prompt).choices[0].message.content
    # chat_memory.save_context(query, response)

    question_with_context = add_context(llm_processed, retrival_result, question)
    answer = conversation.predict(input = question_with_context)

    # remove potential AI prefix
    # print(answer)
    if answer[:3] == "AI:":
        answer = answer[4:]
        # print(answer)
    
    return {
        "rewrited_query" : query,
        "elastic_pipeline_output" : llm_processed,
        "retrieval_pipeline_output" : retrival_result,
        # "vertex_pipeline_output" : vertexiai_output,
        "response" : answer
    }

#TODO: Make conversation memory myself with openai call, 2. add a spinner, 3. Remove elastic search and add scores


if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
