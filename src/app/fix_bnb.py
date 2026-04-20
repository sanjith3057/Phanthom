import bitsandbytes as bnb
import torch
import warnings

def patch_bitsandbytes():
    """
    Monkeypatch bitsandbytes to be compatible with newer transformers/peft versions.
    Fixes: TypeError: Params4bit.__new__() got an unexpected keyword argument '_is_hf_initialized'
    """
    try:
        if hasattr(bnb.nn.modules, "Params4bit"):
            original_new = bnb.nn.modules.Params4bit.__new__
            
            def patched_new(cls, *args, **kwargs):
                # Remove keyword arguments that newer HF/PEFT might pass but older BNB doesn't expect
                kwargs.pop("_is_hf_initialized", None)
                kwargs.pop("_is_quantized", None)
                return original_new(cls, *args, **kwargs)
            
            bnb.nn.modules.Params4bit.__new__ = patched_new
            # print("✅ BitsAndBytes: Params4bit patched for HF compatibility.")
    except Exception as e:
        # Silently fail if bnb isn't structured as expected, but warn in dev
        warnings.warn(f"Failed to patch bitsandbytes: {e}")

# Apply patch immediately
patch_bitsandbytes()
