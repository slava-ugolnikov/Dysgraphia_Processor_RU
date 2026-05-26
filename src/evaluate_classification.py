import pandas as pd
from sklearn.metrics import classification_report, precision_recall_fscore_support, accuracy_score
import warnings

warnings.filterwarnings("ignore")


def evaluate_auto_vs_expert(excel_path: str = "auto_classified.xlsx"):
    """
    Сравнивает автоматическую классификацию («Авто_Тип_ошибки»)
    с экспертной разметкой («Пояснение ошибки»).
    """
    print("Загружаем файл для оценки...")
    dfs = pd.read_excel(excel_path, sheet_name=None)

    # Собираем все листы в один DataFrame
    all_data = []
    for sheet, df in dfs.items():
        df = df.copy()
        df['sheet'] = sheet
        all_data.append(df)

    df_all = pd.concat(all_data, ignore_index=True)

    # Фильтруем только строки, где есть обе метки
    mask = (
            df_all['Авто_Тип_ошибки'].notna() &
            df_all['Авто_Тип_ошибки'].astype(str).str.strip().ne("") &
            df_all['Пояснение ошибки'].notna() &
            df_all['Пояснение ошибки'].astype(str).str.strip().ne("")
    )

    true_labels = df_all.loc[mask, 'Пояснение ошибки'].astype(str).str.strip()
    pred_labels = df_all.loc[mask, 'Авто_Тип_ошибки'].astype(str).str.strip()

    print(f"Всего пар для оценки: {len(true_labels)}")

    if len(true_labels) == 0:
        print("Нет данных для сравнения!")
        return

    # Метрики
    print("Отчет (точное совпадение строк)")
    print(classification_report(true_labels, pred_labels, zero_division=0, digits=3))

    accuracy = accuracy_score(true_labels, pred_labels)
    print(f"\nОбщая точность (accuracy): {accuracy:.3f}")

    df_errors = df_all[mask].copy()
    df_errors['Совпадает'] = true_labels.reset_index(drop=True) == pred_labels.reset_index(drop=True)
    df_errors = df_errors[~df_errors['Совпадает']]
    print(f"\nКоличество расхождений: {len(df_errors)}")
    if len(df_errors) > 0:
        print(df_errors[['sheet', 'Задуманное слово', 'Написанное слово',
                         'Пояснение ошибки', 'Авто_Тип_ошибки']].head(10))


if __name__ == "__main__":
    evaluate_auto_vs_expert()