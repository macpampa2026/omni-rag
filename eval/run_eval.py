#!/usr/bin/env python3
"""Harness de evaluación de calidad del RAG de omni-rag.

Ingesta un set de documentos, corre un conjunto de preguntas contra la API y mide:
  - retrieval recall : ¿el documento correcto aparece en las fuentes?
  - keyword recall   : ¿la respuesta contiene los datos esperados?
  - anti-alucinación : ante preguntas fuera de alcance, ¿responde el fallback en
                       vez de inventar?
  - (opcional) LLM-judge: nota 0-10 de corrección + fundamentación (--judge).

Sale con código 0 si pasa el umbral y 1 si no — así sirve como gate de CI.

Uso:
  python eval/run_eval.py --base-url http://localhost:8000 [--api-key XXX] [--judge]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import httpx

FALLBACK_MARK = "no cubre ese punto"


def _norm(s: str) -> str:
    """Normaliza para comparar palabras clave (quita separadores de miles y $)."""
    return re.sub(r"[.,$]", "", s.lower())


def ask(client: httpx.Client, base: str, headers: dict, question: str) -> dict:
    r = client.post(f"{base}/ask", json={"question": question}, headers=headers)
    r.raise_for_status()
    return r.json()


def judge(ollama_url: str, model: str, question: str, answer: str, gold: str):
    prompt = (
        f"PREGUNTA: {question}\nRESPUESTA DEL SISTEMA: {answer}\n"
        f"INFORMACION CORRECTA (fuente): {gold}\n\n"
        "Calificá la respuesta del 0 al 10 según si es correcta y está "
        "fundamentada en la fuente. Respondé SOLO el número."
    )
    payload = {
        "model": model, "stream": False,
        "messages": [{"role": "user", "content": prompt}],
        "options": {"temperature": 0.0, "num_predict": 8},
    }
    r = httpx.post(f"{ollama_url}/api/chat", json=payload, timeout=120)
    r.raise_for_status()
    m = re.search(r"\d+(?:\.\d+)?", r.json().get("message", {}).get("content", ""))
    return float(m.group()) if m else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=os.getenv("OMNIRAG_BASE_URL", "http://localhost:8000"))
    ap.add_argument("--api-key", default=os.getenv("OMNIRAG_API_KEY", ""))
    ap.add_argument("--dataset", default=str(Path(__file__).parent / "dataset.json"))
    ap.add_argument("--judge", action="store_true", help="usar LLM-judge (Ollama)")
    args = ap.parse_args()

    base = args.base_url.rstrip("/")
    headers = {"X-API-Key": args.api_key} if args.api_key else {}
    data = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    gold_text = {d["doc_id"]: d["text"] for d in data["documents"]}

    ollama_url = os.getenv("OMNIRAG_OLLAMA_URL", "http://localhost:11434").rstrip("/")
    gen_model = os.getenv("OMNIRAG_GEN_MODEL", "qwen2.5:7b")

    retr_hits = retr_total = hall_ok = hall_total = 0
    kw_scores: list[float] = []
    judge_scores: list[float] = []

    with httpx.Client(timeout=180) as client:
        # Preflight: no tiene sentido evaluar si el sistema no está listo.
        try:
            ready = client.get(f"{base}/health/ready", headers=headers).json()
        except httpx.HTTPError as exc:
            print(f"ABORTA: no puedo conectar con la API en {base} ({exc}).")
            sys.exit(2)
        if ready.get("ollama") != "up":
            print(f"ABORTA: el sistema no está listo (ollama={ready.get('ollama')}). "
                  "¿Está corriendo Ollama?")
            sys.exit(2)

        print("Ingestando documentos de evaluación...")
        for d in data["documents"]:
            client.post(f"{base}/documents", json=d, headers=headers).raise_for_status()

        print("\n== Casos ==")
        for case in data["cases"]:
            res = ask(client, base, headers, case["question"])
            answer = res["answer"]
            srcs = [s["doc_id"] for s in res["sources"]]

            if case["in_scope"]:
                retr_total += 1
                hit = case["gold_doc_id"] in srcs
                retr_hits += int(hit)

                kws = case.get("expects_keywords", [])
                na = _norm(answer)
                kw = (sum(1 for k in kws if _norm(k) in na) / len(kws)) if kws else 1.0
                kw_scores.append(kw)

                mark = "OK" if hit and kw >= 0.5 else "!!"
                print(f"[{mark}] {case['question']}  (retrieval={'hit' if hit else 'miss'}, kw={kw:.0%})")

                if args.judge:
                    js = judge(ollama_url, gen_model, case["question"], answer,
                               gold_text.get(case["gold_doc_id"], ""))
                    if js is not None:
                        judge_scores.append(js)
            else:
                hall_total += 1
                ok = FALLBACK_MARK in answer.lower()
                hall_ok += int(ok)
                estado = "no inventó" if ok else "INVENTÓ"
                print(f"[{'OK' if ok else '!!'}] (fuera de alcance) {case['question']}  -> {estado}")

    rr = retr_hits / retr_total if retr_total else 0.0
    kr = sum(kw_scores) / len(kw_scores) if kw_scores else 0.0
    hr = hall_ok / hall_total if hall_total else 1.0

    print("\n== Resumen ==")
    print(f"Retrieval recall : {rr:.0%}  ({retr_hits}/{retr_total})")
    print(f"Keyword recall   : {kr:.0%}")
    print(f"Anti-alucinación : {hr:.0%}  ({hall_ok}/{hall_total})")
    if judge_scores:
        print(f"LLM-judge (0-10) : {sum(judge_scores) / len(judge_scores):.1f}")

    passed = rr >= 0.8 and kr >= 0.7 and hr == 1.0
    print(f"\nRESULTADO: {'PASS' if passed else 'FAIL'}")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
