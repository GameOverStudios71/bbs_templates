from flask import Flask, render_template_string
import sqlite3
import json
from typing import List, Dict

app = Flask(__name__)
DATABASE_PATH = 'presets.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_preset_files(preset_id: int) -> Dict[str, str]:
    """Get HTML, CSS, and JS content for a preset."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT file_type, content 
        FROM files 
        WHERE preset_id = ?
    ''', (preset_id,))
    
    files = {}
    for row in cursor.fetchall():
        files[row['file_type']] = row['content']
    
    conn.close()
    return files

def get_categories_with_presets() -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            c.id as category_id, 
            c.name as category_name,
            p.id as preset_id,
            p.name as preset_name,
            p.description as preset_description
        FROM categories c
        LEFT JOIN presets p ON c.id = p.category_id
        ORDER BY c.name, p.name
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    categories = {}
    for row in rows:
        category_id = row['category_id']
        if category_id not in categories:
            categories[category_id] = {
                'id': category_id,
                'name': row['category_name'],
                'presets': []
            }
        
        if row['preset_id']:
            preset_id = row['preset_id']
            files = get_preset_files(preset_id)
            
            preview_html = files.get('html', '')
            preview_css = files.get('css', '')
            preview_js = files.get('js', '')
            
            # Create preview content
            preview_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>{preview_css}</style>
            </head>
            <body>
                {preview_html}
                <script>{preview_js}</script>
            </body>
            </html>
            """
            
            categories[category_id]['presets'].append({
                'id': preset_id,
                'name': row['preset_name'],
                'description': row['preset_description'] or 'No description available',
                'preview': preview_content,
                'files': {
                    'html': preview_html,
                    'css': preview_css,
                    'js': preview_js
                }
            })
    
    return list(categories.values())

