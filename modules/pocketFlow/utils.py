from langchain_ollama import OllamaLLM

def call_llm(messages):
    client = OllamaLLM(model="deepseek-r1:1.5b")
    # client = OllamaLLM(model="tinyllama:latest")
    
    response = client.invoke(messages)
    
    return response

if __name__ == "__main__":
    # Test the LLM call
    messages = [{"role": "user", "content": "In a few words, what's the meaning of life?"}]
    response = call_llm(messages)
    print(f"Prompt: {messages[0]['content']}")
    print(f"Response: {response}")
