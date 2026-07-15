import csv
import os

import pipeline as p

# Column order of the tracking sheet (first four are the required minimum).
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
    "significativo",
    "p_valor",
    "data_analise",
]


def build_row(df, decision: dict, test_name: str, description: str = "") -> dict:
    """Assemble one tracking row from the decision output."""
    from datetime import datetime
    partner = str(df[p.COL_PARTNER].iloc[0])
    start = df[p.COL_DATE].min().date()
    end = df[p.COL_DATE].max().date()
    pw = decision["pairwise_test"]

    # "resultado" = human summary of the outcome; "decisao" = the action taken.
    if decision["significant"]:
        resultado = (f"{decision['winner']} lidera em "
                     f"{decision['primary_metric']} com significancia "
                     f"(p={pw['p_value']:.4g})")
    else:
        resultado = (f"{decision['winner']} lidera no ponto estimado, sem "
                     f"significancia sobre {decision['runner_up']} "
                     f"(p={pw['p_value']:.4g})")

    return {
        "nome_teste": test_name,
        "descricao": description,
        "resultado": resultado,
        "decisao": decision["decision"],
        "parceiro": partner,
        "periodo": f"{start} a {end}",
        "variantes": df[p.COL_GROUP].nunique(),
        "metrica_primaria": decision["primary_metric"],
        "vencedor": decision["winner"],
        "significativo": "sim" if decision["significant"] else "nao",
        "p_valor": f"{pw['p_value']:.4g}",
        "data_analise": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def append_to_csv(row: dict, csv_path: str) -> str:
    """Append a row to the tracking CSV, writing the header if new."""
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    is_new = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(row)
    return csv_path


def append_to_sheet(row: dict, sheet_id: str, creds_path: str) -> None:
    """Append the same row to a Google Sheet (optional differential).

    Requires: pip install gspread google-auth, plus a service-account JSON
    whose email has edit access to the sheet. The creds file must NEVER be
    committed (see .gitignore).
    """
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    ws = gspread.authorize(creds).open_by_key(sheet_id).sheet1

    # Write the header once, if the sheet is empty.
    if not ws.get_all_values():
        ws.append_row(FIELDS)
    ws.append_row([str(row[f]) for f in FIELDS])