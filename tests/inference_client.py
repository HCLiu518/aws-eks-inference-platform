import time
import requests

# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
# PASTE YOUR AWS PUBLIC IP HERE (e.g., "3.14.159.26")
AWS_PUBLIC_IP = "localhost" 

# The full URL to the vLLM API endpoint
API_URL = f"http://{AWS_PUBLIC_IP}:8000/v1/completions"

# ------------------------------------------------------------------
# THE TEST
# ------------------------------------------------------------------
def test_inference():
    print(f"🚀 Connecting to AI Server at {AWS_PUBLIC_IP}...")

    # The "Prompt" is what we send to the AI
    payload = {
        "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "prompt": "Write a haiku about a software engineer fixing a bug.",
        "max_tokens": 50,
        "temperature": 0.7
    }

    start_time = time.time()
    
    try:
        # Send the POST request
        response = requests.post(API_URL, json=payload, timeout=10)
        response.raise_for_status() # Raise error if status is not 200 OK
        
        # Calculate how long it took (Latency)
        latency = (time.time() - start_time) * 1000
        result = response.json()
        
        # Print the results
        generated_text = result['choices'][0]['text'].strip()
        
        print("\n✅ SUCCESS! Model Responded.")
        print(f"⏱️ Latency: {latency:.2f} ms")
        print("-" * 40)
        print(f"🤖 AI Output:\n{generated_text}")
        print("-" * 40)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION FAILED.")
        print("Tip: Check if the Docker container is fully ready (look for 'Uvicorn running').")
        print("Tip: Check if your Security Group allows Port 8000 from your IP.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    test_inference()