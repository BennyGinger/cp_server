import numpy as np
import pytest
from unittest.mock import Mock, patch

from cp_server.tasks_server.tasks.segementation.cp_seg import run_seg


@pytest.fixture
def sample_image():
    """Create a sample 2D image for testing."""
    return np.random.randint(0, 255, (100, 100), dtype=np.uint8)


@pytest.fixture
def cellpose_settings():
    """Sample cellpose settings for testing."""
    return {
        "model_type": "cyto2",
        "gpu": False,  # Use CPU for tests
        "diameter": 30,
        "flow_threshold": 0.4,
        "cellprob_threshold": 0.0,
        "do_denoise": False,  # Disable denoising for faster tests
    }


@patch('cp_server.tasks_server.tasks.segementation.cp_seg.setup_cellpose')
@patch('cp_server.tasks_server.tasks.segementation.cp_seg.run_cellpose')
def test_run_seg_returns_masks(mock_run_cellpose, mock_setup_cellpose, sample_image, cellpose_settings):
    """run_seg returns single mask for single image input."""
    # Setup mocks
    mock_configured_settings = {'model': Mock(), 'eval_params': {}}
    mock_setup_cellpose.return_value = mock_configured_settings
    
    # Mock masks, flows, styles return from run_cellpose (single image)
    mock_masks = np.ones((100, 100), dtype=np.uint16)
    mock_flows = [np.zeros((100, 100)), np.zeros((100, 100)), np.zeros((100, 100))]
    mock_styles = np.array([1.0, 2.0])
    mock_run_cellpose.return_value = (mock_masks, mock_flows, mock_styles)
    
    # Call run_seg with single image
    result = run_seg(cellpose_settings, sample_image)
    
    # Verify setup_cellpose was called with correct parameters
    mock_setup_cellpose.assert_called_once_with(
        cellpose_settings=cellpose_settings,
        threading=False,
        use_nuclear_channel=False,
        do_denoise=False
    )
    
    # Verify run_cellpose was called with correct parameters
    mock_run_cellpose.assert_called_once_with(sample_image, mock_configured_settings)
    
    # Verify we get back the single mask (not a list)
    assert isinstance(result, np.ndarray)
    assert not isinstance(result, list)
    assert np.array_equal(result, mock_masks)


@patch('cp_server.tasks_server.tasks.segementation.cp_seg.setup_cellpose')
@patch('cp_server.tasks_server.tasks.segementation.cp_seg.run_cellpose')
def test_run_seg_handles_list_of_masks(mock_run_cellpose, mock_setup_cellpose, sample_image, cellpose_settings):
    """run_seg preserves list input/output relationship."""
    # Setup mocks
    mock_configured_settings = {'model': Mock(), 'eval_params': {}}
    mock_setup_cellpose.return_value = mock_configured_settings
    
    # Create a list of images as input
    image_list = [sample_image, sample_image]
    
    # Mock return where masks is a list (matching input)
    mock_masks_list = [np.ones((100, 100), dtype=np.uint16), np.ones((100, 100), dtype=np.uint16)]
    mock_flows = [np.zeros((100, 100)), np.zeros((100, 100))]
    mock_styles = [np.array([1.0, 2.0]), np.array([1.0, 2.0])]
    mock_run_cellpose.return_value = (mock_masks_list, mock_flows, mock_styles)
    
    # Call run_seg with list input
    result = run_seg(cellpose_settings, image_list)
    
    # Should return the list of masks as-is (preserving input/output relationship)
    assert isinstance(result, list)
    assert len(result) == 2
    assert np.array_equal(result[0], mock_masks_list[0])
    assert np.array_equal(result[1], mock_masks_list[1])


def test_run_seg_do_denoise_default(sample_image):
    """do_denoise defaults to True for backward compatibility."""
    cellpose_settings = {"model_type": "cyto2", "gpu": False}
    
    with patch('cp_server.tasks_server.tasks.segementation.cp_seg.setup_cellpose') as mock_setup:
        with patch('cp_server.tasks_server.tasks.segementation.cp_seg.run_cellpose') as mock_run:
            mock_setup.return_value = {'model': Mock(), 'eval_params': {}}
            mock_run.return_value = (np.ones((100, 100)), [], [])
            
            run_seg(cellpose_settings, sample_image)
            
            # Check that do_denoise=True was passed to setup_cellpose
            mock_setup.assert_called_once_with(
                cellpose_settings=cellpose_settings,
                threading=False,
                use_nuclear_channel=False,
                do_denoise=True  # Default value
            )


def test_run_seg_explicit_do_denoise(sample_image):
    """Explicit do_denoise setting is respected."""
    cellpose_settings = {"model_type": "cyto2", "gpu": False, "do_denoise": False}
    
    with patch('cp_server.tasks_server.tasks.segementation.cp_seg.setup_cellpose') as mock_setup:
        with patch('cp_server.tasks_server.tasks.segementation.cp_seg.run_cellpose') as mock_run:
            mock_setup.return_value = {'model': Mock(), 'eval_params': {}}
            mock_run.return_value = (np.ones((100, 100)), [], [])
            
            run_seg(cellpose_settings, sample_image)
            
            # Check that do_denoise=False was passed to setup_cellpose
            mock_setup.assert_called_once_with(
                cellpose_settings=cellpose_settings,
                threading=False,
                use_nuclear_channel=False,
                do_denoise=False  # Explicit value
            )
