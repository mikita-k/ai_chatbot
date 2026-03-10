"""
Response Evaluation System for RAG Chatbot

Provides evaluation of RAG response quality using LLM as Judge:
1. Retrieval Metrics - latency, document count, similarity scores
2. Generation Metrics - response length, token count
3. LLM Judge Scores - relevance, faithfulness, completeness, conciseness
4. Overall Score - weighted quality assessment
"""

import os
import json
from typing import List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RetrievalMetrics:
    """Metrics for the retrieval stage"""
    latency: float
    num_documents: int
    avg_similarity: float
    max_similarity: float
    min_similarity: float
    sources: List[str] = None

    def __post_init__(self):
        if self.sources is None:
            self.sources = []


@dataclass
class GenerationMetrics:
    """Metrics for the generation stage"""
    length: int
    token_count: int
    contains_citations: bool
    uses_llm: bool


@dataclass
class LLMJudgeResult:
    """Result from LLM judge evaluation"""
    relevance_score: float
    faithfulness_score: float
    completeness_score: float
    conciseness_score: float
    overall_score: float
    explanation: str
    critique: str
    suggestions: List[str] = None

    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


@dataclass
class ResponseEvaluation:
    """Complete evaluation of a response"""
    query: str
    response: str
    ground_truth: Optional[str]
    retrieval_metrics: RetrievalMetrics
    generation_metrics: GenerationMetrics
    llm_judge_result: Optional[LLMJudgeResult]
    overall_score: float
    timestamp: str


