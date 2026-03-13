import sys
import json
from rag.llmrag import fact_check

def main():
    query = "What is the PM-KISAN scheme?"
    print(f"Query: {query}")
    try:
        result = fact_check(query)
        print("Result:")
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("answer") else 1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
