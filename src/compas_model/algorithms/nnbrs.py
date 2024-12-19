import numpy.typing as npt
from numpy import asarray
from scipy.spatial import cKDTree


def find_nearest_neighbours(cloud: npt.ArrayLike, nmax: int, dims: int = 3) -> list[tuple[list[float], list[int]]]:
    """Find the nearest neighbours of each point in a cloud among all other points in the cloud.

    Parameters
    ----------
    cloud : array-like
        The cloud of points.
    nmax : int
        The maximum number of neighbours per point.
    dims : int, optional
        The number of dimensions to include in the search.

    Results
    -------
    list[tuple[list[float], list[int]]]
        For each point, a tuple with the distances to the nearest neighbours,
        and the indices to the corresponding points.

    """
    cloud = asarray(cloud)[:, :dims]
    tree = cKDTree(cloud)
    nnbrs = [tree.query(root, nmax) for root in cloud]
    nnbrs = [(d.flatten().tolist(), n.flatten().tolist()) for d, n in nnbrs]
    return nnbrs
