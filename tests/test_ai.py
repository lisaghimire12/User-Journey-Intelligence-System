from types import SimpleNamespace
from ai.interpreter.product_interpreter import interpret_product
def test_missing_information():
    p=SimpleNamespace(name="Shoe",category="Shoes",attributes={"weight":"280g"})
    r=interpret_product(p)
    assert "Width Measurements" in r["missing_information"]
