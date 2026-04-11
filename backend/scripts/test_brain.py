"""
Test script — Valida que Ollama se usa correctamente (100% antes de Gemini).

Uso: cd backend && uv run python scripts/test_brain.py

Resultado: reporte de qué nivel se usó para cada tarea
"""

import asyncio
import json
import sys
from datetime import datetime

sys.path.insert(0, ".")

from app.brain.router import brain_router


async def test_brain():
    """Lance 10 requests de diferentes tipos y verifique uso de Ollama."""
    print("=" * 70)
    print("SYSMHO HUNTER — BRAIN DIAGNOSTICS TEST")
    print("=" * 70)
    print(f"\nTimestamp: {datetime.now().isoformat()}\n")

    test_cases = [
        {
            "task_type": "classify_severity",
            "input_data": {
                "description": "SQL injection in login form"
            },
            "expected_level": 1,
        },
        {
            "task_type": "detect_patterns",
            "input_data": {
                "description": "XSS vulnerability found in user input field"
            },
            "expected_level": 2,
        },
        {
            "task_type": "analyze_response",
            "input_data": {
                "url": "http://example.com/api",
                "status_code": 200,
                "headers": {"Content-Type": "application/json"},
                "body": '{"user": "admin", "password": "secret"}',
            },
            "expected_level": 2,
        },
        {
            "task_type": "reason_next_steps",
            "input_data": {
                "target_url": "http://example.com",
                "recon_data": {"subdomains": ["api.example.com"]},
                "findings": [{"type": "XSS", "severity": "high"}],
            },
            "expected_level": 2,
        },
    ]

    stats = {
        "total": len(test_cases),
        "level_1_count": 0,
        "level_2_count": 0,
        "level_3_count": 0,
        "errors": 0,
        "results": [],
    }

    for i, test in enumerate(test_cases, 1):
        task_type = test["task_type"]
        input_data = test["input_data"]

        try:
            print(f"[{i}/{len(test_cases)}] Task: {task_type}")

            result = await brain_router.route(task_type, input_data)

            brain_level = result.get("brain_level", 0)
            model = result.get("model_used", "unknown")
            latency = result.get("total_latency_ms", 0)
            confidence = result.get("confidence", 0)

            # Contar por nivel
            if brain_level == 1:
                stats["level_1_count"] += 1
            elif brain_level == 2:
                stats["level_2_count"] += 1
            elif brain_level == 3:
                stats["level_3_count"] += 1
            else:
                stats["errors"] += 1

            # Verificar si es correcto
            is_correct = brain_level >= test.get("expected_level", 1)
            status = "✅ OK" if is_correct else "⚠️  FALLBACK"

            print(
                f"  → {status} | Level: {brain_level} | "
                f"Model: {model} | "
                f"Latency: {latency}ms | "
                f"Confidence: {confidence:.3f}\n"
            )

            stats["results"].append({
                "task_type": task_type,
                "brain_level": brain_level,
                "model_used": model,
                "latency_ms": latency,
                "confidence": confidence,
            })

        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}\n")
            stats["errors"] += 1

    # Reporte final
    print("=" * 70)
    print("FINAL REPORT")
    print("=" * 70)

    ollama_usage_pct = (
        100 * stats["level_2_count"] / stats["total"]
        if stats["total"] > 0
        else 0
    )
    gemini_usage_pct = (
        100 * stats["level_3_count"] / stats["total"]
        if stats["total"] > 0
        else 0
    )

    print(f"\n📊 STATISTICS:")
    print(f"  Total tasks: {stats['total']}")
    print(f"  Level 1 (ML):     {stats['level_1_count']:2d} "
          f"({100*stats['level_1_count']/stats['total']:.0f}%)")
    print(f"  Level 2 (Ollama): {stats['level_2_count']:2d} "
          f"({ollama_usage_pct:.0f}%) ← PRIMARY")
    print(f"  Level 3 (Cloud):  {stats['level_3_count']:2d} "
          f"({gemini_usage_pct:.0f}%)")
    print(f"  Errors:           {stats['errors']:2d}")

    print(f"\n🎯 VERDICT:")
    if ollama_usage_pct >= 90:
        print(f"  ✅ PASS: Ollama used {ollama_usage_pct:.0f}% of the time")
        print(f"     SysMho Hunter is using LOCAL AI as PRIMARY ✅")
    elif ollama_usage_pct >= 70:
        print(f"  ⚠️  WARNING: Ollama used {ollama_usage_pct:.0f}% of the time")
        print(f"     Expected >= 90%. Check Ollama availability.")
    else:
        print(f"  ❌ FAIL: Ollama used {ollama_usage_pct:.0f}% of the time")
        print(f"     Fallback to Cloud is too high. Investigate.")

    print("\n" + "=" * 70)

    # Salida JSON para análisis
    print("\nJSON Output:")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    asyncio.run(test_brain())
