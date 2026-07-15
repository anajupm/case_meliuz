import csv
import os
from datetime import datetime

import pandas as pd

import pipeline as p


FIELDS = [
    "nome_teste",
    "descricao",
    "resultado",
    "decisao",
    "parceiro",
    "periodo",
    "variantes",
    "metrica_primaria",
    "vencedor",
    "teste_valido",
    "significativo",
    "p_valor_ajustado",
    "data_analise",
]


def build_row(
    df: pd.DataFrame,
    decision: dict,
    test_name: str,
    description: str = "",
) -> dict:
    partner = str(df[p.COL_PARTNER].iloc[0])
    start = df[p.COL_DATE].min().date()
    end = df[p.COL_DATE].max().date()
    pairwise = decision.get("pairwise_test")

    if decision.get("valid_test", False):
        result = decision["recommendation"]
        p_adjusted = (
            "" if pairwise is None
            else f"{pairwise['p_value_adjusted']:.6g}"
        )
    else:
        result = "Experimento inválido: " + "; ".join(
            decision.get("recommendation", "").split("; ")
        )
        p_adjusted = ""

    return {
        "nome_teste": test_name,
        "descricao": description,
        "resultado": result,
        "decisao": decision["decision"],
        "parceiro": partner,
        "periodo": f"{start} a {end}",
        "variantes": int(df[p.COL_GROUP].nunique()),
        "metrica_primaria": decision["primary_metric"],
        "vencedor": decision.get("winner") or "",
        "teste_valido": (
            "sim" if decision.get("valid_test", False) else "nao"
        ),
        "significativo": (
            "sim" if decision.get("significant", False) else "nao"
        ),
        "p_valor_ajustado": p_adjusted,
        "data_analise": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def upsert_csv(row: dict, csv_path: str) -> str:
    """Insere ou substitui a mesma combinação nome/parceiro/período."""
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)

    existing: list[dict] = []

    if os.path.exists(csv_path):
        with open(
            csv_path,
            newline="",
            encoding="utf-8-sig",
        ) as file:
            reader = csv.DictReader(file)

            # Normaliza também as linhas antigas para o schema atual.
            existing = [
                {
                    field: item.get(field, "")
                    for field in FIELDS
                }
                for item in reader
            ]

    # Normaliza a nova linha para conter somente as colunas oficiais.
    normalized_row = {
        field: row.get(field, "")
        for field in FIELDS
    }

    key_fields = ("nome_teste", "parceiro", "periodo")

    row_key = tuple(
        str(normalized_row.get(field, ""))
        for field in key_fields
    )

    filtered = [
        item
        for item in existing
        if tuple(
            str(item.get(field, ""))
            for field in key_fields
        ) != row_key
    ]

    filtered.append(normalized_row)

    with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDS,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(filtered)

    return csv_path


# Alias para compatibilidade com a versão anterior.
append_to_csv = upsert_csv


def append_to_sheet(row: dict, sheet_id: str, creds_path: str) -> None:
    """Adiciona uma linha ao Google Sheets usando service account."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError as exc:
        raise RuntimeError(
            "Instale as dependências opcionais: "
            "pip install gspread google-auth"
        ) from exc

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_file(
        creds_path,
        scopes=scopes,
    )
    worksheet = gspread.authorize(credentials).open_by_key(sheet_id).sheet1

    if not worksheet.get_all_values():
        worksheet.append_row(FIELDS)

    worksheet.append_row([str(row.get(field, "")) for field in FIELDS])