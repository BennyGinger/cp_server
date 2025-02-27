# Copied the function stitch3D from cellpose, to avoid having to install all the dependencies for the package.

import numpy as np
from numba import jit

def stitch_frames(masks: np.ndarray, stitch_threshold: float=0.25)-> np.ndarray:
    """Stitch 2D masks into a time sequence using a stitch_threshold on IOU.

    Args:
        masks (list or ndarray): List of 2D masks.
        stitch_threshold (float, optional): Threshold value for stitching. Defaults to 0.25.

    Returns:
        list: List of stitched 3D masks.
    """
    
    mmax = masks[0].max()
    empty = 0
    for i in range(len(masks) - 1):
        iou = _intersection_over_union(masks[i + 1], masks[i])[1:, 1:]
        if not iou.size and empty == 0:
            masks[i + 1] = masks[i + 1]
            mmax = masks[i + 1].max()
        elif not iou.size and not empty == 0:
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

def _intersection_over_union(masks_true: np.ndarray, masks_pred: np.ndarray)-> np.ndarray:
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
def _label_overlap(x: np.ndarray, y: np.ndarray)-> np.ndarray:
    """Fast function to get pixel overlaps between masks in x and y.

    Args:
        x (np.ndarray, int): Where 0=NO masks; 1,2... are mask labels.
        y (np.ndarray, int): Where 0=NO masks; 1,2... are mask labels.

    Returns:
        overlap (np.ndarray, int): Matrix of pixel overlaps of size [x.max()+1, y.max()+1].
    """
    
    x = x.ravel()
    y = y.ravel()

    # preallocate a "contact map" matrix
    overlap = np.zeros((1 + x.max(), 1 + y.max()), dtype=np.uint)

    # loop over the labels in x and add to the corresponding
    # overlap entry. If label A in x and label B in y share P
    # pixels, then the resulting overlap is P
    # len(x)=len(y), the number of pixels in the whole image
    for i in range(len(x)):
        overlap[x[i], y[i]] += 1
    return overlap