from backend.ai.llm_parser import parse_query_to_dsl
from backend.ai.validator import validate_dsl
from backend.ai.compiler import compile_and_run

def run_engine(query: str):
    dsl = parse_query_to_dsl(query)
    validate_dsl(dsl)
    results = compile_and_run(dsl)
    return dsl, results
