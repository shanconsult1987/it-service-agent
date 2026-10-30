
"""Ad hoc OpenAI LLM call with token and latency monitoring.

Run from the repository root:
    python -m app.llm_demo

Requires:
    OPENAI_API_KEY environment variable
    openai Python SDK
"""
import os
import sys
import time

from openai import OpenAI

from app.monitoring import record_llm_call, snapshot


def run_demo():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. "
            "Set it in PowerShell before running this demo."
        )

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    prompt = (
        "You are an IT service desk assistant. "
        "Explain three troubleshooting steps for a user "
        "whose corporate VPN keeps disconnecting. "
        "Keep the answer concise and safe. "
        "Do not ask the user to disable security controls."
    )

    started = time.perf_counter()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise and safe IT support assistant. "
                        "Do not recommend bypassing security controls."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=1.0
        )

        elapsed_ms = (
            time.perf_counter() - started
        ) * 1000

        usage = response.usage

        prompt_tokens = (
            usage.prompt_tokens if usage else None
        )
        completion_tokens = (
            usage.completion_tokens if usage else None
        )
        total_tokens = (
            usage.total_tokens if usage else None
        )

        record_llm_call(
            model=model,
            operation="adhoc_it_support_demo",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            elapsed_ms=elapsed_ms,
            success=True
        )

        print("\n========== LLM RESPONSE ==========\n")
        print(response.choices[0].message.content)

        print("\n========== API TOKEN USAGE ==========\n")
        print(f"Model:              {model}")
        print(f"Prompt tokens:      {prompt_tokens}")
        print(f"Completion tokens:  {completion_tokens}")
        print(f"Total tokens:       {total_tokens}")
        print(f"Latency:            {elapsed_ms:.2f} ms")

        print("\n========== PROCESS METRICS ==========\n")
        print(snapshot())

        return response

    except Exception:
        elapsed_ms = (
            time.perf_counter() - started
        ) * 1000

        record_llm_call(
            model=model,
            operation="adhoc_it_support_demo",
            elapsed_ms=elapsed_ms,
            success=False
        )

        # Avoid printing API keys or request contents in error logs.
        print(
            "The LLM request failed. "
            "Check API credentials, model access, quota and connectivity.",
            file=sys.stderr
        )
        raise


if __name__ == "__main__":
    run_demo()