@app.route('/')
def index():
    categories = get_categories_with_presets()
    
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BBS Presets</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f8f9fa;
                padding: 20px 0;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .category-card {
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
                overflow: hidden;
            }
            .category-header {
                background-color: #f1f8ff;
                padding: 1rem 1.5rem;
                border-bottom: 1px solid #dee2e6;
            }
            .category-header h2 {
                margin: 0;
                font-size: 1.5rem;
                color: #0d6efd;
            }
            .presets-container {
                padding: 1.5rem;
            }
            .preset-card {
                height: 100%;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                transition: all 0.3s ease;
                display: flex;
                flex-direction: column;
            }
            .preset-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
                border-color: #86b7fe;
            }
            .preset-body {
                padding: 1.25rem;
                flex: 1;
                display: flex;
                flex-direction: column;
            }
            .preset-title {
                font-size: 1.1rem;
                margin-bottom: 0.75rem;
                color: #212529;
            }
            .preset-description {
                color: #6c757d;
                font-size: 0.9rem;
                margin-bottom: 1rem;
                flex-grow: 1;
            }
            .btn-view {
                align-self: flex-start;
                background-color: #0d6efd;
                border: none;
                padding: 0.375rem 0.75rem;
                font-size: 0.875rem;
                border-radius: 4px;
                color: white;
                text-decoration: none;
                transition: background-color 0.2s;
            }
            .btn-view:hover {
                background-color: #0b5ed7;
                color: white;
            }
            .no-presets {
                color: #6c757d;
                font-style: italic;
                padding: 1rem 0;
            }
            .page-header {
                margin-bottom: 2rem;
                padding-bottom: 1rem;
                border-bottom: 1px solid #e9ecef;
            }
            .page-title {
                color: #0d6efd;
                margin-bottom: 0.5rem;
            }
            .page-subtitle {
                color: #6c757d;
                font-size: 1.1rem;
            }
            @media (max-width: 768px) {
                .preset-card {
                    margin-bottom: 1rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header class="page-header">
                <h1 class="page-title">BBS Presets</h1>
                <p class="page-subtitle">Browse and manage your presets collection</p>
            </header>
            
            <div id="app">
                {% if categories %}
                    {% for category in categories %}
                    <div class="category-card">
                        <div class="category-header">
                            <h2>{{ category.name }}</h2>
                        </div>
                        <div class="presets-container">
                            <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
                                {% if category.presets %}
                                    {% for preset in category.presets %}
                                    <div class="col">
                                        <div class="preset-card" data-preset-id="{{ preset.id }}" style="cursor: pointer;">
                                            <div class="preset-body">
                                                <h3 class="preset-title">{{ preset.name }}</h3>
                                                <p class="preset-description">{{ preset.description }}</p>
                                                <div class="card-preview">
                                                    <div class="preview-iframe-container">
                                                        <iframe class="preview-iframe" sandbox="allow-scripts" data-preset-id="{{ preset.id }}"></iframe>
                                                    </div>
                                                    <div class="preview-actions">
                                                        <button class="btn btn-sm btn-outline-primary preview-btn" data-preset-id="{{ preset.id }}">
                                                            <i class="bi bi-arrows-fullscreen"></i> Expandir
                                                        </button>
                                                    </div>
                                                </div>
                                                <div class="preview-container" id="preview-{{ preset.id }}" style="display: none;">
                                                    <div class="preview-content">
                                                        <div class="preview-tabs">
                                                            <button class="preview-tab active" data-tab="preview">Preview</button>
                                                            <button class="preview-tab" data-tab="html">HTML</button>
                                                            <button class="preview-tab" data-tab="css">CSS</button>
                                                            <button class="preview-tab" data-tab="js">JS</button>
                                                        </div>
                                                        <div class="preview-frame-container">
                                                            <iframe class="preview-frame" id="preview-frame-{{ preset.id }}" sandbox="allow-scripts"></iframe>
                                                            <pre class="code-preview" id="html-{{ preset.id }}" style="display: none;"><code>{{ preset.files.html|e }}</code></pre>
                                                            <pre class="code-preview" id="css-{{ preset.id }}" style="display: none;"><code>{{ preset.files.css|e }}</code></pre>
                                                            <pre class="code-preview" id="js-{{ preset.id }}" style="display: none;"><code>{{ preset.files.js|e }}</code></pre>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    {% endfor %}
                                {% else %}
                                    <div class="col-12">
                                        <p class="no-presets">No presets available in this category.</p>
                                    </div>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                    
                    <!-- Preview Modal -->
                    <div class="modal fade" id="previewModal" tabindex="-1" aria-hidden="true">
                        <div class="modal-dialog modal-xl">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title" id="previewModalLabel">Preview</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                </div>
                                <div class="modal-body">
                                    <div class="preview-tabs">
                                        <button class="preview-tab active" data-tab="preview">Preview</button>
                                        <button class="preview-tab" data-tab="html">HTML</button>
                                        <button class="preview-tab" data-tab="css">CSS</button>
                                        <button class="preview-tab" data-tab="js">JS</button>
                                    </div>
                                    <div class="preview-content">
                                        <iframe id="previewFrame" class="preview-frame" sandbox="allow-scripts"></iframe>
                                        <pre id="htmlContent" class="code-preview" style="display: none;"><code></code></pre>
                                        <pre id="cssContent" class="code-preview" style="display: none;"><code></code></pre>
                                        <pre id="jsContent" class="code-preview" style="display: none;"><code></code></pre>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                {% else %}
                    <div class="alert alert-info">
                        No categories found. Please import some presets first.
                    </div>
                {% endif %}
            </div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            console.log('BBS Presets app initialized');
            
            // Initialize tooltips if any
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
            
            // Initialize modals
            const previewModal = new bootstrap.Modal(document.getElementById('previewModal'));
            
            // Handle tab switching in the preview modal
            function setupTabs(container, presetId = null) {
                const tabs = container.querySelectorAll('.preview-tab');
                tabs.forEach(tab => {
                    tab.addEventListener('click', function(e) {
                        e.stopPropagation();
                        const tabName = this.getAttribute('data-tab');
                        
                        // Update active tab
                        tabs.forEach(t => t.classList.remove('active'));
                        this.classList.add('active');
                        
                        // Hide all content
                        container.querySelectorAll('.preview-frame, .code-preview').forEach(el => {
                            el.style.display = 'none';
                        });
                        
                        // Show selected content
                        if (tabName === 'preview') {
                            container.querySelector('.preview-frame').style.display = 'block';
                        } else if (presetId) {
                            const content = container.querySelector(`#${tabName}-${presetId}`);
                            if (content) content.style.display = 'block';
                        } else {
                            const content = container.querySelector(`#${tabName}Content`);
                            if (content) content.style.display = 'block';
                        }
                    });
                });
            }
            
            // Set up click handlers for preset cards
            document.querySelectorAll('.preset-card').forEach(card => {
                card.addEventListener('click', function(e) {
                    if (e.target.closest('.preview-tab')) return;
                    
                    const presetId = this.querySelector('[id^="preview-"]')?.id.replace('preview-', '');
                    if (!presetId) return;
                    
                    const previewContent = document.getElementById(`preview-${presetId}`).innerHTML;
                    const modalBody = document.querySelector('#previewModal .modal-body');
                    const htmlCode = document.querySelector(`#html-${presetId} code`).textContent;
                    const cssCode = document.querySelector(`#css-${presetId} code`).textContent;
                    const jsCode = document.querySelector(`#js-${presetId} code`).textContent;
                    
                    modalBody.innerHTML = `
                        <div class="preview-content">
                            <div class="preview-tabs">
                                <button class="preview-tab active" data-tab="preview">Preview</button>
                                <button class="preview-tab" data-tab="html">HTML</button>
                                <button class="preview-tab" data-tab="css">CSS</button>
                                <button class="preview-tab" data-tab="js">JS</button>
                            </div>
                            <div class="preview-frame-container">
                                <iframe class="preview-frame" id="preview-frame-${presetId}" sandbox="allow-scripts"></iframe>
                                <pre class="code-preview" id="html-${presetId}" style="display: none;"><code>${htmlCode.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>
                                <pre class="code-preview" id="css-${presetId}" style="display: none;"><code>${cssCode.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>
                                <pre class="code-preview" id="js-${presetId}" style="display: none;"><code>${jsCode.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>
                            </div>
                        </div>
                    `;
                    
                    // Set up the preview iframe
                    const previewFrame = modalBody.querySelector('.preview-frame');
                    if (previewFrame) {
                        const htmlContent = document.querySelector(`#html-${presetId} code`).textContent;
                        const cssContent = document.querySelector(`#css-${presetId} code`).textContent;
                        const jsContent = document.querySelector(`#js-${presetId} code`).textContent;
                        
                        // Create a data URL with the content
                        const previewHtml = `
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <base target="_parent">
                                <style>
                                    ${cssContent.replace(/`/g, '\`')}
                                    body { margin: 0; padding: 10px; }
                                </style>
                            </head>
                            <body>
                                ${htmlContent.replace(/`/g, '\`')}
                                <script>
                                    try {
                                        ${jsContent.replace(/`/g, '\`')}
                                    } catch (e) {
                                        console.error('Error in preview script:', e);
                                    }
                                <\/script>
                            </body>
                            </html>
                        `;
                        
                        // Set the iframe's src to a data URL
                        const dataUrl = 'data:text/html;charset=utf-8,' + encodeURIComponent(previewHtml);
                        previewFrame.src = dataUrl;
                    }
                    
                    // Set up tabs in the modal
                    setupTabs(modalBody, presetId);
                    
                    // Show the modal
                    previewModal.show();
                });
            });
            
            // Set up any initial tabs (if any)
            document.querySelectorAll('.preview-content').forEach(container => {
                setupTabs(container);
            });
            
            // Initialize card previews
            document.querySelectorAll('.preview-iframe').forEach(iframe => {
                const presetId = iframe.getAttribute('data-preset-id');
                if (presetId) {
                    const htmlContent = document.querySelector(`#html-${presetId} code`).textContent;
                    const cssContent = document.querySelector(`#css-${presetId} code`).textContent;
                    const previewHtml = `
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <base target="_parent">
                            <style>
                                ${cssContent.replace(/`/g, '\`')}
                                body { 
                                    margin: 0; 
                                    padding: 5px;
                                    transform-origin: 0 0;
                                    transform: scale(0.5);
                                    width: 200%;
                                    height: 200%;
                                }
                            </style>
                        </head>
                        <body>
                            ${htmlContent.replace(/`/g, '\`')}
                        </body>
                        </html>
                    `;
                    iframe.srcdoc = previewHtml;
                }
            });
            
            // Make preview buttons open the modal
            document.querySelectorAll('.preview-btn').forEach(btn => {
                btn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    const presetId = this.getAttribute('data-preset-id');
                    if (presetId) {
                        const card = this.closest('.preset-card');
                        if (card) card.click();
                    }
                });
            });
            
            // Close modal when clicking outside or pressing Escape
            document.addEventListener('click', function(e) {
                const modal = document.getElementById('previewModal');
                if (e.target === modal) {
                    previewModal.hide();
                }
            });
            
            // Close modal with Escape key
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    previewModal.hide();
                }
            });
            
            // Remove any inline onclick handlers that might be causing issues
            document.querySelectorAll('.preset-card[onclick]').forEach(card => {
                const presetId = card.getAttribute('data-preset-id');
                card.removeAttribute('onclick');
                if (presetId) {
                    card.setAttribute('data-preset-id', presetId);
                }
            });
        });
        </script>
        <style>
            .preview-tabs {
                display: flex;
                border-bottom: 1px solid #dee2e6;
                margin-bottom: 1rem;
            }
            .preview-tab {
                padding: 0.5rem 1rem;
                background: none;
                border: none;
                border-bottom: 2px solid transparent;
                cursor: pointer;
                margin-right: 0.5rem;
            }
            .preview-tab.active {
                border-bottom-color: #0d6efd;
                color: #0d6efd;
                font-weight: 500;
            }
            .preview-frame {
                width: 100%;
                height: 500px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background: white;
            }
            .code-preview {
                height: 500px;
                margin: 0;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background: #f8f9fa;
                overflow: auto;
                padding: 1rem;
                white-space: pre-wrap;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                line-height: 1.5;
            }
            .modal-xl {
                max-width: 90%;
            }
            .modal-body {
                padding: 0;
            }
            .preview-content {
                padding: 1rem;
            }
            
            /* Card Preview Styles */
            .card-preview {
                margin-top: 1rem;
                border: 1px solid #dee2e6;
                border-radius: 0.25rem;
                overflow: hidden;
                background: #f8f9fa;
            }
            
            .preview-iframe-container {
                position: relative;
                width: 100%;
                height: 200px;
                overflow: hidden;
                background: white;
            }
            
            .preview-iframe {
                width: 100%;
                height: 100%;
                border: none;
                transform-origin: 0 0;
                transform: scale(0.5);
                pointer-events: none;
            }
            
            .preview-actions {
                padding: 0.5rem;
                background: #f8f9fa;
                border-top: 1px solid #dee2e6;
                text-align: center;
            }
            
            .preview-btn {
                font-size: 0.75rem;
                padding: 0.15rem 0.5rem;
            }
            
            .preview-btn i {
                margin-right: 0.25rem;
            }
        </style>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    return render_template_string(html, categories=categories)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
