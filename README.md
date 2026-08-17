# Causal and Simulation-Based Analysis of Digital User Behavior

A privacy-aware research prototype that reconstructs digital user journeys,
tests which factors *actually* influence outcomes using causal inference,
simulates hypothetical interventions, and ranks them with an explainable,
evidence-based recommendation engine.

This is a university-level research/engineering prototype, not a commercial
product. It runs entirely on synthetic, privacy-safe data by default.

## Problem statement

Behavioral analytics dashboards typically report correlations ("users who
saw feature X converted more") without establishing whether X actually
*caused* the improvement, and rarely let a team test a change before
building it. This project builds a small but complete pipeline that goes
one step further at each stage:

1. **What happened?** — journey reconstruction and behavioral analytics
2. **What appears to influence the outcome?** — causal inference (DoWhy)
3. **What could happen if we change something?** — discrete-event
   simulation (SimPy)
4. **Which intervention should we prioritize?** — an automated,
   transparently-scored recommendation engine
5. **Why?** — a deterministic, evidence-grounded explanation for every
   recommendation

## Objectives

- Reconstruct non-linear user journeys from raw, privacy-minimized event data
- Identify behavioral segments without forcing labels onto the data
- Estimate causal effects with explicit confounder adjustment, confidence
  intervals, and refutation checks — never a hard-coded number
- Provide a what-if simulator whose every output is clearly labeled
  Simulated/Estimated
- Rank candidate interventions using a documented, transparent scoring
  formula (not a black box, not an LLM)
- Demonstrate a genuinely privacy-aware data design (pseudonymization,
  minimization, aggregation thresholds, configurable retention)

## Architecture

```
Event Data -> Privacy / Data Minimization -> PostgreSQL -> Data Processing
  -> User Journey Reconstruction -> Behavioral Analytics
  -> Behavioral Segmentation -> Causal Inference -> Intervention Identification
  -> What-If Simulation -> Intervention Ranking -> Explainable Recommendation
  -> Interactive Streamlit Dashboard
```

```
user_journey_intelligence/
├── app.py                     # Streamlit entry point / navigation
├── pages/                     # One file per dashboard page
├── src/                       # All non-UI logic (data, analytics, causal, sim)
├── sql/                       # PostgreSQL schema + optional seed
├── scripts/                   # init / generate / pipeline / analysis runners
├── tests/                     # pytest suite
├── data/sample/                # (empty by default) local artifact folder
├── .env.example
└── requirements.txt
```

## Technology stack

| Concern            | Technology                     |
|---------------------|---------------------------------|
| Dashboard            | Streamlit                      |
| Database              | PostgreSQL (SQLAlchemy access layer) |
| Data processing        | Polars, Pandas, NumPy           |
| Visualization           | Plotly                         |
| Causal inference         | DoWhy                          |
| Simulation                | SimPy                          |
| ML / statistics             | scikit-learn, SciPy, statsmodels |
| Configuration                  | python-dotenv                  |

## Installation

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### PostgreSQL setup (recommended)

1. Create a database, e.g. `createdb user_journey_db`
2. Set `DATABASE_URL` in `.env`:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/user_journey_db
   ```
3. Apply the schema and generate data (next section).

If `DATABASE_URL` is left unset, the app automatically falls back to a
local SQLite file at `data/local_dev.db` so it remains runnable without a
Postgres server for quick evaluation — every module talks to the database
through the same SQLAlchemy-based access layer (`src/database.py`)
regardless of which backend is active.

## Data generation & pipeline

Run the whole pipeline in one command:

```bash
python scripts/run_pipeline.py --sessions 6000 --reset
```

This will: initialize the schema, generate synthetic sessions/events,
reconstruct journeys, compute behavioral analytics and segments, run all
predefined causal analyses, and build ranked, explained recommendations —
storing results back into the database for the dashboard to read.

Individual steps can also be run on their own:

```bash
python scripts/init_database.py
python scripts/generate_data.py --sessions 6000 --reset
python scripts/run_analysis.py     # re-run analytics/causal/recs on existing data
```

## Processing pipeline

Raw events are cleaned and type-normalized with Polars
(`src/data_processing.py`), then walked session-by-session to reconstruct
journeys (`src/journey_reconstruction.py`): length, duration, unique vs.
repeated pages, loops, entry/exit pages, conversion, and abandonment stage.
Behavioral KPIs, drop-off analysis, and an interpretable engagement score
are computed in `src/behavioral_analysis.py`. `src/segmentation.py` then
clusters sessions (K-Means over journey/engagement features) and labels
each resulting cluster by its own measured profile rather than forcing a
fixed taxonomy.

## Causal methodology

`src/causal_analysis.py` uses DoWhy's backdoor-adjustment estimator to
test predefined causal questions (e.g. "does reducing registration
friction increase conversion?"), adjusting for `prior_engagement` as an
observed confounder. Every result includes a 95% confidence interval, the
sample size used, the stated assumptions, and a placebo-treatment
refutation check. If the sample is too small or too imbalanced between
treatment/control, the function returns
`insufficient_evidence` and the UI displays that literally instead of a
fabricated number. If DoWhy itself is unavailable or errors, the module
falls back to an explicitly-labeled adjusted OLS estimate with a
bootstrap confidence interval — never a hard-coded value.

## Simulation methodology

`src/simulation_engine.py` builds a real SimPy discrete-event simulation
of the funnel: each simulated session is an independent SimPy process
whose branch probabilities are driven by the same functional relationships
used to generate the synthetic ground truth (see `src/data_generator.py`),
but parameterized by user-adjustable sliders in the What-If Simulator
page. Every run actually executes; results include a bootstrap
uncertainty band and are labeled Simulated/Estimated everywhere they
appear in the UI.

## Recommendation methodology

`src/recommendation_engine.py` combines, per candidate intervention: the
causal effect estimate (preferred when available), the simulated
improvement, the share of sessions the intervention could plausibly
affect (`src/intervention_engine.py`), an engineering-judgment complexity
and risk rating (explicitly documented as judgment, not derived from
data), and an uncertainty penalty derived from the causal CI width /
simulation bootstrap. These are combined via a transparent weighted
formula into a 0–10 score. `src/explanation_engine.py` renders a
deterministic, evidence-grounded explanation for every recommendation; an
LLM is used only optionally, only to rephrase an already-correct
explanation into plainer language, and is explicitly instructed never to
introduce new figures. The system is fully functional with no LLM API key
configured.

## Privacy methodology

See the in-app **Privacy Center** page and `src/privacy.py`. In summary:
pseudonymous session/user tokens generated via a keyed HMAC-SHA256 hash,
an explicit field allow-list enforced before persistence
(`minimize_event` / `minimize_session`), a minimum group size
(`MIN_AGGREGATION_GROUP_SIZE = 5`) before any segment statistic is
considered reportable, and a configurable retention window
(`DATA_RETENTION_DAYS`). No claim of legal compliance with any specific
regulation is made anywhere in the code or UI.

## Running the dashboard

```bash
streamlit run app.py
```

The dashboard reads directly from the configured database (PostgreSQL or
the SQLite fallback) — there is no manual export/import step. Use the
**Refresh now** button on the System Status page, or wait for the
configured cache TTL, to pick up newly generated data.

## Testing

```bash
pytest
```

Covers data generation/processing, journey reconstruction, simulation
sanity checks (e.g. lower friction should on average improve simulated
conversion), recommendation-support calculations, privacy/pseudonymization
behavior, and empty-dataset handling.

## Limitations

- All demonstrated results are computed against **synthetic** data. The
  causal relationships are real in the sense that they are genuinely
  present in the generated data and genuinely recovered by the pipeline,
  but they do not describe any real product or real users.
- The causal analysis uses a single, fairly simple backdoor-adjustment
  estimator (linear regression) and one observed confounder per question;
  a production deployment would want a richer confounder set and
  sensitivity analysis beyond the placebo refutation check included here.
- The recommendation scoring formula is intentionally simple and
  transparent rather than optimized; the weights are a documented
  starting point, not a tuned model.
- The optional LLM summary feature has not been extensively evaluated for
  faithfulness beyond the explicit "do not introduce new numbers"
  instruction in its prompt.

## Future work

- Support ingesting real, already-anonymized event data alongside the
  synthetic generator (the schema and pipeline are designed to make this
  a drop-in replacement — see `scripts/run_analysis.py`).
- Add additional causal estimators (e.g. propensity score matching,
  instrumental variables) and richer refutation suites.
- Extend simulation scenarios to allow saving and comparing arbitrary
  named user-defined scenarios over time.
- Add role-based access and audit logging if this were ever adapted
  beyond a research prototype.
