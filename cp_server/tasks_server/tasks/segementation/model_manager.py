from __future__ import annotations
import threading
from typing import Any

from cp_server.tasks_server import get_logger
### Lazy import ### 
# from cellpose_kit.api import setup_cellpose

logger = get_logger(__name__)


class ModelManager:
    """
    Singleton to manage persistent Cellpose models in worker processes using cellpose-kit
    """
    _instance = None
    _lock = threading.Lock()
    _cached_models: dict[str, Any] = {}  # Cache models only

    def __new__(cls) -> ModelManager:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def get_configured_settings(self, cellpose_settings: dict[str, Any]) -> dict[str, Any]:
        """
        Get or create configured settings using cellpose-kit.
        Caches models based on model settings only, recreates eval params each time.
        """
        from cellpose_kit.api import setup_cellpose  # Lazy import
        
        if not isinstance(cellpose_settings, dict):
            raise TypeError("cellpose_settings must be a dict")
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

        # Always create fresh configured settings (model + current eval params) using setup_cellpose with cached model
        cached = self._cached_models[model_key]
        use_nuclear_channel = cached['model_metadata']['use_nuclear_channel']
        do_denoise = cached['model_metadata']['do_denoise']
        configured_settings = setup_cellpose(
            cellpose_settings=cellpose_settings,
            threading=True,
            use_nuclear_channel=use_nuclear_channel,
            do_denoise=do_denoise,
            model=cached['model'])
        
        # Add lock if present in cache (for thread safety)
        if cached.get('lock') is not None:
            configured_settings['lock'] = cached['lock']
        return configured_settings

    def _extract_model_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        """
        Extract only the settings that affect model initialization
        """
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
            'do_denoise', 'use_nuclear_channel'}  # These affect model choice
        
        return {k: v for k, v in settings.items() if k in model_keys}

    def _get_model_key(self, model_settings: dict[str, Any]) -> str:
        """
        Create a unique key based only on model settings
        """
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
            str(model_settings.get('use_bfloat16', True)),]
        return "_".join(key_parts)

    def _setup_cellpose_model(self, cellpose_settings: dict[str, Any]) -> dict[str, Any]:
        """
        Setup only the model part using cellpose-kit
        """
        from cellpose_kit.api import setup_cellpose  # Lazy import
        
        # Create full configured settings to get the model
        threading_enabled = True
        use_nuclear_channel = cellpose_settings.get('use_nuclear_channel', False)
        do_denoise = cellpose_settings.get('do_denoise', True)

        full_config = setup_cellpose(
            cellpose_settings=cellpose_settings,
            threading=threading_enabled,
            use_nuclear_channel=use_nuclear_channel,
            do_denoise=do_denoise)

        # Extract and return only the model and lock (not eval_params)
        return {
            'model': full_config['model'],
            'lock': full_config.get('lock'),
            'model_metadata': {
                'use_nuclear_channel': use_nuclear_channel,
                'do_denoise': do_denoise}}

    def clear_cache(self) -> None:
        """
        Clear all cached models (useful for testing or memory management)
        """
        with self._lock:
            self._cached_models.clear()
            logger.info("Model cache cleared")

# Global instance
model_manager = ModelManager()