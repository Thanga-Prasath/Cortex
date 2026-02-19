from ctransformers import AutoModelForCausalLM
import os
import sys

model_path = os.path.join(os.getcwd(), 'data', 'models', 'smollm2-360m-instruct-q8_0.gguf')

print(f"Testing model load from: {model_path}")

if not os.path.exists(model_path):
    print("ERROR: File does not exist!")
    sys.exit(1)

file_size_mb = os.path.getsize(model_path) / (1024 * 1024)
print(f"File Size: {file_size_mb:.2f} MB")

try:
    print("Attempting to load...")
    llm = AutoModelForCausalLM.from_pretrained(
        model_path,
        model_type="llama",
        context_length=512
    )
    print("SUCCESS: Model loaded!")
    print("Generating test...")
    print(llm("Hello"))
except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
