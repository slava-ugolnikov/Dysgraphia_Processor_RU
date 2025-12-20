from typing import List, Tuple
import pandas as pd
import openpyxl


class ExcelExporter:
    def export(self, data: List[Tuple[str, str, str]], filename: str):
        df = pd.DataFrame(
            data,
            columns=[
                "Задуманное слово (лемма)",
                "Написанное слово",
                "Тип ошибки"
            ]
        )
        df.to_excel(filename, index=False)
