from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from odf import style, table, text
from odf.opendocument import OpenDocumentSpreadsheet


class OdsReport:
    def __init__(self, events: list[dict], group_by: list[str], calc_col: str):
        self.events = events
        self.group_by = group_by
        self.calc_col = calc_col

        self.data_keys = []
        for ev in self.events:
            for k in ev.keys():
                if k not in self.data_keys and k not in self.group_by and k != self.calc_col:
                    self.data_keys.append(k)

        self.headers = self.group_by + self.data_keys + [self.calc_col]
        self.formula_headers = ["Diferença", "Média", "Desvio Padrão", "DP Relativo"]
        self.all_headers = self.headers + self.formula_headers

        self.col_indices = {name: i + 1 for i, name in enumerate(self.all_headers)}
        self.COL_CALC = self.col_indices[self.calc_col]
        self.COL_DIFF = self.col_indices["Diferença"]
        self.COL_AVG = self.col_indices["Média"]
        self.COL_STD = self.col_indices["Desvio Padrão"]
        self.COL_RSD = self.col_indices["DP Relativo"]

        # Ordenar os eventos com base nas chaves de agrupamento
        self.events.sort(key=lambda x: tuple(x.get(k, "") for k in self.group_by))

        self.doc = OpenDocumentSpreadsheet()
        self.sheet = table.Table(name="Relatório")
        self.doc.spreadsheet.addElement(self.sheet)
        self.styles = self.create_styles()

    def create_styles(self):
        styles = {}
        # Estilos omitidos para brevidade; mantenha a exata mesma lógica do seu código original
        # (Header, Normal, Centered, Numeric)
        for name, bg, align, is_bold in [
            ("Header", "#D9D9D9", "center", True),
            ("Normal", None, "left", False),
            ("Centered", None, "center", False),
            ("Numeric", None, "right", False),
        ]:
            s = style.Style(name=name, family="table-cell")
            if is_bold:
                s.addElement(style.TextProperties(fontweight="bold"))
            if align:
                s.addElement(style.ParagraphProperties(textalign=align))
            props = {"border": "0.05pt solid #888888", "padding": "0.03in"}
            if bg:
                props["backgroundcolor"] = bg
            s.addElement(style.TableCellProperties(**props))
            self.doc.automaticstyles.addElement(s)
            styles[name.lower()] = s
        return styles

    def cell(self, value=None, formula=None, style_name="normal", number_rows_spanned=None, covered=False):
        if covered:
            return table.CoveredTableCell()

        kwargs = {"stylename": self.styles[style_name]}
        if number_rows_spanned:
            kwargs["numberrowsspanned"] = str(number_rows_spanned)

        cell = table.TableCell(**kwargs)
        if formula:
            cell.setAttribute("formula", formula)
            cell.setAttribute("valuetype", "float")
            return cell

        if isinstance(value, (int, float)):
            cell.setAttribute("valuetype", "float")
            cell.setAttribute("value", str(value))
            cell.addElement(text.P(text=str(value)))
        else:
            cell.setAttribute("valuetype", "string")
            cell.addElement(text.P(text="" if value is None else str(value)))

        return cell

    @staticmethod
    def col_name(index: int):
        result = ""
        while index:
            index, remainder = divmod(index - 1, 26)
            result = chr(65 + remainder) + result
        return result

    def ref(self, col: int, row: int):
        return f"[.{self.col_name(col)}{row}]"

    def build(self):
        header_row = table.TableRow()
        for header in self.all_headers:
            header_row.addElement(self.cell(str(header).capitalize(), style_name="header"))
        self.sheet.addElement(header_row)

        grouped = defaultdict(list)
        for event in self.events:
            key = tuple(event.get(k, "") for k in self.group_by)
            grouped[key].append(event)

        current_row = 2

        for key, events in grouped.items():
            group_size = len(events)
            diff_refs = []
            group_start_row = current_row

            for index, event in enumerate(events):
                row = table.TableRow()

                # Colunas Agrupadas
                for col_name in self.group_by:
                    if index == 0:
                        row.addElement(self.cell(event.get(col_name, ""), style_name="centered", number_rows_spanned=group_size))
                    else:
                        row.addElement(self.cell(covered=True))

                # Colunas Individuais
                for col_name in self.data_keys:
                    row.addElement(self.cell(event.get(col_name, ""), style_name="centered"))

                # Coluna de Cálculo Principal (Ex: Timestamp)
                row.addElement(self.cell(event.get(self.calc_col, ""), style_name="numeric"))

                # Diferença Temporal
                if index == 0:
                    row.addElement(self.cell("", style_name="numeric"))
                else:
                    curr_ref = self.ref(self.COL_CALC, current_row)
                    prev_ref = self.ref(self.COL_CALC, current_row - 1)
                    diff_formula = f"of:={curr_ref}-{prev_ref}"
                    row.addElement(self.cell(formula=diff_formula, style_name="numeric"))
                    diff_refs.append(self.ref(self.COL_DIFF, current_row))

                # Estatísticas do Grupo
                if index == 0:
                    # Inicialmente vazio, será preenchido após o grupo
                    row.addElement(self.cell(formula='of:""', style_name="numeric", number_rows_spanned=group_size))
                    row.addElement(self.cell(formula='of:""', style_name="numeric", number_rows_spanned=group_size))
                    row.addElement(self.cell(formula='of:""', style_name="numeric", number_rows_spanned=group_size))
                else:
                    row.addElement(self.cell(covered=True))
                    row.addElement(self.cell(covered=True))
                    row.addElement(self.cell(covered=True))

                self.sheet.addElement(row)
                current_row += 1

            # Atualizar fórmulas do grupo
            if len(diff_refs) > 0:
                diff_range = ";".join(diff_refs)
                avg_formula = f"of:=AVERAGE({diff_range})"
                std_formula = f"of:=STDEV({diff_range})"
                rsd_formula = f"of:=IF(AVERAGE({diff_range})=0;0;STDEV({diff_range})/AVERAGE({diff_range}))"

                first_data_row = self.sheet.childNodes[group_start_row - 1]
                first_data_row.childNodes[self.COL_AVG - 1].setAttribute("formula", avg_formula)
                first_data_row.childNodes[self.COL_STD - 1].setAttribute("formula", std_formula)
                first_data_row.childNodes[self.COL_RSD - 1].setAttribute("formula", rsd_formula)

    def save(self, path: Path):
        self.build()
        self.doc.save(str(path))