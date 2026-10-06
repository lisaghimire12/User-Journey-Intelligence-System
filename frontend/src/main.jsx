import React, { useEffect, useState } from "react";

import {
    createRoot
} from "react-dom/client";

import {
    BrowserRouter,
    Routes,
    Route,
    Link,
    useParams
} from "react-router-dom";

import "./styles.css";


const API =
    import.meta.env.VITE_API_URL ||
    "http://localhost:8000";


/* =========================================================
   USER + SESSION
========================================================= */

const uid =
    localStorage.getItem("journey_uid") ||
    crypto.randomUUID();

const sid =
    sessionStorage.getItem("journey_sid") ||
    crypto.randomUUID();

localStorage.setItem(
    "journey_uid",
    uid
);

sessionStorage.setItem(
    "journey_sid",
    sid
);

let sequence =
    Number(
        sessionStorage.getItem(
            "journey_seq"
        ) || 0
    );


/* =========================================================
   EVENT TRACKING
========================================================= */

async function track(
    eventName,
    page,
    productId = null,
    metadata = {}
) {

    sequence += 1;

    sessionStorage.setItem(
        "journey_seq",
        sequence
    );

    try {

        await fetch(
            API + "/api/events",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    event_name:
                        eventName,

                    anonymous_user_id:
                        uid,

                    session_id:
                        sid,

                    page,

                    product_id:
                        productId,

                    timestamp:
                        new Date().toISOString(),

                    sequence_number:
                        sequence,

                    metadata
                })
            }
        );

    } catch {

        // Analytics failure should
        // never break shopping.

    }
}


/* =========================================================
   PRODUCT IMAGES
========================================================= */

const productImages = {

    "clothing-01":
        "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=85",

    "clothing-02":
        "https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&w=900&q=85",

    "clothing-03":
        "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=900&q=85",

    "shoes-01":
        "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=85",

    "shoes-02":
        "https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=900&q=85",

    "shoes-03":
        "https://images.unsplash.com/photo-1495555961986-6d4c1ecb7be3?auto=format&fit=crop&w=900&q=85",

    "food-01":
        "https://images.unsplash.com/photo-1593095948071-474c5cc2989d?auto=format&fit=crop&w=900&q=85",

    "food-02":
        "https://images.unsplash.com/photo-1606312619070-d48b4c652a52?auto=format&fit=crop&w=900&q=85",

    "food-03":
        "https://images.unsplash.com/photo-1517093728432-a0440f8d45af?auto=format&fit=crop&w=900&q=85",

    "electronics-01":
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=85",

    "electronics-02":
        "https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=900&q=85",

    "electronics-03":
        "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=85"

};


function getProductImage(product) {

    return (
        productImages[product.id] ||
        product.images?.[0] ||
        ""
    );

}


/* =========================================================
   PRODUCTS
========================================================= */

function useProducts() {

    const [
        products,
        setProducts
    ] = useState([]);

    useEffect(() => {

        fetch(
            API + "/api/products"
        )
            .then(response => {

                if (!response.ok) {
                    throw new Error(
                        "Failed to load products"
                    );
                }

                return response.json();

            })
            .then(setProducts)
            .catch(error => {

                console.error(
                    "Products error:",
                    error
                );

            });

    }, []);

    return products;
}


/* =========================================================
   LAYOUT
========================================================= */

function Layout({
    children
}) {

    return (

        <>

            <header>

                <Link
                    className="logo"
                    to="/"
                >
                    ATELIER / 01
                </Link>


                <nav>

                    <Link to="/products">
                        Shop
                    </Link>

                    <Link to="/privacy">
                        Privacy
                    </Link>

                    <Link to="/cart">
                        Cart
                    </Link>

                </nav>

            </header>


            {children}


            <footer>
                ATELIER / 01 · Thoughtful commerce,
                transparent information.
            </footer>

        </>

    );

}


/* =========================================================
   PRODUCT CARD
========================================================= */

function ProductCard({
    product
}) {

    return (

        <Link
            className="card"
            to={
                "/products/" +
                product.id
            }
        >

            <div className="visual">

                <img
                    src={getProductImage(product)}
                    alt={product.name}
                />

                <small>
                    {product.category}
                </small>

            </div>


            <div className="cardrow">

                <div>

                    <b>
                        {product.name}
                    </b>

                    <small>
                        {product.brand}
                    </small>

                </div>

                <span>
                    ₹
                    {Number(
                        product.price
                    ).toLocaleString()}
                </span>

            </div>

        </Link>

    );

}


