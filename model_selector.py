import customtkinter as ctk

class ModelSelector:
    AVAILABLE_MODELS = {
        "DeepSeek": "deepseek-r1-distill-llama-70b",
        "LLaMA Spec": "llama-3.3-70b-specdec",
        "LLaMA Versatile": "llama-3.3-70b-versatile"
    }
    
    def __init__(self, parent):
        self.current_model = None
        
        # Create selection frame
        self.frame = ctk.CTkFrame(parent)
        self.frame.pack(fill="x", padx=25, pady=(0, 10))
        
        # Add label
        label = ctk.CTkLabel(
            self.frame,
            text="Select Model:",
            font=("Segoe UI", 12, "bold")
        )
        label.pack(side="left", padx=15)
        
        # Create combobox for model selection
        self.model_var = ctk.StringVar(value="DeepSeek")
        self.combo = ctk.CTkComboBox(
            self.frame,
            values=list(self.AVAILABLE_MODELS.keys()),
            variable=self.model_var,
            width=200
        )
        self.combo.pack(side="left", padx=15)
        
    def get_selected_model(self):
        """Return the API model identifier for the selected model"""
        try:
            selected_name = self.model_var.get()
            if selected_name not in self.AVAILABLE_MODELS:
                print(f"Warning: Invalid model selection '{selected_name}', defaulting to DeepSeek")
                self.model_var.set("DeepSeek")
                selected_name = "DeepSeek"
            return self.AVAILABLE_MODELS.get(selected_name)
        except Exception as e:
            print(f"Model selection error: {e}")
            return self.AVAILABLE_MODELS["DeepSeek"]  # Default fallback
