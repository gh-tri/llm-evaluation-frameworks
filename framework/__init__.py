"""
The `framework` package: a standalone, presentation-focused deep-dive into
one evaluation/observability framework at a time - separate from the main
Streamlit app (frontend/app.py) on purpose. That app is about YOUR data
(six stations, real scores, comparisons). This one is about the TOOLS
themselves: how a framework works, when to reach for it, and a live,
editable metric you can run in front of an audience.

Run it with:  uv run streamlit run framework/app.py

Structure:
  catalog.py       - the actual content (how it works / integration / when
                      to use / impressive points / pain points) per framework.
  samples.py        - tiny, presentation-friendly example inputs. Deliberately
                      NOT the project's Northwind Robotics dataset - a
                      generic customer-support scenario anyone in the room
                      understands instantly, with one deliberately good,
                      one mediocre, and one bad answer so a live metric run
                      visibly discriminates between them.
  live_deepeval.py  - the real, live DeepEval G-Eval call. No mocks, no
                      pre-computed numbers - typing a new criteria and
                      clicking "run" makes a real judge-model API call.
  app.py            - the Streamlit page that ties it together.
"""