/* =========================================================
   HOME
========================================================= */

function Home() {

    const products =
        useProducts();


    useEffect(() => {

        track(
            "page_view",
            "Home"
        );

    }, []);


    return (

        <Layout>

            <section className="hero">

                <div>

                    <small>
                        THE NEW EVERYDAY
                    </small>

                    <h1>
                        Considered pieces.
                        <br />

                        <i>
                            Better decisions.
                        </i>
                    </h1>

                    <p>
                        A refined storefront where
                        product information is easier
                        to understand before you buy.
                    </p>

                    <Link
                        className="btn dark"
                        to="/products"
                    >
                        Explore collection
                    </Link>

                </div>


                <div className="heroart">

                    <b>
                        FORM
                        <br />
                        MEETS
                        <br />
                        FUNCTION
                    </b>

                </div>

            </section>


            <section className="section">

                <small>
                    CURATED
                </small>

                <h2>
                    Selected essentials
                </h2>


                <div className="grid">

                    {products
                        .slice(0, 4)
                        .map(product => (

                            <ProductCard
                                key={product.id}
                                product={product}
                            />

                        ))}

                </div>

            </section>

        </Layout>

    );

}


/* =========================================================
   PRODUCTS
========================================================= */

function Products() {

    const products =
        useProducts();


    const [
        query,
        setQuery
    ] = useState("");


    useEffect(() => {

        track(
            "page_view",
            "Products"
        );

    }, []);


    function handleSearch(
        value
    ) {

        setQuery(value);

        track(
            "search",
            "Search",
            null,
            {
                query: value
            }
        );

    }


    const filtered =
        products.filter(
            product => (

                (
                    product.name +
                    " " +
                    product.category +
                    " " +
                    product.brand
                )
                    .toLowerCase()
                    .includes(
                        query.toLowerCase()
                    )

            )
        );


    return (

        <Layout>

            <main className="page">

                <small>
                    COLLECTION
                </small>

                <h1>
                    Shop essentials
                </h1>


                <input
                    className="search"
                    placeholder="Search products..."
                    value={query}
                    onChange={event =>
                        handleSearch(
                            event.target.value
                        )
                    }
                />


                <div className="grid">

                    {filtered.map(
                        product => (

                            <ProductCard
                                key={product.id}
                                product={product}
                            />

                        )
                    )}

                </div>

            </main>

        </Layout>

    );

}


/* =========================================================
   KNOW BEFORE YOU BUY
========================================================= */

