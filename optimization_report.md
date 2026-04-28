# Optimization Report: RankPilot API Execution Time

## Chain-of-Thought Analysis
To determine how to speed up the RankPilot API without modifying the `state` or `schemas`, we must analyze the execution flow of the LangGraph workflow and how the FastAPI server handles requests.

1. **API Layer**: `main.py` uses `BackgroundTasks` to offload the LangGraph workflow, allowing the API to return immediately. The Laravel frontend polls the `/status/{job_id}` endpoint. Therefore, the "API execution time" that the user experiences is the time it takes for the background task to complete the graph iteration.
2. **LangGraph Nodes**: The graph executes sequentially: `classification_node` -> `ingestion_node` -> `sanitizer_node` -> `audit_node` -> `interrogator_node` or `optimize_node` -> `assembly_node` -> `snapshot_generator_node` -> `scheduler_node` -> `executive_writer_node`.
3. **LLM Calls (The Bottleneck)**: Almost every node makes synchronous HTTP requests to an LLM provider (OpenAI or OpenRouter). These are blocking operations.
4. **`optimizer_node`**: This node loops through multiple work highlight summaries and matters, making individual, synchronous LLM calls for each (`summary_chain.invoke`, `matter_chain.invoke`).
5. **`sanitizer_node`**: This node chunks long strings into batches and processes them synchronously one by one.
6. **Data Processing**: Extracting text from PDFs and assembling Word documents involve heavy I/O and CPU-bound operations.
7. **Pydantic Validation**: While `state` and `schema` structures cannot be changed, the *way* they are dumped and loaded (`model_dump()`, `**kwargs`) can incur CPU overhead, especially recursively.

Given these observations, our focus must be on parallelizing LLM calls, optimizing the way requests are batched, utilizing asynchronous Python features, caching where possible, and optimizing JSON serialization/deserialization.

---

## 10 Methods to Optimize Execution Speed

Here are 10 optimization methods to reduce the execution time of the RankPilot API without altering the `state` or `schemas`:

### 1. Implement Asynchronous LLM Calls (Asyncio / LangChain Ainvoke)
**The Bottleneck:** Currently, LangGraph nodes (like `extractor.py`, `optimizer.py`, `sanitizer.py`) use the synchronous `.invoke()` method on LangChain chains. This blocks the entire thread waiting for the LLM API to respond.
**The Solution:** Convert the node functions to `async def` and use `.ainvoke()` or `.abatch()` provided by LangChain. FastAPI and LangGraph both support async nodes. This is the single most impactful change you can make, as it allows the server to handle other requests while waiting for the LLM.

### 2. Parallelize Iterative LLM Calls in `optimize_node`
**The Bottleneck:** In `src/agents/optimizer.py`, the code iterates over `work_highlights_summaries`, `publishable_matters`, and `confidential_matters` using a standard `for` loop, waiting for each LLM response before starting the next.
**The Solution:** Use `asyncio.gather()` (if using async) or `concurrent.futures.ThreadPoolExecutor` to run these independent LLM calls concurrently. For example, all 10 summaries can be optimized simultaneously, reducing the total time for that section from `10 x N seconds` to just `1 x N seconds`.

### 3. Parallelize Batch Processing in `sanitizer_node`
**The Bottleneck:** `src/agents/sanitizer.py` splits long text fields into batches and processes them sequentially in a `for` loop.
**The Solution:** Similar to the optimizer, dispatch all batches to the LLM concurrently using a `ThreadPoolExecutor` or `asyncio.gather()`. Since each batch processes a distinct subset of fields, there are no race conditions when updating the `submission_dict` if mapped correctly.

### 4. Optimize the `model_dump()` Serialization Overhead
**The Bottleneck:** Pydantic's `model_dump(exclude_none=True)` and initialization (`Legal500Submission(**submission_dict)`) are called frequently across nodes to convert objects to dictionaries and back. This CPU-bound operation adds up on large nested schemas.
**The Solution:** If you only need to read data (like in `audit_node` or `interrogator_node`), avoid re-instantiating the entire Pydantic model unless you are updating it. For JSON serialization during Pydantic dumps, consider installing `orjson` and configuring Pydantic to use it, as it is significantly faster than the standard library `json`.

### 5. Consolidate Chains in `snapshot_generator_node` and `scheduler_node`
**The Bottleneck:** Depending on the implementation of these Act 3 nodes, they might be making multiple sequential LLM calls to generate different sections of the strategic diagnostic.
**The Solution:** Combine prompts. Ask the LLM to output a single structured JSON containing the `PositioningCore`, `BlindSpots`, and `Milestones` in one go. Using `with_structured_output` with a master schema for the response reduces the network round-trips to the LLM provider.

### 6. Introduce LLM Response Caching
**The Bottleneck:** Repeated testing or identical document processing requests will re-trigger the same LLM inferences, wasting time and credits.
**The Solution:** Implement caching at the LLM level. LangChain supports caching (e.g., `from langchain.cache import SQLiteCache`, `set_llm_cache`). If the `ingestion_node` receives the exact same `extracted_text` and `metadata`, it can return the cached structured schema instantly.

### 7. Optimize LLM Models and Max Tokens
**The Bottleneck:** Generating too many tokens or using overly complex models for simple tasks slows down generation time (Time to First Token and Tokens Per Second).
**The Solution:**
- Ensure that `max_tokens` is strictly limited in all structured output calls to prevent the model from over-generating.
- For simpler tasks like `process_answer_node` (determining 'fill', 'dismiss', 'clarify'), consider using a much faster model (e.g., `gpt-4o-mini` instead of a larger model, or Claude 3.5 Haiku) if the environment allows it, as these routing decisions don't need deep reasoning.

### 8. Streamline PDF / DOCX Text Extraction
**The Bottleneck:** I/O operations and regex chunking in PDF/DOCX parsing (in `src/io/`) can be CPU-intensive and block the event loop.
**The Solution:** Offload the document extraction logic to a separate process using `ProcessPoolExecutor`. This prevents CPU-bound tasks like table parsing with `PyMuPDF` or `python-docx` from blocking the async event loop of the FastAPI server, allowing the workflow to reach the `ingestion_node` faster.

### 9. Fast-Fail in `audit_node`
**The Bottleneck:** The `audit_node` iterates deeply through required fields using a custom `get_nested_value` dot-notation parser in `Legal500Strategy.audit()`.
**The Solution:** The dot-notation parser splits strings and loops over dictionaries recursively for every field in the YAML. Pre-compile these paths or use a faster JSONPath library (like `jsonpath-ng` or `jmespath`) to evaluate missing fields. Additionally, if the total number of missing fields is huge, cap the maximum number of active gaps returned to Laravel to process the most critical ones first, rather than traversing the entire schema every time.

### 10. Bypass the LangGraph Streaming Overhead for API Polling
**The Bottleneck:** In `main.py`, the workflow runs using `workflow.stream()` to update the `JOBS_DB` progress map at every node.
**The Solution:** While `.stream()` is great for UX, iterating over the graph state dictionary at every step adds a slight overhead. Ensure that the `state_update` dictionary merges efficiently. More importantly, instead of having Laravel poll the API constantly, consider implementing WebSockets or Server-Sent Events (SSE). This reduces the HTTP overhead of constant polling and delivers the final JSON payload instantly the millisecond the workflow completes.
