"""
Пример генерации отчёта на основе реальных данных из dict_report.html
"""

import json
from pathlib import Path
from src.generator import ReportGenerator

# Данные из реального отчёта (упрощённая версия)
sample_data = {
    "metadata": {
        "generated_at": "2026-03-26T16:08:32.716740",
        "collection_name": "hotels_dictionaries_23032026",
        "total_points": 3315,
        "points_analyzed": 3315,
        "elapsed_sec": 0.78,
        "embedding_model": "GigaChat EmbeddingsGigaR"
    },
    "total": 3315,
    "all_categories": ["city", "accommodation", "hotel_amenity", "room_amenity", "room_class"],
    "fill_summary": {
        "key": {"filled": 3315, "filled_pct": 100.0, "empty": 0, "null": 0},
        "category": {"filled": 3315, "filled_pct": 100.0, "empty": 0, "null": 0},
        "synonyms": {
            "missing": 0, "missing_pct": 0.0,
            "empty_list": 0, "empty_list_pct": 0.0,
            "one_synonym": 7, "one_pct": 0.21,
            "many_synonyms": 3308, "many_pct": 99.79,
            "length_stats": {"count": 3315, "min": 1, "max": 64, "avg": 5.79, "p50": 6}
        }
    },
    "category_stats": {
        "city": {
            "count": 3014,
            "no_synonyms": 0,
            "one_synonym": 6,
            "many_synonyms": 3008,
            "syn_length_stats": {"count": 3014, "min": 1, "max": 6, "avg": 5.66, "p50": 6.0}
        },
        "accommodation": {
            "count": 14,
            "no_synonyms": 0,
            "one_synonym": 0,
            "many_synonyms": 14,
            "syn_length_stats": {"count": 14, "min": 6, "max": 6, "avg": 6.0, "p50": 6.0}
        },
        "hotel_amenity": {
            "count": 44,
            "no_synonyms": 0,
            "one_synonym": 1,
            "many_synonyms": 43,
            "syn_length_stats": {"count": 44, "min": 1, "max": 6, "avg": 5.89, "p50": 6.0}
        },
        "room_amenity": {
            "count": 237,
            "no_synonyms": 0,
            "one_synonym": 0,
            "many_synonyms": 237,
            "syn_length_stats": {"count": 237, "min": 4, "max": 6, "avg": 5.97, "p50": 6}
        },
        "room_class": {
            "count": 6,
            "no_synonyms": 0,
            "one_synonym": 0,
            "many_synonyms": 6,
            "syn_length_stats": {"count": 6, "min": 49, "max": 64, "avg": 58.17, "p50": 61.0}
        }
    },
    "synonym_distribution": [
        {"count": 1, "entries": 7, "pct": 0.21},
        {"count": 4, "entries": 423, "pct": 12.76},
        {"count": 5, "entries": 143, "pct": 4.31},
        {"count": 6, "entries": 2736, "pct": 82.53},
        {"count": 49, "entries": 1, "pct": 0.03},
        {"count": 52, "entries": 1, "pct": 0.03},
        {"count": 60, "entries": 1, "pct": 0.03},
        {"count": 62, "entries": 2, "pct": 0.06},
        {"count": 64, "entries": 1, "pct": 0.03}
    ],
    "richest_entries": [
        {
            "id": "a287da01-e373-532a-9290-fa783109326c",
            "key": "luxury",
            "category": "room_class",
            "synonyms": ["люкс", "luxury", "deluxe", "делюкс", "де люкс", "de luxe", "suite", "сюит", "сьюит", "джуниор сюит"],
            "syn_count": 64
        },
        {
            "id": "85a3a14f-828a-57f7-bcac-f093759c7b39",
            "key": "economy",
            "category": "room_class",
            "synonyms": ["эконом", "бюджет", "базовый", "простой", "туристический", "туркласс", "койко-место", "койка"],
            "syn_count": 62
        },
        {
            "id": "95e079ce-882b-581a-b052-69c48779b748",
            "key": "vip",
            "category": "room_class",
            "synonyms": ["vip", "ви-ай-пи", "представительский", "президентский", "presidential", "exclusive"],
            "syn_count": 62
        },
        {
            "id": "b910e1a1-be76-537f-bea1-68270bdbed2b",
            "key": "comfort",
            "category": "room_class",
            "synonyms": ["комфорт", "comfort", "улучшенный", "повышенной комфортности", "superior"],
            "syn_count": 52
        },
        {
            "id": "1e6e098b-7023-5aa2-9a7a-b2f59d0e3155",
            "key": "business",
            "category": "room_class",
            "synonyms": ["бизнес", "business", "executive", "деловой", "корпоративный"],
            "syn_count": 49
        }
    ],
    "poorest_entries": [
        {
            "id": "00137b74-3207-5d0f-ac6b-a61a537c85ea",
            "key": "д. Рушиново",
            "category": "city",
            "synonyms": ["деревня Рушиново"],
            "syn_count": 1
        },
        {
            "id": "001fc0cc-8172-51c4-ad33-761076312268",
            "key": "д. Медведево",
            "category": "city",
            "synonyms": ["деревня Медведево"],
            "syn_count": 1
        }
    ]
}

if __name__ == '__main__':
    # Инициализация генератора
    generator = ReportGenerator()
    
    # Загрузка JS компонентов
    generator.load_components_js()
    
    # Генерация отчёта
    output_file = generator.generate_dictionary_report(
        sample_data,
        output_path='example_report.html'
    )
    
    print(f"✓ Отчёт успешно сгенерирован: {output_file}")
    print(f"📊 Всего записей: {sample_data['total']:,}")
    print(f"📁 Категорий: {len(sample_data['all_categories'])}")
    print(f"🔤 Модель: {sample_data['metadata']['embedding_model']}")
