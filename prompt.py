
from langchain.prompts import PromptTemplate
def get_summary(search_content):
    # prompt = f"""
    #         Write a concise summary of the following text delimited by triple backquotes.
    #         Ignore anything that is not technical.
    #         Return your response in bullet points which covers the key points of the text.
    #         ```{search_content}```
    #         BULLET POINT SUMMARY:
    #         """
    
    prompt = f"""
            Write a concise summary of the following text.
            Ignore anything that is not technical.
            Return your response as a technical document that will help a developer understand the technology.
            ```{search_content}```
            Using aboved content deliminated by triple backquotes, write the technical summary.
            TECHNICAL SUMMARY:
            """
    return prompt


def get_summary_messages(content):
    messages = [
            {"role": "system", "content":
             """You are technical summarizor.
             Return your response as a technical document that will help a developer understand the technology.
             Ignore anything that is not technical.
             The content provided include multiple relevant tech docs, deliminated by triple backquotes.
             """
            },
            {"role": "user", "content": f"""
            Write a concise summary of the following text delimited by triple backquotes.
            ```{content}```
            TECHNICAL SUMMARY:
            """}
        ]
    return messages

def query_rewriter(query):
    messages=[
            {"role": "system", "content":
             """You are technical expert.
             Extract the technical term that are helpful for us to do key word search.
             Answer the question as a single string of keywords separated by space.
             For example if the question is "What is the difference between while loop and for loop?" you should answer "While loop for loop".
             If there is no technical term, return an empty string.
             """
            },
            {"role": "user", "content": f"""
            Extract from below question:
            ```{query}```
            Search query:
            """}
    ]
    return messages
    
def get_default_template():
    template = """
You are a technical assistant chatbot, you need to answer question based on the context.
The user does not know the context, you will need to answer the question to them in technical detail.
Below you will be provided with summary of the conversation the current conversation betwwen human and the chatbot deliminated by "###".
###
Summary of conversation:
{history}###
Current Conversation:
{chat_history_lines}###
Above are the summarized memory and current chat_history, given the following extracted parts of a long documents deliminated by "###" and a question, create a final answer to the question.
If the extracted parts are irrelevant or empty, try using the chat history to answer the question.
{input}
        """

    return template

def add_context(llm_processed, retrival_result, question):
    input = f"""
{llm_processed} ###
{retrival_result} ###
Human: {question}
AI: """
    return input


def check_no_need_search(question):
    messages = [
            {"role": "system", "content":
             """You are technical support.
             You will be provided with a question, and deterimine whether the question can be answered by the chat history or need to do a search in a database.
             Return "Yes" if the question can be answered by the chat history, otherwise return "No".
             Only return "Yes" or "No".
             """
            },
            {"role": "user", "content": f"""
            Can this question be answered by the chat history?
            ```{question}```
            """}
        ]
    return messages


def add_context_history(question, context_elastic, context_rag, summarized_memory):
    messages = [
            {"role": "system", "content":
             f"""
             You are a helpful technical assistant, you will answer user's question about a technical document.
             Answer user's question as you are explanaining to the person.
             If the information to answer the question is not in the context, say that you do not know.
             """
            },
            {"role" : "user", "content" : "What is the summary of the context of conversation"},
            {"role": "assistant", "content": summarized_memory},
            {"role": "user", "content": "What is the summary of the technical document relvant to the question?"},
            {"role": "assistant", "content": f"""
            There are two pieces of summary relevant to the question, separated by ###:
            {context_elastic} ### {context_rag}
            """},
            {"role": "user", "content": question}
        ]
    return messages
