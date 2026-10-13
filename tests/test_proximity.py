"""Regression tests for descriptive spatial proximity statistics."""
import csv
import io
import math
import pytest
from spatial_cell_comm.proximity import analyze_proximity


def run(text, radius=5):
    return analyze_proximity(csv.DictReader(io.StringIO(text)), radius)


def test_pair_counts_with_boundary_and_same_type():
    data = "cell_id,cell_type,x,y\n1,T,0,0\n2,M,3,4\n3,T,6,8\n4,F,100,100\n"
    result = run(data)
    assert result["n_cells"] == 4
    assert result["n_pairs"] == 2
    assert result["pair_counts"] == [
        {"type_a": "M", "type_b": "T", "contacts": 2, "mean_distance": 5.0}
    ]


def test_unordered_same_type_and_negative_coordinates():
    result = run("cell_id,cell_type,x,y\n1,T,-1,-1\n2,T,-1,-1\n3,T,9,9\n", 1)
    assert result["n_pairs"] == 1
    assert result["pair_counts"][0]["type_a"] == "T"
    assert result["pair_counts"][0]["type_b"] == "T"
    assert result["pair_counts"][0]["mean_distance"] == 0


def test_no_contacts_and_sparse_rows():
    result = run("cell_id,cell_type,x,y\n1,A,0,0\n2,B,100,100\n")
    assert result["n_pairs"] == 0
    assert result["pair_counts"] == []


@pytest.mark.parametrize("radius", [0, -1, float("nan"), float("inf")])
def test_invalid_radius(radius):
    with pytest.raises(ValueError, match="radius"):
        analyze_proximity([{"cell_id": "1", "cell_type": "A", "x": 0, "y": 0}], radius)


@pytest.mark.parametrize("records", [
    "cell_id,cell_type,x,y\n1,A,NaN,0\n",
    "cell_id,cell_type,x,y\n1,A,0,Inf\n",
    "cell_id,cell_type,x,y\n1,A,0,0\n1,B,1,1\n",
    "cell_id,cell_type,x,y\n1,,0,0\n",
    "cell_id,cell_type,x,y\n",
    "cell_id,cell_type,x,y\n1,A,wrong,0\n",
])
def test_invalid_rows(records):
    with pytest.raises(ValueError):
        run(records)


def test_cell_limit():
    rows = [{"cell_id": str(i), "cell_type": "A", "x": i, "y": 0} for i in range(3)]
    with pytest.raises(ValueError, match="limit"):
        analyze_proximity(rows, 1, max_cells=2)
