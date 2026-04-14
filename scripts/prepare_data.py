import json
from datasets import Dataset

def prepare_dataset():
    input_file = "data/pc_control_dataset.jsonl"
    prepared_data = []
    
    with open(input_file, "r") as f:
        for line in f:
            entry = json.loads(line)
            # Format: Instruction -> Thought -> Action
            # We wrap this in a single 'text' field for SFT
            text = f"### Instruction:\n{entry['instruction']}\n\n### Thought:\n{entry['thought']}\n\n### Action:\n{entry['action']}"
            prepared_data.append({"text": text})
            
    dataset = Dataset.from_list(prepared_data)
    print(f"Prepared {len(prepared_data)} lines for training.")
    return dataset

if __name__ == "__main__":
    prepare_dataset()
