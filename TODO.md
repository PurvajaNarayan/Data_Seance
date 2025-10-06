# Tasks

1. finding the best way to demonstrate bias in data
    1. What model?
    2. What explainability techniques?

2. Finalizing a set of Guidelines for the project (Minimally Viable) ([cognitive bias codex](https://www.sog.unc.edu/sites/www.sog.unc.edu/files/course_materials/Cognitive%20Biases%20Codex.pdf), [Ethical Principles for Web Machine Learning](https://www.w3.org/TR/webmachinelearning-ethics/))

3. Agent adaptation
    1. Guidelines validation
        - `V1` minimal guidlines fittable in context
        - `V2` ranker for largers set of guidelines
    2. tools
        1. Code reader (reading code to get model and data)
            1. `V1`: manually pass it as arguements
            2. `V2`: Code parsing, agent loads model and data on the fly based on existing code
        2. metadata access
        3. explainability techniques access
            - `V1`: minimal set of explainable techniques, (fittable in context)
            - `V2`: Ranker for larger set of explainability techniques
        4. python runtime to run explainability.

4. Streamlit UI
    1. guidelines page
    1. explanation:
        - `V1` single page prose form
        - `V2`: side by side
            1. plot/visualizations pannel
            2. text explanation pannel

