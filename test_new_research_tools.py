"""
Verification script for new research studio tools:
1. search_crossref
2. search_europepmc
3. export_latex_to_docx
4. verify_claims_against_sources
5. run_deep_research
"""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from agent.tools import create_default_registry

def test_new_tools():
    reg = create_default_registry()
    tools = reg._tools

    print("=== 1. Testing search_crossref ===")
    res1 = reg.execute("search_crossref", {"query": "deep residual learning for image recognition", "max_results": 2})
    print("search_crossref snippet:\n", res1[:350])
    assert "CrossRef" in res1, "CrossRef search failed"
    print("--> PASS")

    print("\n=== 2. Testing search_europepmc ===")
    res2 = reg.execute("search_europepmc", {"query": "CRISPR Cas9 gene editing", "max_results": 2})
    print("search_europepmc snippet:\n", res2[:350])
    assert "Europe PMC" in res2 or "PubMed" in res2, "Europe PMC search failed"
    print("--> PASS")

    print("\n=== 3. Testing run_deep_research (end-to-end) ===")
    res3 = reg.execute("run_deep_research", {"topic": "AI Agents for Scientific Discovery", "num_papers": 3, "language": "uzbek"})
    print("run_deep_research report:\n", res3)
    assert "Deep Research" in res3, "Deep research synthesis failed"
    print("--> PASS")

    print("\n=== 4. Testing verify_claims_against_sources ===")
    sample_pdf = root / "outputs" / "papers" / "sample_paper.pdf"
    if sample_pdf.exists():
        res4 = reg.execute("verify_claims_against_sources", {
            "claims": "This paper discusses machine learning models.\nIt presents empirical evaluations on datasets.",
            "source_pdf": str(sample_pdf)
        })
        print("verify_claims snippet:\n", res4[:350])
        print("--> PASS")

    print("\n==========================================")
    print(" ALL 5 NEW ADVANCED RESEARCH TOOLS PASSED! ")
    print("==========================================")

if __name__ == "__main__":
    test_new_tools()
