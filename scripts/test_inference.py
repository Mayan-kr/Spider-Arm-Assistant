from unsloth import FastLanguageModel
import torch
import json

def test_inference():
    # Load correctly as a multi-modal model if possible, 
    # but Qwen 3.5 0.8B in some unsloth versions is just text-heavy.
    model_path = "qwen_assistant_lora"
    print(f"[TEST] Loading model from {model_path}...")
    
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = model_path,
        max_seq_length = 2048,
        load_in_4bit = True,
    )
    FastLanguageModel.for_inference(model)

    instruction = "Take a screenshot and check my disk space."
    print(f"[TEST] Instruction: {instruction}")
    
    prompt = f"### Instruction:\n{instruction}\n\n### Thought:\n"
    
    inputs = tokenizer(prompt, return_tensors = "pt").to("cuda")
    
    print(f"[TEST] Generating...")
    outputs = model.generate(
        input_ids = inputs.input_ids,
        attention_mask = inputs.attention_mask,
        max_new_tokens = 128,
        use_cache = True,
        do_sample = False,  # Greedy decoding for deterministic tool calls
    )
    
    # Only decode the NEW tokens — strip the prompt from the output
    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
    print("-" * 30)
    print(response)
    print("-" * 30)

if __name__ == "__main__":
    test_inference()
