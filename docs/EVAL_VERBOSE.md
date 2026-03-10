# EVAL_VERBOSE - Response Quality Evaluation

## Overview

The `EVAL_VERBOSE` parameter controls whether detailed response quality metrics are displayed.

## Configuration

Set in `.env` file:

```env
# Show detailed quality evaluation reports
EVAL_VERBOSE=true

# Or just show basic latency metrics (default)
EVAL_VERBOSE=false
```

## Output Comparison

### With `EVAL_VERBOSE=false` (default)
```
Q: How much does 3 hours cost?
A: Parking costs $2 per hour, so 3 hours = $6.
   (Retrieval latency: 0.027s, top=3)
```

### With `EVAL_VERBOSE=true`
```
Q: How much does 3 hours cost?
A: Parking costs $2 per hour, so 3 hours = $6.

⏱️ Latency: retrieval=0.027s | docs=3 | similarity=0.85
🎯 Faithfulness: 0.88/1.00 (hallucinations: none)
📋 Relevance: 0.92 | Completeness: 0.85
✅ Overall: 0.88/1.00 - Very Good ⭐⭐
```

## Quality Levels

| Score Range | Level | Indicator |
|------------|-------|-----------|
| 0.90-1.00 | Excellent | ⭐⭐⭐ |
| 0.80-0.89 | Very Good | ⭐⭐ |
| 0.70-0.79 | Good | ⭐ |
| 0.50-0.69 | Fair | ⚠️ |
| <0.50 | Poor | ❌ |

## How It Works

1. **SimpleRAGChatbot** automatically detects `EVAL_VERBOSE` on initialization
   - If `true`: Creates ResponseEvaluator instance
   - If `false`: Skips evaluation (more efficient)

2. **answer()** method checks `EVAL_VERBOSE` when generating response
   - If `true`: Evaluates response quality with LLM Judge
   - If `false`: Only includes basic retrieval latency

3. **ResponseEvaluator** calculates 4-8 essential metrics:
   - **Line 1**: Latency (retrieval time) + document count + similarity score
   - **Line 2**: Faithfulness score (RAG hallucinations detection)
   - **Line 3**: Relevance + Completeness scores
   - **Line 4**: Overall score and quality level

**Compact design principle**: Shows only what matters, omits noise.

## Implementation Details

### Files
- **Code**: `src/stage1/response_evaluator.py` - Evaluation engine
- **Integration**: `src/stage1/rag_chatbot.py` - Auto-detection and formatting
- **Config**: `.env` - `EVAL_VERBOSE=true/false`

### Key Methods
- `ResponseEvaluator.evaluate_retrieval()` - Calculates retrieval metrics
- `ResponseEvaluator.evaluate_generation()` - Calculates generation metrics
- `ResponseEvaluator._llm_judge_score()` - Gets LLM Judge scores
- `ResponseEvaluator.format_report()` - Returns detailed report (empty if EVAL_VERBOSE=false)
- `ResponseEvaluator.format_metrics_inline()` - Returns inline metrics

### Auto-Detection Logic

In `SimpleRAGChatbot.__init__()`:
```python
if include_evaluation is None:
    include_evaluation = os.getenv("EVAL_VERBOSE", "false").lower() == "true"
```

In `answer()`:
```python
if include_metrics is None:
    include_metrics = os.getenv("EVAL_VERBOSE", "false").lower() == "true"
```

## Performance Impact

- **EVAL_VERBOSE=false**: No overhead, normal performance
- **EVAL_VERBOSE=true**: +3-5 seconds per response (OpenAI API call for evaluation)

## Use Cases

1. **Development**: Set `EVAL_VERBOSE=true` to see quality metrics during development
2. **Production**: Set `EVAL_VERBOSE=false` for fast responses
3. **Testing**: Set `EVAL_VERBOSE=true` to evaluate answer quality
4. **Debugging**: Set `EVAL_VERBOSE=true` to understand why answers score low

## Related Documentation

- [STAGE1.md](STAGE1.md) - Response Quality Evaluation section
- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Design decisions
- [../readme.md](../readme.md) - Main project README
- [src/stage1/response_evaluator.py](../src/stage1/response_evaluator.py) - Source code
