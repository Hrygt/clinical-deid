# preprocess.py

import json
import ast
from pathlib import Path
from collections import Counter
from transformers import AutoTokenizer
from labels import NEMOTRON_TO_ENTITY, LABEL2ID, ENTITY_TYPES

MODEL_NAME = "yikuan8/Clinical-Longformer"
MAX_LENGTH = 4096

def load_data(path):
    """Load JSONL data."""
    records = []
    with open(path) as f:
        for line in f:
            records.append(json.loads(line))
    return records

def spans_to_bilou(text, spans, tokenizer):
    """
    Convert character-level spans to token-level BILOU labels.
    
    Returns:
        input_ids: token ids
        attention_mask: attention mask
        labels: BILOU label ids for each token
    """
    # Tokenize with offset mapping
    encoding = tokenizer(
        text,
        max_length=MAX_LENGTH,
        truncation=True,
        padding="max_length",
        return_offsets_mapping=True,
        return_tensors=None
    )
    
    offset_mapping = encoding["offset_mapping"]
    input_ids = encoding["input_ids"]
    attention_mask = encoding["attention_mask"]
    
    # Initialize all labels as "O"
    labels = [LABEL2ID["O"]] * len(input_ids)
    
    # Filter spans to only include our target entities
    filtered_spans = []
    for span in spans:
        nemotron_label = span["label"]
        if nemotron_label in NEMOTRON_TO_ENTITY:
            entity_type = NEMOTRON_TO_ENTITY[nemotron_label]
            filtered_spans.append({
                "start": span["start"],
                "end": span["end"],
                "entity": entity_type
            })
    
    # For each span, find which tokens it covers
    for span in filtered_spans:
        span_start = span["start"]
        span_end = span["end"]
        entity = span["entity"]
        
        # Find tokens that overlap with this span
        span_token_indices = []
        for idx, (token_start, token_end) in enumerate(offset_mapping):
            # Skip special tokens (offset is (0,0))
            if token_start == 0 and token_end == 0 and idx != 0:
                continue
            # Check for overlap
            if token_end > span_start and token_start < span_end:
                span_token_indices.append(idx)
        
        # Apply BILOU tags
        if len(span_token_indices) == 0:
            continue
        elif len(span_token_indices) == 1:
            # Single token: U tag
            idx = span_token_indices[0]
            labels[idx] = LABEL2ID[f"U-{entity}"]
        else:
            # Multi-token: B, I..., L
            for i, idx in enumerate(span_token_indices):
                if i == 0:
                    labels[idx] = LABEL2ID[f"B-{entity}"]
                elif i == len(span_token_indices) - 1:
                    labels[idx] = LABEL2ID[f"L-{entity}"]
                else:
                    labels[idx] = LABEL2ID[f"I-{entity}"]
    
    # Set labels for special tokens to -100 (ignored in loss)
    for idx, (token_start, token_end) in enumerate(offset_mapping):
        if token_start == 0 and token_end == 0:
            labels[idx] = -100
    
    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels
    }

def preprocess_dataset(input_path, output_path):
    """Process full dataset."""
    print(f"Loading tokenizer: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    
    print(f"Loading data from {input_path}")
    records = load_data(input_path)
    print(f"Loaded {len(records)} records")
    
    processed = []
    entity_counts = Counter()
    skipped = 0
    
    for i, record in enumerate(records):
        text = record["text"]
        spans = record["spans"]
        
        # Count entities for stats
        for span in spans:
            if span["label"] in NEMOTRON_TO_ENTITY:
                entity_counts[NEMOTRON_TO_ENTITY[span["label"]]] += 1
        
        try:
            result = spans_to_bilou(text, spans, tokenizer)
            result["uid"] = record["uid"]
            result["document_type"] = record["document_type"]
            processed.append(result)
        except Exception as e:
            print(f"Error processing record {i}: {e}")
            skipped += 1
            continue
        
        if (i + 1) % 500 == 0:
            print(f"Processed {i + 1}/{len(records)}")
    
    print(f"\nProcessed: {len(processed)}, Skipped: {skipped}")
    
    print(f"\nEntity counts:")
    for entity, count in entity_counts.most_common():
        print(f"  {entity}: {count}")
    
    # Save processed data
    output_path = Path(output_path)
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, "w") as f:
        for record in processed:
            f.write(json.dumps(record) + "\n")
    
    print(f"\nSaved to {output_path}")
    return processed

if __name__ == "__main__":
    preprocess_dataset(
        "data/nemotron_healthcare.jsonl",
        "data/processed_bilou.jsonl"
    )