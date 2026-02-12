from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QTextBrowser,
                             QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, 
                             QGraphicsLineItem, QGraphicsItem, QFrame)
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QBrush, QPen, QColor, QPainter, QPainterPath
from .styles import get_stylesheet, THEME_COLORS
import json
import os
import math

class GraphNode(QGraphicsEllipseItem):
    """Visual Node in the Knowledge Graph."""
    def __init__(self, text, node_type, data=None):
        super().__init__(-25, -25, 50, 50)
        self.text = text
        self.node_type = node_type # 'root', 'category', 'intent'
        self.data = data or {}
        self.edges = []
        
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges |
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        
        # Color based on type
        if node_type == 'root': self.color = QColor("#FFD700") # Gold
        elif node_type == 'category': self.color = QColor("#00FFFF") # Cyan
        else: self.color = QColor("#39FF14") # Green

    def add_edge(self, edge):
        self.edges.append(edge)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)

    def paint(self, painter, option, widget):
        # Body
        painter.setBrush(QBrush(self.color if not self.isSelected() else Qt.GlobalColor.white))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawEllipse(self.rect())
        
        # Label (Shortened)
        painter.setPen(Qt.GlobalColor.black)
        font = painter.font()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        
        display_text = self.text if len(self.text) < 10 else self.text[:8] + ".."
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, display_text)

class GraphEdge(QGraphicsLineItem):
    """Line connecting two GraphNodes."""
    def __init__(self, source, target):
        super().__init__()
        self.source = source
        self.target = target
        self.source.add_edge(self)
        self.target.add_edge(self)
        
        self.setZValue(-1)
        pen = QPen(QColor(100, 100, 100, 150), 1)
        self.setPen(pen)
        self.update_position()

    def update_position(self):
        self.setLine(self.source.scenePos().x(), self.source.scenePos().y(),
                     self.target.scenePos().x(), self.target.scenePos().y())

class KnowledgeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cortex Intelligence - Knowledge Graph")
        self.setGeometry(150, 150, 1100, 750)
        
        # Theme
        try:
            config_path = os.path.join(os.getcwd(), 'data', 'user_config.json')
            with open(config_path, 'r') as f:
                theme = json.load(f).get("theme", "Neon Green")
        except: theme = "Neon Green"
        self.setStyleSheet(get_stylesheet(theme))
        
        self.accent_color = THEME_COLORS.get(theme, "#39FF14")

        # Main Layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        
        # Left: Graph Sidebar & Search
        left_panel = QWidget()
        left_panel.setFixedWidth(250)
        left_layout = QVBoxLayout(left_panel)
        
        left_layout.addWidget(QLabel("Knowledge Explorer", objectName="SubHeader"))
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search intents...")
        self.search_bar.textChanged.connect(self.filter_graph)
        left_layout.addWidget(self.search_bar)
        
        self.info_panel = QTextBrowser()
        self.info_panel.setHtml("<p style='color: gray;'>Click a node to view metadata...</p>")
        left_layout.addWidget(QLabel("Node Details:"))
        left_layout.addWidget(self.info_panel)
        
        layout.addWidget(left_panel)
        
        # Right: Canvas
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-1000, -1000, 2000, 2000)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        layout.addWidget(self.view)
        
        # Initialize
        self.nodes = []
        self.load_graph_data()
        
        # Selection event
        self.scene.selectionChanged.connect(self.on_selection_changed)

    def load_graph_data(self):
        """Loads intents from JSON and builds the visual tree."""
        # 1. Create Root
        cortex_root = GraphNode("Cortex", "root")
        self.scene.addItem(cortex_root)
        cortex_root.setPos(0, 0)
        self.nodes.append(cortex_root)
        
        intents_dir = os.path.join(os.getcwd(), 'data', 'intents')
        if not os.path.exists(intents_dir): return
        
        files = [f for f in os.listdir(intents_dir) if f.endswith('.json')]
        
        # 2. Add Category Nodes (Level 1)
        angle_step = (2 * math.pi) / len(files) if files else 0
        radius_lvl1 = 250
        
        for i, filename in enumerate(files):
            category_name = filename.replace('.json', '').capitalize()
            angle = i * angle_step
            x = radius_lvl1 * math.cos(angle)
            y = radius_lvl1 * math.sin(angle)
            
            cat_node = GraphNode(category_name, "category")
            self.scene.addItem(cat_node)
            cat_node.setPos(x, y)
            self.nodes.append(cat_node)
            
            # Connect to root
            self.scene.addItem(GraphEdge(cortex_root, cat_node))
            
            # 3. Add Intent Nodes (Level 2)
            try:
                with open(os.path.join(intents_dir, filename), 'r') as f:
                    data = json.load(f)
                    
                intents = data.get('intents', [])
                intent_angle_step = (math.pi * 0.5) / (len(intents) if intents else 1) # Spread in an arc 
                radius_lvl2 = 180
                
                for j, intent in enumerate(intents):
                    # Offset position relative to category
                    # We want them to spread outwards from the center
                    io_angle = angle + (j - len(intents)/2) * 0.15
                    ix = x + radius_lvl2 * math.cos(io_angle)
                    iy = y + radius_lvl2 * math.sin(io_angle)
                    
                    int_node = GraphNode(intent['tag'], "intent", intent)
                    self.scene.addItem(int_node)
                    int_node.setPos(ix, iy)
                    self.nodes.append(int_node)
                    
                    self.scene.addItem(GraphEdge(cat_node, int_node))
                    
            except Exception as e:
                print(f"Error loading {filename}: {e}")

    def on_selection_changed(self):
        selected = self.scene.selectedItems()
        if selected and isinstance(selected[0], GraphNode):
            node = selected[0]
            if node.node_type == 'intent':
                patterns = node.data.get('patterns', [])
                responses = node.data.get('responses', [])
                
                html = f"<h3>Intent: {node.text}</h3>"
                html += "<b>Patterns (Triggers):</b><ul>"
                for p in patterns[:10]: html += f"<li>{p}</li>"
                if len(patterns) > 10: html += "<li>...</li>"
                html += "</ul>"
                
                if responses:
                    html += "<b>Sample Responses:</b><ul>"
                    for r in responses[:5]: html += f"<li>{r}</li>"
                    html += "</ul>"
                
                self.info_panel.setHtml(html)
            else:
                self.info_panel.setHtml(f"<h3>{node.text}</h3><p>Category node grouping intents.</p>")

    def filter_graph(self, text):
        text = text.lower()
        for node in self.nodes:
            if not text:
                node.setSelected(False)
                node.update()
                continue
                
            if text in node.text.lower():
                node.setSelected(True)
            else:
                node.setSelected(False)
            node.update()
