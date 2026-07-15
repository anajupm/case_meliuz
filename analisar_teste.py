"""
analisar_teste.py — Step 5: the orchestrator (entry point).

Runs the whole pipeline for one A/B test with a single command:
    load_and_clean -> metrics_by_group -> decide -> report -> tracking

Usage:
    python analisar_teste.py <caminho_do_csv> [--nome NOME] [--desc DESCRICAO]

Optional Google Sheets (differential):
    python analisar_teste.py <csv> --sheet-id ID --creds caminho/cred.json
"""

import argparse
import os
import sys

# This file lives at the project root; the modules live in src/.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import pipeline as p
import decision as dec
import report as rp
import tracking as tk


def main():
    parser = argparse.ArgumentParser(
        description="Analisa um teste A/B de cashback e registra o resultado.")
    parser.add_argument("csv", help="Caminho do CSV do teste")
    parser.add_argument("--nome", default=None, help="Nome do teste")
    parser.add_argument("--desc", default="", help="Descrição do teste")
    parser.add_argument("--reports-dir", default="reports",
                        help="Pasta de saída dos relatórios")
    parser.add_argument("--tracking", default="tracking/acompanhamento.csv",
                        help="Caminho da planilha CSV de acompanhamento")
    parser.add_argument("--sheet-id", default=None,
                        help="ID do Google Sheet (diferencial, opcional)")
    parser.add_argument("--creds", default=None,
                        help="JSON da service account (opcional)")
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print(f"Arquivo não encontrado: {args.csv}")
        sys.exit(1)

    # 1) Limpar + métricas
    df, quality = p.load_and_clean(args.csv)
    metrics = p.metrics_by_group(df)

    # 2) Decidir
    decision = dec.decide(df, metrics)

    # 3) Relatório
    partner = df[p.COL_PARTNER].iloc[0]
    test_name = args.nome or f"Teste de cashback - {partner}"
    md = rp.build_report(df, metrics, decision, quality, test_name=test_name)
    report_path = rp.save_report(md, args.reports_dir, partner)

    # 4) Registro na planilha
    row = tk.build_row(df, decision, test_name, args.desc)
    csv_path = tk.append_to_csv(row, args.tracking)
    if args.sheet_id and args.creds:
        tk.append_to_sheet(row, args.sheet_id, args.creds)
        sheet_msg = " | Google Sheet atualizado"
    else:
        sheet_msg = ""

    # 5) Resumo no terminal
    print("=" * 60)
    print(f"Teste: {test_name}")
    print(f"Decisão: {decision['decision']}")
    print(f"Relatório: {report_path}")
    print(f"Planilha: {csv_path}{sheet_msg}")
    print("=" * 60)


if __name__ == "__main__":
    main()