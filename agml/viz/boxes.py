import cv2
import numpy as np

import matplotlib.pyplot as plt

from agml.utils.general import resolve_tuple_values, as_scalar, scalar_unpack
from agml.data.tools import _resolve_coco_annotations # noqa
from agml.viz.tools import get_colormap, auto_resolve_image, format_image

@auto_resolve_image
def annotate_bboxes_on_image(image, bboxes = None, labels = None):
    """Annotates bounding boxes onto an image.

    Given an image with bounding boxes and labels, this method will
    annotate the bounding boxes directly onto the image (with category
    label). Bounding boxes are expected to be in COCO JSON format, that
    is, (`x_min`, `y_max`, `width`, `height`). Use the helper method
    `agml.data.convert_bboxes` to format your bounding boxes as such.

    Parameters
    ----------
    image : Any
        Either the image, or a tuple consisting of the image,
        bounding boxes, and (optional) labels.
    bboxes : Any
        The bounding boxes in COCO JSON format. This can be either
        a dictionary with COCO JSON annotations, or just the boxes.
    labels : Any
        Optional category labels for the bounding box color.

    Returns
    -------
    The annotated image.
    """
    image, bboxes, labels = resolve_tuple_values(
        image, bboxes, labels, custom_error =
        "If `image` is a tuple/list, it should contain "
        "three values: the image, mask, and (optionally) labels.")
    if isinstance(bboxes, dict):
        bboxes = _resolve_coco_annotations(bboxes)['bboxes']
    image = format_image(image)
    if labels is None:
        labels = [1] * len(bboxes)

    for bbox, label in zip(bboxes, labels):
        x1, y1, width, height = scalar_unpack(bbox)
        x2, y2 = x1 + width, y1 + height
        image = cv2.rectangle(image, (x1, y1), (x2, y2),
                      get_colormap()[as_scalar(label)], 2)
    return image


@auto_resolve_image
def visualize_image_and_boxes(image, bboxes = None, labels = None):
    """Visualizes an image with annotated bounding boxes.

    This method performs the same actions as `annotate_bboxes_on_image`,
    but simply displays the image once it has been formatted.

    Parameters
    ----------
    image : Any
        Either the image, or a tuple consisting of the image,
        bounding boxes, and (optional) labels.
    bboxes : Any
        The bounding boxes in COCO JSON format.
    labels : Any
        Optional category labels for the bounding box color.

    Returns
    -------
    The matplotlib figure with the image.
    """
    image, bboxes, labels = resolve_tuple_values(
        image, bboxes, labels, custom_error =
        "If `image` is a tuple/list, it should contain "
        "three values: the image, mask, and (optionally) labels.")
    image = annotate_bboxes_on_image(image, bboxes, labels)

    plt.figure(figsize = (10, 10))
    plt.imshow(image)
    plt.gca().axis('off')
    plt.gca().set_aspect('equal')
    plt.show()
    return image


