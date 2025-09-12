import threading
from typing import Dict, Any, Optional
import numpy as np

from cp_server.tasks_server import get_logger

logger = get_logger('model_manager')

class ModelManager:
    """Singleton to manage persistent Cellpose models in worker processes using cellpose-kit"""
    _instance = None
    _lock = threading.Lock()
    _cached_models: Dict[str, Any] = {}  # Cache models only
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_configured_settings(self, cellpose_settings: dict) -> Any:
        """
        Get or create configured settings using cellpose-kit.
        Caches models based on model settings only, recreates eval params each time.
        """
        # Separate model and eval settings
        model_settings = self._extract_model_settings(cellpose_settings)
        model_key = self._get_model_key(model_settings)
        
        # Get or create cached model
        if model_key not in self._cached_models:
            logger.info(f"Setting up new Cellpose model with cellpose-kit: {model_key}")
            self._cached_models[model_key] = self._setup_cellpose_model(cellpose_settings)
            logger.info(f"Cellpose-kit model {model_key} configured and cached")
        else:
            logger.debug(f"Using cached cellpose-kit model: {model_key}")
        
        # Always create fresh configured settings (model + current eval params)
        return self._create_configured_settings(
            self._cached_models[model_key], 
            cellpose_settings
        )
    
    def _extract_model_settings(self, settings: dict) -> dict:
        """Extract only the settings that affect model initialization"""
        # Model settings from v3 and v4 backends
        model_keys = {
            # Common model settings
            'gpu', 'device', 'pretrained_model', 'model_type',
            # v3 specific
            'diam_mean', 'nchan', 'mkldnn', 'pretrained_model_ortho', 'backbone',
            'restore_type', 'chan2_restore',  # v3 denoise specific
            # v4 specific  
            'use_bfloat16',
            # Our custom settings
            'do_denoise', 'use_nuclear_channel'  # These affect model choice
        }
        
        return {k: v for k, v in settings.items() if k in model_keys}
    
    def _get_model_key(self, model_settings: dict) -> str:
        """Create a unique key based only on model settings"""
        key_parts = [
            # Core model identity
            str(model_settings.get('pretrained_model', model_settings.get('model_type', 'cyto3'))),
            str(model_settings.get('gpu', True)),
            str(model_settings.get('device', 'None')),
            # Model-specific settings
            str(model_settings.get('do_denoise', True)),
            str(model_settings.get('use_nuclear_channel', False)),
            str(model_settings.get('restore_type', 'None')),
            # v3 specific
            str(model_settings.get('diam_mean', 30.0)),
            str(model_settings.get('nchan', 2)),
            str(model_settings.get('backbone', 'default')),
            # v4 specific
            str(model_settings.get('use_bfloat16', True)),
        ]
        return "_".join(key_parts)
    
    def _setup_cellpose_model(self, cellpose_settings: dict) -> Any:
        """Setup only the model part using cellpose-kit"""
        try:
            from cellpose_kit.api import setup_cellpose
        except ImportError as e:
            logger.error("Failed to import cellpose-kit. Ensure cellpose-kit is installed on this worker.")
            raise
            
        # Create full configured settings to get the model
        threading_enabled = True
        use_nuclear_channel = cellpose_settings.get('use_nuclear_channel', False)
        do_denoise = cellpose_settings.get('do_denoise', True)
        
        full_config = setup_cellpose(
            cellpose_settings=cellpose_settings,
            threading=threading_enabled,
            use_nuclear_channel=use_nuclear_channel,
            do_denoise=do_denoise
        )
        
        # Extract and return only the model and lock (not eval_params)
        return {
            'model': full_config['model'],
            'lock': full_config.get('lock'),
            'model_metadata': {
                'use_nuclear_channel': use_nuclear_channel,
                'do_denoise': do_denoise
            }
        }
    
    def _create_configured_settings(self, cached_model: dict, current_settings: dict) -> dict:
        """Create fresh configured settings with cached model + current eval params"""
        try:
            from cellpose_kit.backend.v3 import configure_eval_params as v3_eval
            from cellpose_kit.backend.v4 import configure_eval_params as v4_eval
            from cellpose_kit.compat import get_cellpose_version
        except ImportError as e:
            logger.error("Failed to import cellpose-kit backend functions.")
            raise
        
        # Determine which eval params to use based on cellpose version
        backend = get_cellpose_version()
        metadata = cached_model['model_metadata']
        
        if backend == "v3":
            eval_params = v3_eval(
                current_settings, 
                metadata['use_nuclear_channel'], 
                metadata['do_denoise']
            )
        elif backend == "v4":
            eval_params = v4_eval(
                current_settings, 
                metadata['use_nuclear_channel'], 
                metadata['do_denoise']
            )
        else:
            raise ValueError(f"Unsupported cellpose backend: {backend}")
        
        return {
            'model': cached_model['model'],
            'eval_params': eval_params,
            'lock': cached_model.get('lock')
        }
    
    def clear_cache(self):
        """Clear all cached models (useful for testing or memory management)"""
        with self._lock:
            self._cached_models.clear()
            logger.info("Model cache cleared")

# Global instance
model_manager = ModelManager()
