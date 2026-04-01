"""
Report Generator - Python module for generating HTML reports
Uses Jinja2 templates and framework components
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape


class ReportGenerator:
    """Генератор отчётов на основе шаблонов и данных"""
    
    def __init__(self, template_dir: str = None, dist_dir: str = None):
        """
        Инициализация генератора
        
        Args:
            template_dir: Путь к директории с шаблонами
            dist_dir: Путь к директории для выходных файлов
        """
        self.base_dir = Path(__file__).parent
        self.template_dir = Path(template_dir) if template_dir else self.base_dir / 'templates'
        self.dist_dir = Path(dist_dir) if dist_dir else self.base_dir / 'dist'
        self.components_js = ""
        
        # Загрузка CSS
        self.styles_css = self._load_css()
        
        # Настройка Jinja2
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Фильтры
        self.env.filters['tojson'] = lambda x: json.dumps(x, ensure_ascii=False)
    
    def _load_css(self) -> str:
        """Загрузка скомпилированного CSS"""
        # Пробуем несколько путей для CSS
        possible_paths = [
            self.base_dir.parent / 'dist' / 'styles.css',  # ../dist/styles.css
            self.dist_dir / 'styles.css',  # ./dist/styles.css
            Path(__file__).parent.parent / 'dist' / 'styles.css'  # ../../dist/styles.css
        ]
        
        for css_path in possible_paths:
            if css_path.exists():
                return css_path.read_text(encoding='utf-8')
        return ""
    
    def load_components_js(self) -> str:
        """Загрузка скомпилированного JS компонентов"""
        js_path = self.dist_dir / 'components.js'
        if js_path.exists():
            self.components_js = js_path.read_text(encoding='utf-8')
        return self.components_js
    
    def generate_dictionary_report(
        self,
        data: Dict[str, Any],
        output_path: str = None,
        collection_name: str = None,
        embedding_model: str = None
    ) -> str:
        """
        Генерация отчёта по словарю
        
        Args:
            data: Данные отчёта (структура как в sample files)
            output_path: Путь для сохранения HTML
            collection_name: Название коллекции
            embedding_model: Модель эмбеддингов
            
        Returns:
            Путь к сохранённому файлу
        """
        # Подготовка данных
        metadata = data.get('metadata', {})
        fill_summary = data.get('fill_summary', {})
        category_stats = data.get('category_stats', {})
        synonym_dist = data.get('synonym_distribution', [])
        richest = data.get('richest_entries', [])[:5]
        poorest = data.get('poorest_entries', [])[:5]
        vector_search = data.get('vector_search', {})
        
        # Формирование заголовка
        generated_at = metadata.get('generated_at', datetime.now().isoformat())
        collection = collection_name or metadata.get('collection_name', 'Коллекция')
        model = embedding_model or metadata.get('embedding_model', 'Unknown')
        
        header_numbers = [
            {'id': 'kpi-total', 'label_id': 'kpi-total-lbl', 'value': str(data.get('total', 0)), 'label': 'Всего'},
        ]
        
        # Добавление категорий в header
        all_categories = data.get('all_categories', [])
        for i, cat in enumerate(all_categories[:4]):
            cat_count = category_stats.get(cat, {}).get('count', 0)
            header_numbers.append({
                'id': f'kpi-c{i}',
                'label_id': f'kpi-c{i}-lbl',
                'value': str(cat_count),
                'label': cat
            })
        
        # Навигация
        navigation = [
            {'section': 'sec-fill', 'title': 'Заполненность'},
            {'section': 'sec-cats', 'title': 'По категориям'},
            {'section': 'sec-syndist', 'title': 'Синонимы'},
            {'section': 'sec-rich', 'title': 'Богатые / бедные'},
        ]
        
        if vector_search:
            navigation.append({'section': 'sec-search', 'title': 'Поиск'})
        
        # Рендеринг секций через компоненты
        # Импортируем функции напрямую из JS-файла через строковую интерполяцию
        # Для Python версии используем локальные функции
        
        def py_renderFillSection(fill_summary):
            """Python версия рендеринга заполненности"""
            if not fill_summary:
                return '<div class="card"><div class="card-b">Нет данных</div></div>'
            
            key = fill_summary.get('key', {})
            synonyms = fill_summary.get('synonyms', {})
            stats = synonyms.get('length_stats', {})
            
            html = '<div class="g3">'
            
            if key:
                filled_pct = key.get('filled_pct', 0)
                empty = key.get('empty', 0)
                filled = key.get('filled', 0)
                html += f'''
                    <div class="card">
                        <div class="card-h">Ключевое поле</div>
                        <div class="card-b">
                            <div class="br">
                                <div class="br-l">Заполнено</div>
                                <div class="br-t"><div class="br-f" style="width:{filled_pct}%;background:#21A038"></div></div>
                                <div class="br-v">{filled:,}</div>
                            </div>
                        </div>
                    </div>
                '''
            
            if synonyms:
                many_pct = synonyms.get('many_pct', 0)
                one_pct = synonyms.get('one_pct', 0)
                missing_pct = synonyms.get('missing_pct', 0)
                html += f'''
                    <div class="card">
                        <div class="card-h">Синонимы</div>
                        <div class="card-b">
                            <div class="br">
                                <div class="br-l">Много синонимов</div>
                                <div class="br-t"><div class="br-f" style="width:{many_pct}%;background:#21A038"></div></div>
                                <div class="br-v">{many_pct:.1f}%</div>
                            </div>
                            <div class="br">
                                <div class="br-l">1 синоним</div>
                                <div class="br-t"><div class="br-f" style="width:{one_pct}%;background:#f5a623"></div></div>
                                <div class="br-v">{one_pct:.1f}%</div>
                            </div>
                        </div>
                    </div>
                '''
            
            if stats:
                html += f'''
                    <div class="card">
                        <div class="card-h">Статистика</div>
                        <div class="card-b">
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px">
                                <div><strong>Min:</strong> {stats.get('min', 0)}</div>
                                <div><strong>Max:</strong> {stats.get('max', 0)}</div>
                                <div><strong>Avg:</strong> {stats.get('avg', 0):.2f}</div>
                                <div><strong>P50:</strong> {stats.get('p50', 0)}</div>
                            </div>
                        </div>
                    </div>
                '''
            
            html += '</div>'
            return html
        
        def py_renderCategoryStats(category_stats):
            """Python версия рендеринга статистики по категориям"""
            if not category_stats:
                return '<div>Нет данных</div>'
            
            html = ''
            for cat_name, data in category_stats.items():
                count = data.get('count', 0)
                avg_syn = data.get('syn_length_stats', {}).get('avg', 0)
                no_syn = data.get('no_synonyms', 0)
                
                html += f'''
                    <div class="card">
                        <div class="card-h">{cat_name}</div>
                        <div class="card-b">
                            <div class="kpi g" style="margin-bottom:12px">
                                <div class="kpi-l">Записей</div>
                                <div class="kpi-v">{count:,}</div>
                            </div>
                            <div style="font-size:12px;color:var(--mu)">
                                <div>Среднее кол-во синонимов: <strong>{avg_syn:.2f}</strong></div>
                                <div>Без синонимов: <strong>{no_syn}</strong></div>
                            </div>
                        </div>
                    </div>
                '''
            return html
        
        def py_renderSynonymDistribution(dist):
            """Python версия рендеринга распределения синонимов"""
            if not dist:
                return '<div>Нет данных</div>'
            
            max_val = max((d.get('entries', 0) for d in dist), default=1)
            html = ''
            
            for d in dist:
                count = d.get('count', 0)
                entries = d.get('entries', 0)
                pct = d.get('pct', 0)
                
                if count == 0:
                    label = '0 синонимов'
                    color = '#d0021b'
                elif count == 1:
                    label = '1 синоним'
                    color = '#f5a623'
                else:
                    label = f'{count} синонимов'
                    color = '#21A038'
                
                bar_pct = (entries / max_val * 100) if max_val > 0 else 0
                
                html += f'''
                    <div class="br">
                        <div class="br-l">{label}</div>
                        <div class="br-t"><div class="br-f" style="width:{bar_pct}%;background:{color}"></div></div>
                        <div class="br-v">{entries:,} ({pct:.2f}%)</div>
                    </div>
                '''
            return html
        
        def py_renderEntryCard(entry, accent_color='#21A038'):
            """Python версия рендеринга карточки записи"""
            synonyms = entry.get('synonyms', [])
            display_syns = synonyms[:8]
            syn_count = entry.get('syn_count', len(synonyms))
            key = entry.get('key', '')
            category = entry.get('category', '')
            
            syns_html = ''.join(
                f'<span class="syn-tag" style="background:var(--wh);border:1px solid var(--br);border-radius:14px;padding:2px 9px;font-size:12px">{s}</span>'
                for s in display_syns
            )
            more_html = f'<span style="font-size:11px;color:var(--lt)">+ещё {syn_count - 8}</span>' if syn_count > 8 else ''
            
            return f'''
                <div class="sq" style="margin-bottom:10px">
                    <div class="sq-body">
                        <div class="sq-r" style="border-left:3px solid {accent_color}">
                            <div style="font-weight:600;font-size:13px;margin-bottom:4px">{key}</div>
                            <div style="font-size:11px;color:var(--mu);margin-bottom:6px">
                                <span class="bdg bdg-ci">{category}</span>
                                <span style="margin-left:8px">{syn_count} синонимов</span>
                            </div>
                            <div style="display:flex;flex-wrap:wrap;gap:4px">
                                {syns_html}
                                {more_html}
                            </div>
                        </div>
                    </div>
                </div>
            '''
        
        def py_renderSearchResults(vector_search_data):
            """Python версия рендеринга результатов поиска"""
            if not vector_search_data:
                return ''
            
            agg = vector_search_data.get('aggregate_metrics', {})
            queries = vector_search_data.get('queries', [])
            lat = agg.get('latency', {})
            sc = agg.get('top1_score', {})
            
            html = f'''
                <div class="card" style="margin-bottom:16px">
                    <div class="card-h">Агрегированные метрики</div>
                    <div class="card-b">
                        <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--br);font-size:12px">
                            <span>Avg latency</span>
                            <span style="font-weight:600">{lat.get('avg_ms', 0):.2f} ms</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--br);font-size:12px">
                            <span>P50</span>
                            <span style="font-weight:600">{lat.get('p50_ms', 0):.2f} ms</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--br);font-size:12px">
                            <span>P90</span>
                            <span style="font-weight:600">{lat.get('p90_ms', 0):.2f} ms</span>
                        </div>
            '''
            
            if sc.get('avg') is not None:
                html += f'''
                    <div style="display:flex;justify-content:space-between;padding:5px 0;font-size:12px">
                        <span>Avg top1 score</span>
                        <span style="font-weight:600">{sc.get('avg', 0):.4f}</span>
                    </div>
                '''
            
            html += '</div></div>'
            
            # Query cards
            for q in queries:
                ms = q.get('metrics', {})
                results = q.get('top_results', [])
                
                html += f'''
                    <div class="sq" style="margin-bottom:10px">
                        <div class="sq-h">
                            <div class="sq-n">{q.get('query_num', 0)}</div>
                            <div class="sq-t">{q.get('query_text', '')}</div>
                            <div class="sq-ms">
                                <div class="sq-m">embed <strong>{ms.get('embed_ms', 0):.2f} ms</strong></div>
                                <div class="sq-m">search <strong>{ms.get('search_ms', 0):.2f} ms</strong></div>
                            </div>
                        </div>
                        <div class="sq-body">
                '''
                
                for j, r in enumerate(results):
                    html += f'''
                        <div class="sq-r">
                            <div class="sq-r-top">
                                <div class="sq-rk">{j + 1}.</div>
                                <div class="sq-nm">{r.get('key', '')}</div>
                                <span class="bdg bdg-ci">{r.get('category', '')}</span>
                            </div>
                            <div style="font-family:monospace;font-size:10px;color:var(--lt);margin-top:3px">{r.get('id', '')}</div>
                        </div>
                    '''
                
                html += '</div></div>'
            
            return html
        
        fill_section_html = py_renderFillSection(fill_summary)
        category_stats_html = py_renderCategoryStats(category_stats)
        synonym_dist_html = py_renderSynonymDistribution(synonym_dist)
        richest_html = ''.join(py_renderEntryCard(e, '#21A038') for e in richest)
        poorest_html = ''.join(py_renderEntryCard(e, '#d0021b') for e in poorest)
        search_results_html = py_renderSearchResults(vector_search) if vector_search else ''
        
        # Контекст шаблона
        context = {
            'report_title': f'Отчёт — {collection}',
            'header_badge': 'Коллекция активна',
            'header_title': 'Словарная коллекция — аналитика',
            'header_meta': [
                f'📦 {collection}',
                f'🗓 {generated_at[:16].replace("T", " ")}',
                f'⚡ {model}'
            ],
            'header_numbers': header_numbers,
            'navigation': navigation,
            'fill_section_html': fill_section_html,
            'category_stats_html': category_stats_html,
            'synonym_dist_html': synonym_dist_html,
            'richest_html': richest_html or '—',
            'poorest_html': poorest_html or '—',
            'search_results_html': search_results_html,
            'vector_search': bool(vector_search),
            'report_data': data,
            'styles_css': self.styles_css,
            'components_js': self.components_js,
            'footer_text': f'{collection} · {generated_at[:16].replace("T", " ")} · {model}'
        }
        
        # Рендеринг
        template = self.env.get_template('dictionary_report.html')
        html_content = template.render(**context)
        
        # Сохранение
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.dist_dir / f'dictionary_report_{timestamp}.html'
        else:
            output_path = Path(output_path)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding='utf-8')
        
        return str(output_path)
    
    def generate_custom_report(
        self,
        template_name: str,
        context: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Генерация отчёта по произвольному шаблону
        
        Args:
            template_name: Имя шаблона
            context: Контекст для рендеринга
            output_path: Путь для сохранения
            
        Returns:
            Путь к сохранённому файлу
        """
        if 'styles_css' not in context:
            context['styles_css'] = self.styles_css
        if 'components_js' not in context:
            context['components_js'] = self.components_js
        
        template = self.env.get_template(template_name)
        html_content = template.render(**context)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding='utf-8')
        
        return str(output_path)