function ProductInsight({
    product,
    close
}) {

    const [
        data,
        setData
    ] = useState(null);


    const [
        loading,
        setLoading
    ] = useState(true);


    const [
        error,
        setError
    ] = useState("");


    async function loadInsight() {

        setLoading(true);
        setData(null);
        setError("");


        try {

            console.log(
                "Requesting product insight:",
                product.id
            );


            const response =
                await fetch(
                    API +
                    "/api/product-insight",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            product_id:
                                product.id
                        })
                    }
                );


            console.log(
                "Insight API status:",
                response.status
            );


            if (!response.ok) {

                throw new Error(
                    `API returned ${response.status}`
                );

            }


            const result =
                await response.json();


            console.log(
                "Insight API result:",
                result
            );


            setData(result);

        } catch (err) {

            console.error(
                "Product insight error:",
                err
            );


            setError(
                "We couldn't generate the product insight. Please try again."
            );

        } finally {

            setLoading(false);

        }

    }


    useEffect(() => {

        track(
            "product_insight_opened",
            "Product",
            product.id
        );

        loadInsight();

        // eslint-disable-next-line react-hooks/exhaustive-deps

    }, [product.id]);


    return (

        <div className="overlay">

            <aside className="insight">


                {/* CLOSE */}

                <button
                    className="x"
                    onClick={() => {

                        track(
                            "product_insight_closed",
                            "Product",
                            product.id
                        );

                        close();

                    }}
                >
                    ×
                </button>


                {/* HEADER */}

                <small>
                    ✦ KNOW BEFORE YOU BUY
                </small>


                <h2>
                    {product.name}
                </h2>


                <p className="muted">
                    Understand what the specifications
                    actually mean before making a decision.
                </p>


                {/* =================================================
                    LOADING
                ================================================= */}

                {loading && (

                    <div className="loading">

                        <div className="loading-symbol">
                            ✦
                        </div>

                        <p>
                            Analyzing product information...
                        </p>

                        <small>
                            Turning specifications into
                            practical buying context.
                        </small>

                    </div>

                )}


                {/* =================================================
                    ERROR
                ================================================= */}

                {!loading && error && (

                    <div className="insight-error">

                        <p>
                            {error}
                        </p>


                        <button
                            className="btn"
                            onClick={loadInsight}
                        >
                            Try again
                        </button>

                    </div>

                )}


                {/* =================================================
                    RESULT
                ================================================= */}

                {!loading &&
                    !error &&
                    data && (

                    <>


                        {/* =================================================
                            QUICK UNDERSTANDING
                        ================================================= */}

                        {data.summary && (

                            <section>

                                <label>
                                    QUICK UNDERSTANDING
                                </label>

                                <p className="insight-summary">
                                    {data.summary}
                                </p>

                            </section>

                        )}


                        {/* =================================================
                            KEY FACTS
                        ================================================= */}

                        {data.facts?.length > 0 && (

                            <section>

                                <label>
                                    KEY FACTS
                                </label>


                                {data.facts.map(
                                    (
                                        fact,
                                        index
                                    ) => (

                                        <article
                                            className="fact"
                                            key={index}
                                        >

                                            <small>
                                                {fact.attribute}
                                            </small>


                                            <b>
                                                {String(
                                                    fact.value
                                                )}
                                            </b>


                                            {fact.meaning && (

                                                <div
                                                    className="fact-block"
                                                >

                                                    <span>
                                                        WHAT IT MEANS
                                                    </span>

                                                    <p>
                                                        {fact.meaning}
                                                    </p>

                                                </div>

                                            )}


                                            {fact.implication && (

                                                <div
                                                    className="fact-block"
                                                >

                                                    <span>
                                                        WHAT THIS MEANS
                                                        FOR YOU
                                                    </span>

                                                    <p>
                                                        {fact.implication}
                                                    </p>

                                                </div>

                                            )}


                                            {fact.source && (

                                                <div className="source">

                                                    Source:{" "}
                                                    {fact.source}

                                                </div>

                                            )}

                                        </article>

                                    )
                                )}

                            </section>

                        )}


                        {/* =================================================
                            REAL WORLD COMPARISON
                        ================================================= */}

                        {data.comparisons?.length > 0 && (

                            <section>

                                <label>
                                    {
                                        data.comparison_title ||
                                        "REAL-WORLD COMPARISON"
                                    }
                                </label>


                                <p className="muted">

                                    Numbers are easier to
                                    understand when connected
                                    to something familiar.
                                    These comparisons are
                                    approximate context and
                                    do not mean the products
                                    are nutritionally or
                                    functionally identical.

                                </p>


                                {data.comparisons.map(
                                    (
                                        comparison,
                                        index
                                    ) => (

                                        <article
                                            className="comparison"
                                            key={index}
                                        >

                                            <small>
                                                {
                                                    comparison.metric
                                                }
                                            </small>


                                            <b>
                                                {
                                                    comparison.product_value
                                                }
                                            </b>


                                            <strong>
                                                {
                                                    comparison.comparison
                                                }
                                            </strong>


                                            <span>
                                                {
                                                    comparison.note
                                                }
                                            </span>

                                        </article>

                                    )
                                )}

                            </section>

                        )}


                        {/* =================================================
                            TRADE-OFFS
                        ================================================= */}

                        {data.tradeoffs?.length > 0 && (

                            <section>

                                <label>
                                    TRADE-OFFS
                                </label>


                                {data.tradeoffs.map(
                                    (
                                        tradeoff,
                                        index
                                    ) => (

                                        <div
                                            className="tradeoff"
                                            key={index}
                                        >

                                            {tradeoff.advantage && (

                                                <>

                                                    <b>
                                                        ADVANTAGE
                                                    </b>

                                                    <p>
                                                        {
                                                            tradeoff.advantage
                                                        }
                                                    </p>

                                                </>

                                            )}


                                            {tradeoff.consideration && (

                                                <>

                                                    <b>
                                                        CONSIDERATION
                                                    </b>

                                                    <p>
                                                        {
                                                            tradeoff.consideration
                                                        }
                                                    </p>

                                                </>

                                            )}

                                        </div>

                                    )
                                )}

                            </section>

                        )}


                        {/* =================================================
                            CONSIDERATIONS
                        ================================================= */}

                        {data.considerations?.length > 0 && (

                            <section>

                                <label>
                                    THINGS TO CONSIDER
                                </label>


                                <ul>

                                    {data.considerations.map(
                                        (
                                            item,
                                            index
                                        ) => (

                                            <li key={index}>
                                                {item}
                                            </li>

                                        )
                                    )}

                                </ul>

                            </section>

                        )}


                        {/* =================================================
                            MISSING INFORMATION
                        ================================================= */}

                        {data.missing_information?.length > 0 && (

                            <section>

                                <label>
                                    WHAT ISN'T PROVIDED
                                </label>


                                <p className="muted">

                                    These details aren't available
                                    in the supplied product
                                    information. They may be
                                    worth checking before you order.

                                </p>


                                {data.missing_information.map(
                                    (
                                        item,
                                        index
                                    ) => (

                                        <div
                                            className="missing"
                                            key={index}
                                        >

                                            <b>
                                                {
                                                    typeof item ===
                                                    "string"
                                                        ? item
                                                        : item.title
                                                }
                                            </b>


                                            {typeof item !==
                                                "string" &&
                                                item.reason && (

                                                    <span>
                                                        {
                                                            item.reason
                                                        }
                                                    </span>

                                                )}

                                        </div>

                                    )
                                )}

                            </section>

                        )}


                        {/* =================================================
                            WHAT THIS MEANS FOR YOU
                        ================================================= */}

                        {data.bottom_line && (

                            <section>

                                <label>
                                    WHAT THIS MEANS FOR YOU
                                </label>


                                <p className="bottom-line">
                                    {data.bottom_line}
                                </p>

                            </section>

                        )}

                    </>

                )}

            </aside>

        </div>

    );

}


