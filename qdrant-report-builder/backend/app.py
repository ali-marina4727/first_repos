"""
Qdrant Report Builder - Backend API
Flask application for managing report generation from Qdrant collections
"""

from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
import json
import os
from pathlib import Path
from datetime import datetime
import hashlib

app = Flask(__name__, static_folder='../static', template_folder='../templates')
CORS(app)

# Configuration
QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
QDRANT_PORT = int(os.getenv('QDRANT_PORT', '6333'))
REPORTS_DIR = Path('/workspace/qdrant-report-builder/generated_reports')
REPORTS_DIR.mkdir(exist_ok=True)

# In-memory storage for configurations (can be replaced with DB)
report_configs = {}

def get_qdrant_client():
    """Initialize Qdrant client"""
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

@app.route('/')
def index():
    """Serve the main application"""
    return send_from_directory('../static', 'index.html')

@app.route('/api/collections', methods=['GET'])
def get_collections():
    """Get list of all collections from Qdrant"""
    try:
        client = get_qdrant_client()
        collections = client.get_collections().collections
        collection_names = [col.name for col in collections]
        return jsonify({'collections': collection_names})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/collections/<collection_name>/schema', methods=['GET'])
def get_collection_schema(collection_name):
    """Get schema information for a collection"""
    try:
        client = get_qdrant_client()
        info = client.get_collection(collection_name)
        
        # Sample points to extract payload fields
        points = client.scroll(
            collection_name=collection_name,
            limit=10,
            with_payload=True,
            with_vectors=False
        )[0]
        
        # Extract unique payload fields
        payload_fields = set()
        field_types = {}
        
        for point in points:
            if point.payload:
                for key, value in point.payload.items():
                    payload_fields.add(key)
                    field_types[key] = type(value).__name__
        
        return jsonify({
            'collection_name': collection_name,
            'vectors_count': info.vectors_count,
            'points_count': info.points_count,
            'payload_fields': list(payload_fields),
            'field_types': field_types,
            'status': info.status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/collections/<collection_name>/sample', methods=['GET'])
def get_sample_data(collection_name):
    """Get sample data from collection"""
    try:
        limit = request.args.get('limit', 10, type=int)
        client = get_qdrant_client()
        
        points = client.scroll(
            collection_name=collection_name,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )[0]
        
        samples = []
        for point in points:
            samples.append({
                'id': point.id,
                'payload': point.payload
            })
        
        return jsonify({'samples': samples, 'count': len(samples)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/configs', methods=['POST'])
def save_config():
    """Save report configuration"""
    config = request.json
    config_id = hashlib.md5(json.dumps(config, sort_keys=True).encode()).hexdigest()[:8]
    config['id'] = config_id
    config['created_at'] = datetime.now().isoformat()
    
    report_configs[config_id] = config
    
    # Save to file
    config_file = REPORTS_DIR / f'config_{config_id}.json'
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    return jsonify(config)

@app.route('/api/configs/<config_id>', methods=['GET'])
def get_config(config_id):
    """Get report configuration"""
    if config_id in report_configs:
        return jsonify(report_configs[config_id])
    
    # Try to load from file
    config_file = REPORTS_DIR / f'config_{config_id}.json'
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
            report_configs[config_id] = config
            return jsonify(config)
    
    return jsonify({'error': 'Config not found'}), 404

@app.route('/api/configs', methods=['GET'])
def list_configs():
    """List all saved configurations"""
    configs = []
    
    # From memory
    configs.extend(report_configs.values())
    
    # From files
    for config_file in REPORTS_DIR.glob('config_*.json'):
        config_id = config_file.stem.replace('config_', '')
        if config_id not in report_configs:
            with open(config_file, 'r') as f:
                config = json.load(f)
                configs.append(config)
    
    return jsonify({'configs': configs})

@app.route('/api/generate', methods=['POST'])
def generate_report():
    """Generate report from configuration"""
    config = request.json
    
    try:
        client = get_qdrant_client()
        collection_name = config['collection_name']
        
        # Fetch all points with payload
        all_points = []
        offset = None
        
        while True:
            points, next_offset = client.scroll(
                collection_name=collection_name,
                limit=100,
                with_payload=True,
                with_vectors=False,
                offset=offset
            )
            all_points.extend(points)
            if next_offset is None:
                break
            offset = next_offset
        
        # Prepare data for report
        report_data = {
            'collection_name': collection_name,
            'generated_at': datetime.now().isoformat(),
            'total_points': len(all_points),
            'config': config,
            'data': []
        }
        
        # Extract relevant fields based on config
        fields_to_extract = []
        for block in config.get('blocks', []):
            if 'field' in block:
                fields_to_extract.append(block['field'])
            if 'fields' in block:
                fields_to_extract.extend(block['fields'])
        
        fields_to_extract = list(set(fields_to_extract))
        
        for point in all_points:
            row = {'id': point.id}
            for field in fields_to_extract:
                row[field] = point.payload.get(field) if point.payload else None
            report_data['data'].append(row)
        
        # Generate HTML report
        html_content = generate_html_report(report_data, config)
        
        # Save report
        report_filename = f"report_{collection_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        report_path = REPORTS_DIR / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return jsonify({
            'success': True,
            'report_path': f'/api/reports/{report_filename}',
            'download_url': f'/api/reports/download/{report_filename}',
            'points_processed': len(all_points)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_html_report(data, config):
    """Generate standalone HTML report"""
    
    # Aggregate data for charts
    chart_data = {}
    for block in config.get('blocks', []):
        if block.get('type') == 'chart' and 'field' in block:
            field = block['field']
            chart_type = block.get('chart_type', 'bar')
            
            # Count values
            value_counts = {}
            for row in data['data']:
                value = row.get(field)
                if value is not None:
                    value_str = str(value)
                    value_counts[value_str] = value_counts.get(value_str, 0) + 1
            
            chart_data[field] = {
                'labels': list(value_counts.keys()),
                'values': list(value_counts.values()),
                'type': chart_type,
                'field': field
            }
    
    # KPI calculations
    kpi_data = []
    for block in config.get('blocks', []):
        if block.get('type') == 'kpi':
            kpi = {
                'title': block.get('title', 'KPI'),
                'value': block.get('value', 0),
                'field': block.get('field'),
                'format': block.get('format', 'number')
            }
            
            if 'field' in block and block['field']:
                # Calculate from data
                field_values = [row.get(block['field']) for row in data['data']]
                numeric_values = [v for v in field_values if isinstance(v, (int, float))]
                
                if block.get('aggregation') == 'sum':
                    kpi['value'] = sum(numeric_values) if numeric_values else 0
                elif block.get('aggregation') == 'avg':
                    kpi['value'] = sum(numeric_values) / len(numeric_values) if numeric_values else 0
                elif block.get('aggregation') == 'count':
                    kpi['value'] = len([v for v in field_values if v is not None])
                elif block.get('aggregation') == 'unique':
                    kpi['value'] = len(set(str(v) for v in field_values if v is not None))
            
            kpi_data.append(kpi)
    
    # Table data
    table_config = None
    table_rows = []
    for block in config.get('blocks', []):
        if block.get('type') == 'table':
            table_config = block
            columns = block.get('columns', [])
            
            for row in data['data']:
                table_row = {}
                for col in columns:
                    field = col.get('field') if isinstance(col, dict) else col
                    table_row[field] = row.get(field)
                table_rows.append(table_row)
            break
    
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчёт: {data['collection_name']}</title>
    <style>
        :root {{
            --primary: #10b981;
            --primary-dark: #059669;
            --bg: #f9fafb;
            --card-bg: #ffffff;
            --text: #1f2937;
            --text-light: #6b7280;
            --border: #e5e7eb;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        header {{
            background: var(--card-bg);
            padding: 2rem;
            margin-bottom: 2rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
            color: var(--text);
        }}
        
        .meta {{
            color: var(--text-light);
            font-size: 0.875rem;
        }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .kpi-card {{
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border-left: 4px solid var(--primary);
        }}
        
        .kpi-title {{
            font-size: 0.875rem;
            color: var(--text-light);
            margin-bottom: 0.5rem;
        }}
        
        .kpi-value {{
            font-size: 2rem;
            font-weight: bold;
            color: var(--text);
        }}
        
        .section {{
            background: var(--card-bg);
            padding: 2rem;
            margin-bottom: 2rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .section-title {{
            font-size: 1.25rem;
            margin-bottom: 1.5rem;
            color: var(--text);
        }}
        
        .chart-container {{
            position: relative;
            height: 400px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        
        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        
        th {{
            background: var(--bg);
            font-weight: 600;
            font-size: 0.875rem;
            color: var(--text-light);
        }}
        
        tr:hover {{
            background: var(--bg);
        }}
        
        .table-container {{
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Отчёт: {data['collection_name']}</h1>
            <p class="meta">Сгенерировано: {data['generated_at']} | Записей: {data['total_points']}</p>
        </header>
        
        <!-- KPI Cards -->
        {generate_kpi_html(kpi_data)}
        
        <!-- Charts -->
        {generate_charts_html(chart_data)}
        
        <!-- Tables -->
        {generate_table_html(table_config, table_rows) if table_config else ''}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script>
        // Chart initialization code
        {generate_chart_js(chart_data)}
    </script>
</body>
</html>'''
    
    return html

def generate_kpi_html(kpi_data):
    """Generate KPI cards HTML"""
    if not kpi_data:
        return ''
    
    html = '<div class="kpi-grid">\n'
    for kpi in kpi_data:
        value = kpi['value']
        if isinstance(value, float):
            value = f'{value:,.2f}'
        elif isinstance(value, int):
            value = f'{value:,}'
        
        html += f'''
        <div class="kpi-card">
            <div class="kpi-title">{kpi['title']}</div>
            <div class="kpi-value">{value}</div>
        </div>\n'''
    html += '</div>\n'
    return html

def generate_charts_html(chart_data):
    """Generate charts sections HTML"""
    if not chart_data:
        return ''
    
    html = ''
    for field, data in chart_data.items():
        html += f'''
        <div class="section">
            <h2 class="section-title">Распределение: {field}</h2>
            <div class="chart-container">
                <canvas id="chart-{field}"></canvas>
            </div>
        </div>\n'''
    return html

def generate_chart_js(chart_data):
    """Generate chart initialization JavaScript"""
    if not chart_data:
        return ''
    
    js = '''
    document.addEventListener('DOMContentLoaded', function() {\n'''
    
    for field, data in chart_data.items():
        colors = generate_colors(len(data['labels']))
        
        js += f'''
        new Chart(document.getElementById('chart-{field}'), {{
            type: '{data['type']}',
            data: {{
                labels: {json.dumps(data['labels'])},
                datasets: [{{
                    label: '{field}',
                    data: {json.dumps(data['values'])},
                    backgroundColor: {json.dumps(colors)},
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'top',
                    }}
                }}
            }}
        }});\n'''
    
    js += '    });\n'
    return js

def generate_colors(count):
    """Generate color palette"""
    base_colors = [
        '#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444',
        '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'
    ]
    
    colors = []
    for i in range(count):
        colors.append(base_colors[i % len(base_colors)])
    return colors

def generate_table_html(table_config, rows):
    """Generate table HTML"""
    if not table_config or not rows:
        return ''
    
    columns = table_config.get('columns', [])
    if not columns:
        return ''
    
    html = '''
    <div class="section">
        <h2 class="section-title">Данные</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>\n'''
    
    for col in columns:
        header = col.get('title', col.get('field', col)) if isinstance(col, dict) else col
        html += f'                        <th>{header}</th>\n'
    
    html += '''                    </tr>
                </thead>
                <tbody>\n'''
    
    for row in rows[:100]:  # Limit to 100 rows for performance
        html += '                    <tr>\n'
        for col in columns:
            field = col.get('field', col) if isinstance(col, dict) else col
            value = row.get(field, '')
            if value is None:
                value = '-'
            html += f'                        <td>{value}</td>\n'
        html += '                    </tr>\n'
    
    html += '''                </tbody>
            </table>
        </div>
    </div>\n'''
    
    return html

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
