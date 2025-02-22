from .fixtures import recursive_fixture, method_fixture
from bw2analyzer.utils import print_recursive_calculation, print_recursive_supply_chain
from bw2data.tests import bw2test
import bw2data as bd
import bw2calc as bc
import io
import pytest


@bw2test
def test_print_recursive_calculation_nonunitary_production(capsys):
    bd.Database("f").write(
        {
            ("f", "b"): {"exchanges": [], "type": "emission", "location": "GLO"},
            ("f", "1"): {
                "exchanges": [
                    {"input": ("f", "1"), "amount": 2, "type": "production"},
                    {"input": ("f", "2"), "amount": 2, "type": "technosphere"},
                ],
                "location": "GLO",
            },
            ("f", "2"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "b"), "amount": 1, "type": "biosphere"},
                ]
            },
        }
    )
    bd.Method(("m",)).write([(("f", "b"), 1)])

    print_recursive_calculation(("f", "1"), ("m",))
    expected = """Fraction of score | Absolute score | Amount | Activity
0001 |     1 |     1 | Activity with missing fields (call ``valid(why=True)`` to see more)
  0001 |     1 |     1 | Activity with missing fields (call ``valid(why=True)`` to see more)
"""
    assert capsys.readouterr().out == expected


@bw2test
def test_print_recursive_calculation_nonunitary_production_losses(capsys):
    bd.Database("f").write(
        {
            ("f", "b"): {"exchanges": [], "type": "emission", "location": "GLO"},
            ("f", "1"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "1"), "amount": 3, "type": "production"},
                    {"input": ("f", "1"), "amount": 1, "type": "technosphere"},
                    {"input": ("f", "2"), "amount": 2, "type": "technosphere"},
                ]
            },
            ("f", "2"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "b"), "amount": 1, "type": "biosphere"},
                ]
            },
        }
    )
    bd.Method(("m",)).write([(("f", "b"), 1)])

    print_recursive_calculation(("f", "1"), ("m",))
    expected = """Fraction of score | Absolute score | Amount | Activity
0001 |     1 |     1 | Activity with missing fields (call ``valid(why=True)`` to see more)
  0001 |     1 |     1 | Activity with missing fields (call ``valid(why=True)`` to see more)
"""
    assert capsys.readouterr().out == expected


@bw2test
def test_print_recursive_calculation_nonunitary_production_multiple_production(capsys):
    bd.Database("f").write(
        {
            ("f", "b"): {"exchanges": [], "type": "emission", "location": "GLO"},
            ("f", "1"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "1"), "amount": 1, "type": "production"},
                    {"input": ("f", "1"), "amount": 1, "type": "production"},
                    {"input": ("f", "2"), "amount": 2, "type": "technosphere"},
                ]
            },
            ("f", "2"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "b"), "amount": 1, "type": "biosphere"},
                ]
            },
        }
    )
    bd.Method(("m",)).write([(("f", "b"), 1)])

    with pytest.warns(UserWarning, match="Hit multiple production exchanges"):
        print_recursive_calculation(("f", "1"), ("m",))

    expected = """Fraction of score | Absolute score | Amount | Activity
0001 |     1 |     1 | Activity with missing fields (call ``valid(why=True)`` to see more)
"""
    assert capsys.readouterr().out == expected


@bw2test
def test_print_recursive_calculation(capsys):
    bd.Database("c").write({("c", "flow"): {"type": "emission"}})
    db = bd.Database("a")

    db.write(recursive_fixture)
    method = bd.Method(("method",))
    method.register()
    method.write(method_fixture)

    act = bd.get_activity(("a", "1"))
    lca = bc.LCA({act: 1}, ("method",))
    lca.lci()
    lca.lcia()

    print_recursive_calculation(act, ("method",))
    expected = """Fraction of score | Absolute score | Amount | Activity
0001 | 4.836 |     1 | 'process 1' (b, RU, None)
  0.586 | 2.836 |   0.8 | 'process 2' (b, UA, None)
    0.504 | 2.436 |  0.48 | 'process 3' (b, BY, None)
      0.499 | 2.412 | 0.048 | 'process 5' (b, RO, None)
"""
    assert capsys.readouterr().out == expected

    # max_level
    print_recursive_calculation(act, ("method",), max_level=1)
    expected = """Fraction of score | Absolute score | Amount | Activity
0001 | 4.836 |     1 | 'process 1' (b, RU, None)
  0.586 | 2.836 |   0.8 | 'process 2' (b, UA, None)
"""
    assert capsys.readouterr().out == expected

    # amount
    print_recursive_calculation(act, ("method",), amount=2, max_level=1)
    expected = """Fraction of score | Absolute score | Amount | Activity
0001 | 9.671 |     2 | 'process 1' (b, RU, None)
  0.586 | 5.671 |   1.6 | 'process 2' (b, UA, None)
"""
    assert capsys.readouterr().out == expected

    # cutoff
    print_recursive_calculation(act, ("method",), cutoff=0.00025)
    expected = """Fraction of score | Absolute score | Amount | Activity
0001 | 4.836 |     1 | 'process 1' (b, RU, None)
  0.586 | 2.836 |   0.8 | 'process 2' (b, UA, None)
    0.504 | 2.436 |  0.48 | 'process 3' (b, BY, None)
      0.00496 | 0.024 |   4.8 | 'process 4' (b, MD, None)
      0.499 | 2.412 | 0.048 | 'process 5' (b, RO, None)
"""
    assert capsys.readouterr().out == expected
    # io test
    io_ = io.StringIO()
    print_recursive_calculation(act, ("method",), max_level=1, file_obj=io_)
    io_.seek(0)
    expected = """Fraction of score | Absolute score | Amount | Activity
0001 | 4.836 |     1 | 'process 1' (b, RU, None)
  0.586 | 2.836 |   0.8 | 'process 2' (b, UA, None)
"""
    assert io_.read() == expected

    # tab_character
    print_recursive_calculation(act, ("method",), max_level=1, tab_character="🐎")
    expected = """Fraction of score | Absolute score | Amount | Activity
0001 | 4.836 |     1 | 'process 1' (b, RU, None)
🐎0.586 | 2.836 |   0.8 | 'process 2' (b, UA, None)
"""
    assert capsys.readouterr().out == expected