/* =========================================================
   PRODUCT DETAIL
========================================================= */

function ProductDetail() {

    const {
        id
    } = useParams();


    const products =
        useProducts();


    const product =
        products.find(
            item =>
                item.id === id
        );


    const [
        insightOpen,
        setInsightOpen
    ] = useState(false);


    const [
        selectedSize,
        setSelectedSize
    ] = useState("");


    useEffect(() => {

        if (product) {

            track(
                "view_item",
                "Product",
                product.id
            );

        }

    }, [product?.id]);


    if (!product) {

        return (

            <Layout>

                <main className="page">

                    Loading...

                </main>

            </Layout>

        );

    }


    const sizes =
        product.attributes?.sizes || [];


    function chooseSize(
        size
    ) {

        setSelectedSize(
            String(size)
        );


        track(
            "select_size",
            "Product",
            product.id,
            {
                variant:
                    String(size)
            }
        );

    }


    function addToCart() {

        localStorage.setItem(
            "cart",
            JSON.stringify({
                id: product.id,
                size: selectedSize
            })
        );


        track(
            "add_to_cart",
            "Product",
            product.id,
            {
                quantity: 1
            }
        );


        alert(
            "Added to cart"
        );

    }


    return (

        <Layout>

            <main className="detail">


                <div className="bigvisual">

                    <img
                        src={getProductImage(product)}
                        alt={product.name}
                    />

                </div>


                <div className="copy">

                    <small>
                        {product.brand}
                    </small>


                    <h1>
                        {product.name}
                    </h1>


                    <h3>
                        ₹
                        {Number(
                            product.price
                        ).toLocaleString()}
                    </h3>


                    <p>
                        {product.description}
                    </p>


                    <div className="attrs">

                        {Object.entries(
                            product.attributes || {}
                        )
                            .slice(0, 7)
                            .map(
                                (
                                    [
                                        key,
                                        value
                                    ]
                                ) => (

                                    <div
                                        key={key}
                                    >

                                        <small>
                                            {key
                                                .replaceAll(
                                                    "_",
                                                    " "
                                                )}
                                        </small>


                                        <b>
                                            {
                                                Array.isArray(
                                                    value
                                                )
                                                    ? value.join(
                                                        ", "
                                                    )
                                                    : String(value)
                                            }
                                        </b>

                                    </div>

                                )
                            )}

                    </div>


                    {sizes.length > 0 && (

                        <>

                            <small>
                                SELECT SIZE / VARIANT
                            </small>


                            <div className="sizes">

                                {sizes.map(
                                    size => (

                                        <button
                                            key={size}
                                            className={
                                                selectedSize ===
                                                String(size)
                                                    ? "selected"
                                                    : ""
                                            }
                                            onClick={() =>
                                                chooseSize(
                                                    size
                                                )
                                            }
                                        >
                                            {size}
                                        </button>

                                    )
                                )}

                            </div>

                        </>

                    )}


                    <button
                        className="btn dark full"
                        onClick={addToCart}
                    >
                        Add to cart
                    </button>


                    <button
                        className="btn full"
                        onClick={() =>
                            setInsightOpen(true)
                        }
                    >
                        ✦ Know Before You Buy
                    </button>

                </div>

            </main>


            {insightOpen && (

                <ProductInsight
                    product={product}
                    close={() =>
                        setInsightOpen(false)
                    }
                />

            )}

        </Layout>

    );

}


