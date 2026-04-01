# Report Framework

Фреймворк для генерации HTML отчётов в стиле sample reports из репозитория.

## Структура

```
report-framework/
├── src/
│   ├── styles/
│   │   └── main.scss          # SCSS стили (CSS переменные, компоненты)
│   ├── components/
│   │   └── index.js           # JS компоненты для рендеринга
│   └── generator.py           # Python генератор отчётов
├── templates/
│   ├── base.html              # Базовый шаблон
│   └── dictionary_report.html # Шаблон отчёта по словарю
├── data/                      # Данные для отчётов (опционально)
├── dist/                      # Скомпилированные файлы
├── package.json
├── webpack.config.js
└── README.md
```

## Установка

```bash
cd report-framework

# Установка Node.js зависимостей
npm install

# Установка Python зависимостей
pip install jinja2

# Сборка CSS и JS
npm run build
```

## Использование

### 1. Генерация отчёта через Python

```python
from src.generator import ReportGenerator

# Инициализация
generator = ReportGenerator()
generator.load_components_js()

# Данные отчёта (структура как в sample files)
data = {
    'metadata': {
        'generated_at': '2026-03-26T16:08:32',
        'collection_name': 'hotels_dictionaries',
        'total_points': 3315,
        'embedding_model': 'GigaChat EmbeddingsGigaR'
    },
    'total': 3315,
    'all_categories': ['city', 'hotel_amenity', 'room_amenity'],
    'fill_summary': {...},
    'category_stats': {...},
    'synonym_distribution': [...],
    'richest_entries': [...],
    'poorest_entries': [...]
}

# Генерация
output_file = generator.generate_dictionary_report(
    data,
    output_path='reports/my_report.html'
)
print(f"Report generated: {output_file}")
```

### 2. Компоненты для кастомных отчётов

```javascript
import {
  renderKPI,
  renderKPIGrid,
  renderBarRow,
  renderFillSection,
  renderCategoryStats,
  renderSynonymDistribution,
  renderEntryCard,
  renderSearchResults,
  renderTable,
  initChart,
  initNavigation,
  animateBars
} from './src/components/index.js';

// Пример: рендеринг KPI
const kpiHTML = renderKPI('Всего записей', '3,315', '+12% за неделю', 'g');

// Пример: рендеринг прогресс-бара
const barHTML = renderBarRow('Заполнено', 95.5, '3,167 / 3,315', '#21A038');

// Пример: таблица
const tableHTML = renderTable(
  [
    {key: 'name', header: 'Название'},
    {key: 'value', header: 'Значение'}
  ],
  [
    {name: 'Элемент 1', value: 100},
    {name: 'Элемент 2', value: 200}
  ]
);
```

### 3. Создание своего шаблона

Создайте файл в `templates/my_template.html`:

```html
<!DOCTYPE html>
<html lang='ru'>
<head>
  <meta charset='UTF-8'>
  <title>{{ report_title }}</title>
  <style>{{ styles_css|safe }}</style>
</head>
<body>
  <div class='hdr'>
    <h1>{{ header_title }}</h1>
  </div>
  
  <div class='main'>
    {{ content_html|safe }}
  </div>
  
  <script>
    const R = {{ report_data|tojson }};
    {{ components_js|safe }}
  </script>
</body>
</html>
```

Генерация:

```python
generator.generate_custom_report(
    template_name='my_template.html',
    context={
        'report_title': 'Мой отчёт',
        'header_title': 'Заголовок',
        'content_html': '<div>Контент</div>',
        'report_data': {'key': 'value'}
    },
    output_path='reports/custom.html'
)
```

## Компоненты

### KPI Cards
- `renderKPI(label, value, subtext, colorClass)` - одиночная KPI карточка
- `renderKPIGrid(kpis)` - сетка KPI (4 колонки)

### Progress Bars
- `renderBarRow(label, pct, value, color)` - строка с прогресс-баром

### Sections
- `renderFillSection(fillSummary)` - секция заполненности
- `renderCategoryStats(categoryStats)` - статистика по категориям
- `renderSynonymDistribution(dist)` - распределение синонимов
- `renderEntryCard(entry, accentColor)` - карточка записи
- `renderSearchResults(vectorSearchData)` - результаты поиска

### Utilities
- `fmtN(n)` - форматирование чисел
- `fmtP(pct)` - форматирование процентов
- `fmtMs(ms)` - форматирование миллисекунд
- `initChart(canvasId, config)` - инициализация Chart.js
- `initNavigation()` - навигация по секциям
- `animateBars()` - анимация прогресс-баров

## Темизация

CSS переменные в `src/styles/main.scss`:

```scss
:root {
  --g: #21A038;    // Основной зелёный
  --gd: #0d4d1a;   // Тёмный зелёный
  --y: #f5a623;    // Жёлтый
  --r: #d0021b;    // Красный
  --b: #0077cc;    // Синий
  // ... другие переменные
}
```

## Сборка

```bash
# Development mode (watch)
npm run dev

# Production build
npm run build

# Clean dist
npm run clean
```

## Примеры

Примеры готовых отчётов в `/workspace`:
- `dict_report.html` - отчёт по словарю
- `hotels_report_5.html` - отчёт по отелям
- `test_report (2).html` - тестовый отчёт
