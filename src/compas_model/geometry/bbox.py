from numpy import array
from numpy import asarray
from scipy.linalg import svd

from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Point


def pca_box(points: list[Point]) -> Box:
    """Compute an oriented bounding box for the given points based on the principle components of the XYZ coordinates.

    Parameters
    ----------
    points : list[:class:`compas.geometry.Point`]
        A list of 3D points.

    Returns
    -------
    :class:`compas.geometry.Box`

    See Also
    --------
    :func:`compas.geometry.oriented_bounding_box_numpy`
    :func:`compas.geometry.pca_numpy`

    Notes
    -----
    The resulting box is not (necessarily) a minimum bounding volume.
    The box is computed by reprojecting the points onto the principle component vectors to identify the box extents.
    The origin of the box is found as the centroid of the points, corrected with the box extents.

    Examples
    --------
    >>> import random
    >>> import math
    >>> from compas.geometry import Pointcloud
    >>> from compas.geometry import Translation, Rotation
    >>> from compas_model.geometry import pca_box

    Construct a cloud of points.

    >>> cloud = Pointcloud.from_bounds(8, 3, 1, 53)

    Construct a random translation.

    >>> vector = [10 * random.random(), 10 * random.random(), 10 * random.random()]
    >>> T = Translation.from_vector(vector)

    Construct a random rotation.

    >>> axis = [random.random(), random.random(), random.random()]
    >>> angle = math.radians(random.random() * 180)
    >>> R = Rotation.from_axis_and_angle(axis, angle)

    Transform the cloud and compute its PCA box.

    >>> cloud.transform(T * R)
    >>> box = pca_box(cloud)

    Check.

    >>> all(box.contains_point(point) for point in cloud)
    True

    """
    X = asarray(points)
    n = X.shape[0]
    mean = X.mean(axis=0)

    Y = X - mean
    C = Y.T.dot(Y) / (n - 1)
    u, s, vT = svd(C, full_matrices=False)

    xaxis, yaxis, zaxis = vT

    x = Y.dot(xaxis)
    y = Y.dot(yaxis)
    z = Y.dot(zaxis)

    xmin, xmax = x.min(), x.max()
    ymin, ymax = y.min(), y.max()
    zmin, zmax = z.min(), z.max()

    xsize = xmax - xmin
    ysize = ymax - ymin
    zsize = zmax - zmin

    point = mean + 0.5 * (xmin + xmax) * xaxis + 0.5 * (ymin + ymax) * yaxis + 0.5 * (zmin + zmax) * zaxis

    return Box(xsize=xsize, ysize=ysize, zsize=zsize, frame=Frame(point, xaxis, yaxis))


def combine_aabbs(boxes: list[Box]) -> Box:
    extents = array([[box.xmin, box.ymin, box.zmin, box.xmax, box.ymax, box.zmax] for box in boxes])
    mins = extents.min(axis=0)
    maxs = extents.max(axis=0)
    xmin, ymin, zmin = mins[:3]
    xmax, ymax, zmax = maxs[3:]
    xsize = xmax - xmin
    ysize = ymax - ymin
    zsize = zmax - zmin
    point = xmin + 0.5 * xsize, ymin + 0.5 * ysize, zmin + 0.5 * zsize
    return Box(xsize, ysize, zsize, frame=Frame(point=point))


def combine_obbs(boxes: list[Box]) -> Box:
    return pca_box([box.points for box in boxes])