@bw2test
def test_print_recursive_supply_chain(capsys):
    db = bd.Database("a")
    db.write(recursive_fixture)
    act = bd.get_activity(("a", "1"))

    print_recursive_supply_chain(activity=act)
    expected = """1: 'process 1' (b, RU, None)
  0.8: 'process 2' (b, UA, None)
    0.48: 'process 3' (b, BY, None)
"""
    assert capsys.readouterr().out == expected

    print_recursive_supply_chain(activity=act, amount=2)
    expected = """2: 'process 1' (b, RU, None)
  1.6: 'process 2' (b, UA, None)
    0.96: 'process 3' (b, BY, None)
"""
    assert capsys.readouterr().out == expected

    print_recursive_supply_chain(activity=act, tab_character="🐎")
    expected = """1: 'process 1' (b, RU, None)
🐎0.8: 'process 2' (b, UA, None)
🐎🐎0.48: 'process 3' (b, BY, None)
"""
    assert capsys.readouterr().out == expected

    io_ = io.StringIO()
    print_recursive_supply_chain(activity=act, file_obj=io_)
    io_.seek(0)
    expected = """1: 'process 1' (b, RU, None)
  0.8: 'process 2' (b, UA, None)
    0.48: 'process 3' (b, BY, None)
"""
    assert io_.read() == expected

    print_recursive_supply_chain(activity=act, cutoff=0.05, max_level=5)
    expected = """1: 'process 1' (b, RU, None)
  0.8: 'process 2' (b, UA, None)
    0.48: 'process 3' (b, BY, None)
      4.8: 'process 4' (b, MD, None)
"""
    assert capsys.readouterr().out == expected

    print_recursive_supply_chain(activity=act, cutoff=0, max_level=5)
    expected = """1: 'process 1' (b, RU, None)
  0.8: 'process 2' (b, UA, None)
    0.48: 'process 3' (b, BY, None)
      4.8: 'process 4' (b, MD, None)
      0.048: 'process 5' (b, RO, None)
        0.0024: 'process 1' (b, RU, None)
          0.00192: 'process 2' (b, UA, None)
"""
    assert capsys.readouterr().out == expected


@bw2test
def test_print_recursive_supply_chain_nonunitary_production(capsys):
    bd.Database("f").write(
        {
            ("f", "b"): {"exchanges": [], "type": "emission", "location": "GLO"},
            ("f", "1"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "1"), "amount": 2, "type": "production"},
                    {"input": ("f", "2"), "amount": 2, "type": "technosphere"},
                ]
            },
            ("f", "2"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "b"), "amount": 1, "type": "biosphere"},
                ]
            },
        }
    )

    print_recursive_supply_chain(("f", "1"))
    expected = """1: Activity with missing fields (call ``valid(why=True)`` to see more)
  1: Activity with missing fields (call ``valid(why=True)`` to see more)
"""
    assert capsys.readouterr().out == expected


@bw2test
def test_print_recursive_supply_chain_nonunitary_production_losses(capsys):
    bd.Database("f").write(
        {
            ("f", "b"): {"exchanges": [], "type": "emission", "location": "GLO"},
            ("f", "1"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "1"), "amount": 3, "type": "production"},
                    {"input": ("f", "1"), "amount": 1, "type": "technosphere"},
                    {"input": ("f", "2"), "amount": 2, "type": "technosphere"},
                ]
            },
            ("f", "2"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "b"), "amount": 1, "type": "biosphere"},
                ]
            },
        }
    )

    print_recursive_supply_chain(("f", "1"))
    expected = """1: Activity with missing fields (call ``valid(why=True)`` to see more)
  1: Activity with missing fields (call ``valid(why=True)`` to see more)
"""
    assert capsys.readouterr().out == expected


@bw2test
def test_print_recursive_supply_chain_nonunitary_production_multiple_production(capsys):
    bd.Database("f").write(
        {
            ("f", "b"): {"exchanges": [], "type": "emission", "location": "GLO"},
            ("f", "1"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "1"), "amount": 1, "type": "production"},
                    {"input": ("f", "1"), "amount": 1, "type": "production"},
                    {"input": ("f", "2"), "amount": 2, "type": "technosphere"},
                ]
            },
            ("f", "2"): {
                "location": "GLO",
                "exchanges": [
                    {"input": ("f", "b"), "amount": 1, "type": "biosphere"},
                ]
            },
        }
    )

    with pytest.warns(UserWarning, match="Hit multiple production exchanges"):
        print_recursive_supply_chain(("f", "1"))

    expected = """1: Activity with missing fields (call ``valid(why=True)`` to see more)
"""
    assert capsys.readouterr().out == expected
