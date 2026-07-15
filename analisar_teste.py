import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import decision as dec
import pipeline as p
import report as rp
import tracking as tk


def _json_default(value):
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"Objeto não serializável: {type(value).__name__}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Analisa um teste A/B de cashback, gera relatório e registra "
            "a decisão."
        )
    )
    parser.add_argument("csv", help="Caminho do CSV do teste")
    parser.add_argument("--nome", default=None, help="Nome do teste")
    parser.add_argument("--desc", default="", help="Descrição do teste")
    parser.add_argument(
        "--reports-dir",
        default="reports",
        help="Pasta de saída dos relatórios",
    )
    parser.add_argument(
        "--tracking",
        default="tracking/acompanhamento.csv",
        help="CSV consolidado de acompanhamento",
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="Arquivo opcional para salvar a saída estruturada em JSON",
    )
    parser.add_argument(
        "--sheet-id",
        default=None,
        help="ID de uma planilha Google Sheets opcional",
    )
    parser.add_argument(
        "--creds",
        default=None,
        help="JSON da service account para Google Sheets",
    )
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        parser.error(f"Arquivo não encontrado: {args.csv}")
    if bool(args.sheet_id) != bool(args.creds):
        parser.error("--sheet-id e --creds devem ser informados juntos.")

    try:
        df, quality = p.load_and_clean(args.csv)
        metrics = p.metrics_by_group(df)
        decision = dec.decide(df, metrics, quality)

        partner = str(df[p.COL_PARTNER].iloc[0])
        test_name = args.nome or f"Teste de cashback - {partner}"

        markdown = rp.build_report(
            df,
            metrics,
            decision,
            quality,
            test_name=test_name,
        )
        report_path = rp.save_report(
            markdown,
            args.reports_dir,
            partner,
        )

        tracking_row = tk.build_row(
            df,
            decision,
            test_name,
            args.desc,
        )
        tracking_path = tk.upsert_csv(tracking_row, args.tracking)

        sheet_message = ""
        if args.sheet_id and args.creds:
            tk.append_to_sheet(tracking_row, args.sheet_id, args.creds)
            sheet_message = " | Google Sheets atualizado"

        payload = {
            "test_name": test_name,
            "partner": partner,
            "quality": quality,
            "metrics": metrics.round(6).to_dict(orient="index"),
            "decision": decision,
            "report_path": report_path,
            "tracking_path": tracking_path,
        }

        if args.json_output:
            output_path = Path(args.json_output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(
                    payload,
                    indent=2,
                    ensure_ascii=False,
                    default=_json_default,
                ),
                encoding="utf-8",
            )

        print("=" * 72)
        print(f"Teste: {test_name}")
        print(f"Validade: {'válido' if decision['valid_test'] else 'inválido'}")
        print(f"Decisão: {decision['decision']}")
        print(f"Relatório: {report_path}")
        print(f"Tracking: {tracking_path}{sheet_message}")
        if args.json_output:
            print(f"JSON: {args.json_output}")
        print("=" * 72)

    except (ValueError, RuntimeError, OSError) as exc:
        print(f"Erro durante a análise: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()