class ResponseEvaluator:
    """
    Comprehensive evaluation system for RAG responses.

    Uses LLM as judge to evaluate quality by comparing:
    - Generated response vs ground truth
    - Relevance to query
    - Faithfulness to sources
    - Completeness and conciseness
    """

    def __init__(self, use_llm_judge: bool = True, model: str = None):
        """
        Initialize evaluator.

        Args:
            use_llm_judge: Whether to use LLM for quality judgment
            model: OpenAI model name (default: gpt-3.5-turbo)
        """
        self.use_llm_judge = use_llm_judge
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self._llm_client = None

    def _get_llm_client(self):
        """Lazy load OpenAI client"""
        if self._llm_client is None:
            try:
                import openai
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise RuntimeError("OPENAI_API_KEY not set")
                if hasattr(openai, "OpenAI"):
                    self._llm_client = openai.OpenAI(api_key=api_key)
                else:
                    openai.api_key = api_key
                    self._llm_client = openai
            except Exception as e:
                raise RuntimeError(f"Failed to initialize OpenAI client: {e}")
        return self._llm_client

    def evaluate_retrieval(
        self,
        query: str,
        retrieved_docs: List[Tuple[int, float]],
        docs_text: List[str],
        latency: float
    ) -> RetrievalMetrics:
        """
        Evaluate retrieval stage metrics.

        Args:
            query: User query
            retrieved_docs: List of (doc_index, similarity_score) tuples
            docs_text: Full text of all documents
            latency: Time taken for retrieval (seconds)

        Returns:
            RetrievalMetrics object
        """
        if not retrieved_docs:
            return RetrievalMetrics(
                latency=latency,
                num_documents=0,
                avg_similarity=0.0,
                max_similarity=0.0,
                min_similarity=0.0,
                sources=[]
            )

        similarities = [score for _, score in retrieved_docs]
        sources = [docs_text[idx] for idx, _ in retrieved_docs if idx < len(docs_text)]

        return RetrievalMetrics(
            latency=latency,
            num_documents=len(retrieved_docs),
            avg_similarity=sum(similarities) / len(similarities),
            max_similarity=max(similarities),
            min_similarity=min(similarities),
            sources=sources
        )

    def evaluate_generation(
        self,
        response: str,
        uses_llm: bool
    ) -> GenerationMetrics:
        """
        Evaluate generation stage metrics.

        Args:
            response: Generated response text
            uses_llm: Whether LLM was used for generation

        Returns:
            GenerationMetrics object
        """
        # Count tokens approximately (rough estimate: 1 token ≈ 4 chars)
        token_count = len(response) // 4

        return GenerationMetrics(
            length=len(response),
            token_count=token_count,
            contains_citations=bool("[similarity=" in response or "[source" in response),
            uses_llm=uses_llm
        )

    def _llm_judge_score(
        self,
        query: str,
        response: str,
        ground_truth: Optional[str] = None,
        sources: Optional[List[str]] = None
    ) -> LLMJudgeResult:
        """
        Use LLM as judge to evaluate response quality.

        Args:
            query: Original user query
            response: Generated response
            ground_truth: Expected/gold standard answer (optional)
            sources: Retrieved source documents

        Returns:
            LLMJudgeResult with detailed scoring
        """
        if not self.use_llm_judge:
            return None

        try:
            client = self._get_llm_client()
        except Exception as e:
            print(f"Warning: LLM judge unavailable: {e}")
            return None

        # Build evaluation prompt
        sources_text = ""
        if sources:
            sources_text = "\n\nRetrieved Sources:\n"
            sources_text += "\n---\n".join(f"Source {i+1}:\n{src}" for i, src in enumerate(sources[:3]))

        ground_truth_text = ""
        if ground_truth:
            ground_truth_text = f"\n\nExpected/Ground Truth Answer:\n{ground_truth}"

        evaluation_prompt = f"""You are an expert evaluator of AI-generated responses. 
Evaluate the following response to a user query on multiple dimensions.

User Query:
{query}

Generated Response:
{response}
{sources_text}
{ground_truth_text}

Evaluate the response on the following criteria (0-1 scale):

1. RELEVANCE: Is the response relevant and directly addressing the query?
2. FAITHFULNESS: Does the response accurately reflect the retrieved sources without hallucination?
3. COMPLETENESS: Does the response adequately answer the question?
4. CONCISENESS: Is the response concise without being too brief?

Provide your evaluation in the following JSON format:
{{
    "relevance_score": <0-1>,
    "faithfulness_score": <0-1>,
    "completeness_score": <0-1>,
    "conciseness_score": <0-1>,
    "overall_score": <0-1>,
    "explanation": "<brief overall summary>",
    "critique": "<specific strengths and weaknesses>",
    "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
}}

IMPORTANT: Respond with ONLY the JSON object, no additional text."""

        try:
            if hasattr(client, 'chat'):
                # Old OpenAI API
                response_obj = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": evaluation_prompt}],
                    temperature=0.1,
                    max_tokens=500
                )
                result_text = response_obj.choices[0].message.content
            else:
                # Fallback to old interface
                response_obj = client.ChatCompletion.create(
                    model=self.model,
                    messages=[{"role": "user", "content": evaluation_prompt}],
                    temperature=0.1,
                    max_tokens=500
                )
                result_text = response_obj["choices"][0]["message"]["content"]

            # Parse JSON response
            result_dict = json.loads(result_text)

            return LLMJudgeResult(
                relevance_score=float(result_dict.get("relevance_score", 0.0)),
                faithfulness_score=float(result_dict.get("faithfulness_score", 0.0)),
                completeness_score=float(result_dict.get("completeness_score", 0.0)),
                conciseness_score=float(result_dict.get("conciseness_score", 0.0)),
                overall_score=float(result_dict.get("overall_score", 0.0)),
                explanation=result_dict.get("explanation", ""),
                critique=result_dict.get("critique", ""),
                suggestions=result_dict.get("suggestions", [])
            )

        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse LLM judge response: {e}")
            return None
        except Exception as e:
            print(f"Warning: LLM judge error: {e}")
            return None

    def evaluate(
        self,
        query: str,
        response: str,
        retrieval_metrics: RetrievalMetrics,
        generation_metrics: GenerationMetrics,
        ground_truth: Optional[str] = None
    ) -> ResponseEvaluation:
        """
        Perform complete evaluation of a response.

        Args:
            query: User query
            response: Generated response
            retrieval_metrics: Retrieval stage metrics
            generation_metrics: Generation stage metrics
            ground_truth: Expected answer for comparison (optional)

        Returns:
            ResponseEvaluation with all metrics and scores
        """
        from datetime import datetime

        # Get LLM judge evaluation
        llm_judge_result = self._llm_judge_score(
            query,
            response,
            ground_truth,
            retrieval_metrics.sources
        )

        # Calculate overall score
        overall_score = 0.0
        if llm_judge_result:
            # Weight the LLM judge scores
            overall_score = (
                llm_judge_result.relevance_score * 0.3 +      # 30% relevance
                llm_judge_result.faithfulness_score * 0.3 +    # 30% faithfulness
                llm_judge_result.completeness_score * 0.2 +    # 20% completeness
                llm_judge_result.conciseness_score * 0.1 +     # 10% conciseness
                min(retrieval_metrics.avg_similarity, 1.0) * 0.1  # 10% retrieval quality
            )

        return ResponseEvaluation(
            query=query,
            response=response,
            ground_truth=ground_truth,
            retrieval_metrics=retrieval_metrics,
            generation_metrics=generation_metrics,
            llm_judge_result=llm_judge_result,
            overall_score=overall_score,
            timestamp=datetime.now().isoformat()
        )

    def format_report(self, evaluation: ResponseEvaluation) -> str:
        """
        Format evaluation as compact human-readable report (4-8 lines).
        Shows only the most essential metrics.

        Args:
            evaluation: ResponseEvaluation object

        Returns:
            Formatted report string (empty if EVAL_VERBOSE=false)
        """
        # Check EVAL_VERBOSE env var
        eval_verbose = os.getenv("EVAL_VERBOSE", "false").lower() == "true"
        if not eval_verbose:
            return ""

        lines = []

        # Essential metrics only
        if evaluation.llm_judge_result:
            judge = evaluation.llm_judge_result

            # Line 1-2: Retrieval & Generation
            latency = evaluation.retrieval_metrics.latency
            gen_time = 0  # generation happens before evaluation
            lines.append(f"⏱️ Latency: retrieval={latency:.3f}s | docs={evaluation.retrieval_metrics.num_documents} | "
                        f"similarity={evaluation.retrieval_metrics.avg_similarity:.2f}")

            # Line 3: Critical metric - Faithfulness (hallucinations)
            lines.append(f"🎯 Faithfulness: {judge.faithfulness_score:.2f}/1.00 (hallucinations: {'none' if judge.faithfulness_score >= 0.8 else 'detected'})")

            # Line 4: Relevance & Completeness
            lines.append(f"📋 Relevance: {judge.relevance_score:.2f} | Completeness: {judge.completeness_score:.2f}")

            # Line 5: Overall score & quality level
            score = evaluation.overall_score
            level = self._score_to_level(score)
            lines.append(f"✅ Overall: {score:.2f}/1.00 - {level}")

        return "\n".join(lines)

    @staticmethod
    def _score_to_level(score: float) -> str:
        """Convert numeric score to quality level"""
        if score >= 0.9:
            return "Excellent ⭐⭐⭐"
        elif score >= 0.8:
            return "Very Good ⭐⭐"
        elif score >= 0.7:
            return "Good ⭐"
        elif score >= 0.5:
            return "Fair ⚠️"
        else:
            return "Poor ❌"

    def format_metrics_inline(self, evaluation: ResponseEvaluation) -> str:
        """
        Format metrics for inline display (compact format).

        Args:
            evaluation: ResponseEvaluation object

        Returns:
            Compact metrics string
        """
        parts = []

        # Retrieval
        parts.append(f"Retrieval latency: {evaluation.retrieval_metrics.latency:.3f}s, "
                    f"top={evaluation.retrieval_metrics.num_documents}")

        # Similarity
        if evaluation.retrieval_metrics.num_documents > 0:
            parts.append(f"similarity: {evaluation.retrieval_metrics.avg_similarity:.3f} "
                        f"(max: {evaluation.retrieval_metrics.max_similarity:.3f})")
            parts.append(f"retrieval_quality: {evaluation.retrieval_metrics.avg_similarity:.2f}/1.00")

        # Generation
        parts.append(f"length: {evaluation.generation_metrics.token_count} tokens")

        # LLM Judge
        if evaluation.llm_judge_result:
            judge = evaluation.llm_judge_result
            parts.append(f"quality: relevance={judge.relevance_score:.2f}, "
                        f"faithful={judge.faithfulness_score:.2f}, "
                        f"complete={judge.completeness_score:.2f}")
            parts.append(f"overall: {evaluation.overall_score:.2f}/1.00 "
                        f"({self._score_to_level(evaluation.overall_score)})")

        return " | ".join(parts)


# Helper function to integrate with existing RAG chatbot
def evaluate_response(
    query: str,
    response: str,
    retrieved_hits: List[Tuple[int, float]],
    docs: List[str],
    latency: float,
    uses_llm: bool = False,
    ground_truth: Optional[str] = None,
    use_judge: bool = True
) -> ResponseEvaluation:
    """
    Convenience function to evaluate a single response.

    Args:
        query: User query
        response: Generated response
        retrieved_hits: Retrieved (doc_index, similarity_score) tuples
        docs: Document texts
        latency: Retrieval time
        uses_llm: Whether LLM was used
        ground_truth: Expected answer
        use_judge: Whether to use LLM judge

    Returns:
        ResponseEvaluation object
    """
    evaluator = ResponseEvaluator(use_llm_judge=use_judge)

    retrieval_metrics = evaluator.evaluate_retrieval(query, retrieved_hits, docs, latency)
    generation_metrics = evaluator.evaluate_generation(response, uses_llm)

    return evaluator.evaluate(
        query,
        response,
        retrieval_metrics,
        generation_metrics,
        ground_truth
    )
