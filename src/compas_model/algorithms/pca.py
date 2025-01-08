from numpy import asarray
from scipy.linalg import svd

from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Point


def pca_box(points: list[Point]) -> Box:
    """Compute the principle components of a set of data points.

    Parameters
    ----------
    points : list[:class:`compas.geometry.Point`]
        A list of 3D points.

    Returns
    -------
    :class:`compas.geometry.Box`

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
