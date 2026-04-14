from unsloth import FastLanguageModel
import torch
from trl import SFTTrainer
from transformers import TrainingArguments
from scripts.prepare_data import prepare_dataset

def run_training():
    # 1. Model & Tokenizer Config
    model_name = "unsloth/Qwen2.5-1.5B-Instruct"
    max_seq_length = 2048 # Adjusted for 4GB VRAM
    
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = model_name,
        max_seq_length = max_seq_length,
        load_in_4bit = True, # Critical for 4GB VRAM
    )

    # 2. Add LoRA Adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r = 16, # Rank
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                          "gate_proj", "up_proj", "down_proj",],
        lora_alpha = 16,
        lora_dropout = 0,
        bias = "none",
        use_gradient_checkpointing = "unsloth", # Saves VRAM
        random_state = 3407,
    )

    # 3. Data Preparation
    dataset = prepare_dataset()

    # 4. Training Arguments
    trainer = SFTTrainer(
        model = model,
        tokenizer = tokenizer,
        train_dataset = dataset,
        dataset_text_field = "text",
        max_seq_length = max_seq_length,
        dataset_num_proc = 2,
        packing = False, # Can speed up for short sequences
        args = TrainingArguments(
            per_device_train_batch_size = 1, # Minimal VRAM usage
            gradient_accumulation_steps = 16, # Achieve effective batch size
            warmup_steps = 5,
            max_steps = 30, # Small example run
            learning_rate = 2e-4,
            fp16 = not torch.cuda.is_bf16_supported(),
            bf16 = torch.cuda.is_bf16_supported(),
            logging_steps = 1,
            optim = "adamw_8bit",
            weight_decay = 0.01,
            lr_scheduler_type = "linear",
            seed = 3407,
            output_dir = "outputs",
        ),
    )

    # 5. Execute Training
    print("[TRAIN] Starting fine-tuning...")
    trainer.train()
    
    # 6. Save Model
    print("[TRAIN] Saving LoRA adapters...")
    model.save_pretrained("qwen_assistant_lora")
    tokenizer.save_pretrained("qwen_assistant_lora")
    print("[TRAIN] Done!")

if __name__ == "__main__":
    run_training()
