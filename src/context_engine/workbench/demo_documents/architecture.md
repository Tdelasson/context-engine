# Deterministic runtime architecture

Context Engine separates probabilistic model proposals from deterministic application behavior.
The Agent Runtime owns state transitions. A model may propose a tool call, but the Tool Runtime
performs registry lookup, schema validation, policy evaluation, optional approval, execution, and
structured tracing. Provider-specific model behavior stays behind the Model Gateway.
