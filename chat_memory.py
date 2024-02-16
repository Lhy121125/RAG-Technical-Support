"""
This is the chat memory class,
Langchain sucks, as it fials to provide multi-threading features
"""

def summarize_context(input, output, max_token, context, client):
    context = context if context != "" else "The human is asking a question and the AI is providing an answer."
    messages = [
            {"role": "system", "content": 
             f"""
                Your task is to generate a summary of the conversation history between a human and AI technical assistant.
                You will be provided with the human's input and the AI's response, as well as the previous context.
                Summary should not be more than {max_token} tokens.
             """
            },
            {"role": "user", "content": "What is the conversation context?"},
            {"role": "assistant", "content": context},
            {"role": "user", "content": input},
            {"role": "assistant", "content": output},
            {"role": "user", "content": f"Summarize the conversation history between the human and AI technical assistant with no more than {max_token} token."},
        ]
    
    summarization = client.chat.completions.create(model="gpt-3.5-turbo-0125", messages=messages).choices[0].message.content
    return summarization

class Chat_memory:
    def __init__(self, max_token, client) -> None:
        self.chat_history = []
        self.summary = ""
        self.max_token = max_token
        self.client = client

    def save_context(self, input, output):
        self.chat_history.append({
            "role": "user",
            "content": input,
        })
        self.chat_history.append({
            "role": "assistant",
            "content": output,
        })
        self.summary = summarize_context(input, output, self.max_token, self.summary, self.client)


    def get_summary(self):
        return self.summary