# Пример использования
if __name__ == '__main__':
    # Тестовые данные
    sample_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'collection_name': 'test_collection',
            'total_points': 1000,
            'embedding_model': 'TestModel v1'
        },
        'total': 1000,
        'all_categories': ['cat1', 'cat2', 'cat3'],
        'fill_summary': {
            'key': {'filled': 1000, 'filled_pct': 100, 'empty': 0, 'null': 0},
            'synonyms': {
                'missing': 10, 'missing_pct': 1.0,
                'one_synonym': 100, 'one_pct': 10.0,
                'many_synonyms': 890, 'many_pct': 89.0,
                'length_stats': {'min': 1, 'max': 20, 'avg': 5.5, 'p50': 5}
            }
        },
        'category_stats': {
            'cat1': {'count': 500, 'no_synonyms': 5, 'syn_length_stats': {'avg': 6.2}},
            'cat2': {'count': 300, 'no_synonyms': 3, 'syn_length_stats': {'avg': 4.8}},
            'cat3': {'count': 200, 'no_synonyms': 2, 'syn_length_stats': {'avg': 5.1}}
        },
        'synonym_distribution': [
            {'count': 0, 'entries': 10, 'pct': 1.0},
            {'count': 1, 'entries': 100, 'pct': 10.0},
            {'count': 5, 'entries': 500, 'pct': 50.0},
            {'count': 10, 'entries': 390, 'pct': 39.0}
        ],
        'richest_entries': [
            {'key': 'luxury', 'category': 'room_class', 'synonyms': ['люкс', 'deluxe', 'suite'] * 5, 'syn_count': 15}
        ],
        'poorest_entries': [
            {'key': 'basic', 'category': 'room_class', 'synonyms': ['базовый'], 'syn_count': 1}
        ]
    }
    
    generator = ReportGenerator()
    generator.load_components_js()
    output_file = generator.generate_dictionary_report(sample_data)
    print(f"Report generated: {output_file}")
