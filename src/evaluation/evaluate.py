import asyncio
import pandas as pd
from typing import List, Dict
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from src.agents.langgraph_workflow import RAGWorkflow
from config.settings import settings

class RAGEvaluator:
    def __init__(self):
        self.rag_workflow = RAGWorkflow()
        # Ragas needs its own LLM/Embeddings instances
        self.eval_llm = ChatOpenAI(
            model=settings.llm.openai_model,
            api_key=settings.llm.openai_api_key
        )
        self.eval_embeddings = OpenAIEmbeddings(
            model=settings.llm.embedding_model,
            api_key=settings.llm.openai_api_key
        )

    async def generate_answers(self, questions: List[str], ground_truths: List[str]) -> Dict:
        """
        Run the RAG pipeline for a list of questions to generate answers and contexts.
        """
        answers = []
        contexts = []

        print(f"Generating answers for {len(questions)} questions...")
        
        for question in questions:
            try:
                result = await self.rag_workflow.app.ainvoke({
                    "question": question,
                    "iterations": 0
                })
                
                answers.append(result.get("generation", ""))
                # Ragas expects a list of strings for contexts
                contexts.append(result.get("documents", []))
                
            except Exception as e:
                print(f"Error processing question '{question}': {e}")
                answers.append("Error")
                contexts.append([])

        return {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths
        }

    def run_evaluation(self, data: Dict) -> Dict:
        """
        Run Ragas evaluation on the generated data.
        """
        print("Running Ragas evaluation...")
        
        dataset = Dataset.from_dict(data)
        
        results = evaluate(
            dataset=dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            ],
            llm=self.eval_llm,
            embeddings=self.eval_embeddings
        )
        
        return results

async def main():
    # Example Golden Dataset (In production, load this from a file)
    test_questions = [
        "What is the architecture of the system?",
        "How does the hybrid search work?",
        "What databases are used?"
    ]
    
    test_ground_truths = [
        "The system uses a scalable context-aware search architecture with hybrid search (Milvus + Elasticsearch), agentic orchestration (LangGraph), and enterprise data integration (Cloud SQL + Snowflake).",
        "Hybrid search combines dense vector retrieval from Milvus and sparse lexical retrieval from Elasticsearch using Reciprocal Rank Fusion (RRF).",
        "The system uses Milvus for vector storage, Elasticsearch for text search, PostgreSQL (Cloud SQL) for user history, and Snowflake for analytics."
    ]
    
    evaluator = RAGEvaluator()
    
    # 1. Generate Answers
    data = await evaluator.generate_answers(test_questions, test_ground_truths)
    
    # 2. Run Evaluation
    results = evaluator.run_evaluation(data)
    
    print("\n=== Evaluation Results ===")
    print(results)
    
    # Save results
    df = results.to_pandas()
    df.to_csv("evaluation_results.csv", index=False)
    print("\nResults saved to evaluation_results.csv")

if __name__ == "__main__":
    asyncio.run(main())
