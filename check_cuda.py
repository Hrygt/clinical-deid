# check_cuda.py

import torch

print("=" * 50)
print("CUDA Diagnostics")
print("=" * 50)

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"Device count: {torch.cuda.device_count()}")
    print(f"Current device: {torch.cuda.current_device()}")
    print(f"Device name: {torch.cuda.get_device_name(0)}")
    
    # Memory info
    props = torch.cuda.get_device_properties(0)
    total_memory = props.total_memory / 1024**3
    print(f"Total VRAM: {total_memory:.1f} GB")
    
    # Quick tensor test
    print("\nRunning tensor test...")
    x = torch.randn(1000, 1000, device="cuda")
    y = torch.matmul(x, x)
    print(f"Tensor test passed! Result shape: {y.shape}")
    
    # Test model loading
    print("\nTesting model load...")
    from transformers import LongformerForTokenClassification
    model = LongformerForTokenClassification.from_pretrained(
        "yikuan8/Clinical-Longformer",
        num_labels=101
    )
    model.to("cuda")
    print("Model loaded to GPU successfully!")
    
    # Memory after model load
    allocated = torch.cuda.memory_allocated(0) / 1024**3
    print(f"GPU memory allocated: {allocated:.2f} GB")
    
    del model
    torch.cuda.empty_cache()
    print("\nCUDA check passed! ✓")
else:
    print("\n⚠️  CUDA not available!")
    print("Check your PyTorch installation:")
    print("  pip install torch --index-url https://download.pytorch.org/whl/cu121")