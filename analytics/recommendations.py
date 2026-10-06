def recommendations(o):
    return [
      {"title":"Improve checkout flow","evidence":[f"Current abandonment is {o['abandonment_rate']}%"],"expected_benefit":10,"confidence":"Medium","complexity":"Low","risk":"Low","explanation":"Checkout is a plausible intervention target; validate it with controlled experimentation before making a causal claim."},
      {"title":"Improve product information visibility","evidence":["Product insight interactions are tracked in the same journey pipeline"],"expected_benefit":5,"confidence":"Low","complexity":"Low","risk":"Low","explanation":"The Know Before You Buy feature provides richer product context without turning the storefront into a chatbot."}
    ]