/* =========================================================
   CART
========================================================= */

function Cart() {

    const cartItem =
        JSON.parse(
            localStorage.getItem(
                "cart"
            ) || "null"
        );


    const products =
        useProducts();


    const product =
        products.find(
            productItem =>
                productItem.id ===
                cartItem?.id
        );


    useEffect(() => {

        track(
            "view_cart",
            "Cart"
        );

    }, []);


    return (

        <Layout>

            <main className="page">

                <small>
                    YOUR CART
                </small>


                <h1>
                    Shopping bag
                </h1>


                {!product ? (

                    <p>
                        Your cart is empty.
                    </p>

                ) : (

                    <>

                        <div className="cart">

                            <div>

                                <b>
                                    {product.name}
                                </b>

                                {cartItem?.size && (

                                    <small>
                                        Size:{" "}
                                        {cartItem.size}
                                    </small>

                                )}

                            </div>


                            <span>
                                ₹
                                {Number(
                                    product.price
                                ).toLocaleString()}
                            </span>

                        </div>


                        <Link
                            className="btn dark"
                            to="/checkout"
                        >
                            Continue to checkout
                        </Link>

                    </>

                )}

            </main>

        </Layout>

    );

}


/* =========================================================
   CHECKOUT
========================================================= */

function Checkout() {

    return (

        <Layout>

            <main className="page">

                <small>
                    CHECKOUT
                </small>


                <h1>
                    Complete your order
                </h1>


                <div className="form">

                    <input
                        placeholder="Full name"
                    />


                    <input
                        placeholder="Shipping address"
                    />


                    <input
                        placeholder="Card number (demo only)"
                    />


                    <button
                        className="btn dark"
                        onClick={() => {

                            track(
                                "begin_checkout",
                                "Checkout"
                            );


                            track(
                                "purchase",
                                "Confirmation"
                            );


                            location.href =
                                "/confirmation";

                        }}
                    >
                        Place order
                    </button>

                </div>

            </main>

        </Layout>

    );

}


/* =========================================================
   PRIVACY
========================================================= */

function Privacy() {

    return (

        <Layout>

            <main className="page narrow">

                <small>
                    PRIVACY CENTER
                </small>


                <h1>
                    Transparent by design.
                </h1>


                <h3>
                    Collected
                </h3>

                <p>
                    Anonymous/pseudonymous session ID,
                    event type, timestamp and necessary
                    page/product context.
                </p>


                <h3>
                    Not collected
                </h3>

                <p>
                    Passwords, payment details, email,
                    phone numbers or direct personal
                    identifiers.
                </p>


                <h3>
                    Protection
                </h3>

                <p>
                    Allow-list, data minimization,
                    HMAC-SHA256 pseudonymization,
                    retention and aggregation rules.
                </p>

            </main>

        </Layout>

    );

}


/* =========================================================
   CONFIRMATION
========================================================= */

function Confirmation() {

    return (

        <Layout>

            <main className="success">

                <small>
                    ORDER CONFIRMED
                </small>


                <h1>
                    Thank you.
                </h1>


                <p>
                    Your demo purchase has been
                    recorded as a journey conversion.
                </p>

            </main>

        </Layout>

    );

}


/* =========================================================
   APP
========================================================= */

function App() {

    return (

        <Routes>

            <Route
                path="/"
                element={
                    <Home />
                }
            />


            <Route
                path="/products"
                element={
                    <Products />
                }
            />


            <Route
                path="/products/:id"
                element={
                    <ProductDetail />
                }
            />


            <Route
                path="/cart"
                element={
                    <Cart />
                }
            />


            <Route
                path="/checkout"
                element={
                    <Checkout />
                }
            />


            <Route
                path="/confirmation"
                element={
                    <Confirmation />
                }
            />


            <Route
                path="/privacy"
                element={
                    <Privacy />
                }
            />

        </Routes>

    );

}


/* =========================================================
   ROOT
========================================================= */

createRoot(
    document.getElementById("root")
).render(

    <BrowserRouter>

        <App />

    </BrowserRouter>

);