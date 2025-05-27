import numpy as np
from numba import jit
from skimage.segmentation import relabel_sequential


############### Main Function ################
def track_masks(masks: np.ndarray, stitch_threshold: float=0.25) -> np.ndarray:
    """
    Track cells over time by stitching 2D masks into a time sequence using a stitch_threshold on IOU. Incomplete tracks are also automatically trimmed.

    Args:
        masks (ndarray): stack of masks, where masks[t] is a 2D array of masks at time t.
        stitch_threshold (float, optional): Threshold value for stitching. Defaults to 0.25.

    Returns:
        ndarray: stitched masks.
    """
    stitched_masks = _stitch_frames(masks, stitch_threshold)
    trimmed_mask = _trim_incomplete_tracks(stitched_masks)
    return relabel_sequential(trimmed_mask)[0]


################# Stitching and IOU Functions ################

# Copied the function stitch3D from cellpose, to avoid having to install all the dependencies for the package.
def _stitch_frames(masks: np.ndarray, stitch_threshold: float) -> np.ndarray:
    """Stitch 2D masks into a continuous time sequence by matching masks across frames using a specified IOU threshold.

    Args:
        masks (ndarray): stack of masks, where masks[t] is a 2D array of masks at time t.
        stitch_threshold (float): Threshold value for stitching.

    Returns:
        ndarray: stitched masks.
    """
    
    mmax = masks[0].max()
    empty = 0
    for i in range(len(masks) - 1):
        iou = _intersection_over_union(masks[i + 1], masks[i])[1:, 1:]
        if not iou.size and empty == 0:
            mmax = masks[i + 1].max()
        elif not iou.size and empty != 0:
            icount = masks[i + 1].max()
            istitch = np.arange(mmax + 1, mmax + icount + 1, 1, masks.dtype)
            mmax += icount
            istitch = np.append(np.array(0), istitch)
            masks[i + 1] = istitch[masks[i + 1]]
        else:
            iou[iou < stitch_threshold] = 0.0
            iou[iou < iou.max(axis=0)] = 0.0
            istitch = iou.argmax(axis=1) + 1
            ino = np.nonzero(iou.max(axis=1) == 0.0)[0]
            istitch[ino] = np.arange(mmax + 1, mmax + len(ino) + 1, 1, masks.dtype)
            mmax += len(ino)
            istitch = np.append(np.array(0), istitch)
            masks[i + 1] = istitch[masks[i + 1]]
            empty = 1

    return masks

def _intersection_over_union(masks_true: np.ndarray, masks_pred: np.ndarray) -> np.ndarray:
    """Calculate the intersection over union of all mask pairs.

    Parameters:
        masks_true (np.ndarray, int): Ground truth masks, where 0=NO masks; 1,2... are mask labels.
        masks_pred (np.ndarray, int): Predicted masks, where 0=NO masks; 1,2... are mask labels.

    Returns:
        iou (np.ndarray, float): Matrix of IOU pairs of size [x.max()+1, y.max()+1].

    How it works:
        The overlap matrix is a lookup table of the area of intersection
        between each set of labels (true and predicted). The true labels
        are taken to be along axis 0, and the predicted labels are taken 
        to be along axis 1. The sum of the overlaps along axis 0 is thus
        an array giving the total overlap of the true labels with each of
        the predicted labels, and likewise the sum over axis 1 is the
        total overlap of the predicted labels with each of the true labels.
        Because the label 0 (background) is included, this sum is guaranteed
        to reconstruct the total area of each label. Adding this row and
        column vectors gives a 2D array with the areas of every label pair
        added together. This is equivalent to the union of the label areas
        except for the duplicated overlap area, so the overlap matrix is
        subtracted to find the union matrix. 
    """
    
    overlap = _label_overlap(masks_true, masks_pred)
    n_pixels_pred: np.ndarray = np.sum(overlap, axis=0, keepdims=True)
    n_pixels_true: np.ndarray = np.sum(overlap, axis=1, keepdims=True)
    iou = overlap / (n_pixels_pred + n_pixels_true - overlap)
    iou[np.isnan(iou)] = 0.0
    return iou

@jit(nopython=True)
def _label_overlap(m1: np.ndarray, m2: np.ndarray) -> np.ndarray:
    """Fast function to get pixel overlaps between masks in m1 and m2.

    Args:
        m1 (np.ndarray, int): Where 0=NO masks; 1,2... are mask labels.
        m2 (np.ndarray, int): Where 0=NO masks; 1,2... are mask labels.

    Returns:
        overlap (np.ndarray, int): Matrix of pixel overlaps of size [m1.max()+1, m2.max()+1].
    """
    
    m1 = m1.ravel()
    m2 = m2.ravel()

    # preallocate a "contact map" matrix
    overlap = np.zeros((1 + m1.max(), 1 + m2.max()), dtype=np.uint)

    # loop over the labels in x and add to the corresponding
    # overlap entry. If label A in x and label B in y share P
    # pixels, then the resulting overlap is P
    # len(x)=len(y), the number of pixels in the whole image
    for i in range(len(m1)):
        overlap[m1[i], m2[i]] += 1
    return overlap

def _trim_incomplete_tracks(mask: np.ndarray) -> np.ndarray:
    """
    Trim incomplete tracks from the mask stack.

    This function returns a new 3D mask array (tyx format) where only the objects 
    present in every frame are kept. Incomplete tracks (objects not found in all frames)
    are set to 0.

    Args:
        mask (np.ndarray): 3D mask array in tyx format.

    Returns:
        np.ndarray: The trimmed mask array.
    """
    # Determine the complete set of objects (present in every frame)
    complete_objs = set(np.unique(mask[0]))
    for frame in mask[1:]:
        complete_objs.intersection_update(np.unique(frame))
    
    # Create a copy of the mask to avoid modifying the original input
    trimmed_mask = mask.copy()
    
    # Set to 0 any object not present in all frames
    trimmed_mask[~np.isin(trimmed_mask, list(complete_objs))] = 0
    
    return trimmed_mask


if __name__ == "__main__":
    from pathlib import Path
    from tifffile import imread, imwrite
    
    img_path = Path("/media/ben/Analysis/Python/Images/Image_tests/dst_test/_z1_t10.tif_masks.tif")
    masks = imread(img_path)
    
    tracked_masks = track_masks(masks, stitch_threshold=0.75)
    
    # Save the tracked masks to a new file
    save_path = img_path.parent.joinpath(img_path.name.replace("_masks", "_tracked_masks"))
    imwrite(save_path, tracked_masks.astype(np.uint16), compression='zlib')