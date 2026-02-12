from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFrame, QSplitter, QListWidget,
                             QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsPathItem,
                             QInputDialog, QMenu, QMessageBox)
from PyQt6.QtCore import Qt, QRectF, QPointF, QMimeData
from PyQt6.QtGui import QBrush, QPen, QColor, QPainter, QPainterPath, QDrag, QPainterPathStroker
from .styles import get_stylesheet, THEME_COLORS

# --- 0. Custom List Widget to ensure clean Mime Data ---
class NodeList(QListWidget):
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < 10:
            return

        item = self.currentItem()
        if item:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(item.text())
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.CopyAction)

# --- 1. Connection Line (Bezier Curve) ---
class ConnectionPath(QGraphicsPathItem):
    def __init__(self, start_port, end_port=None, cur_pos=None):
        super().__init__()
        self.setZValue(-1) 
        self.start_port = start_port
        self.end_port = end_port
        self.cur_pos = cur_pos if cur_pos else start_port.scenePos()
        
        # Track connections in ports
        self.start_port.add_connection(self)
        if self.end_port:
            self.end_port.add_connection(self)
        
        pen = QPen(QColor("#39FF14"), 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.update_path()
        
    def update_pos(self, pos):
        self.cur_pos = pos
        self.update_path()
        
    def update_path(self):
        start = self.start_port.scenePos()
        end = self.end_port.scenePos() if self.end_port else self.cur_pos
        
        path = QPainterPath()
        path.moveTo(start)
        
        # Cubic Bezier Control Points
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        ctrl1 = QPointF(start.x() + dx * 0.5, start.y())
        ctrl2 = QPointF(end.x() - dx * 0.5, end.y())
        
        path.cubicTo(ctrl1, ctrl2, end)
        self.setPath(path)

    def shape(self):
        # Improve hit testing for thin lines
        path = self.path()
        stroker = QPainterPathStroker()
        stroker.setWidth(10) # 10px clickable width
        return stroker.createStroke(path)

# --- 2. Port Item (Input/Output Dots) ---
class PortItem(QGraphicsItem):
    def __init__(self, parent, port_type="out"):
        super().__init__(parent)
        self.parent_node = parent
        self.port_type = port_type # 'in' or 'out'
        self.radius = 6
        self.connections = []
        self.setAcceptHoverEvents(True)
        
        if port_type == "in":
            self.setPos(75, 0)
        else:
            self.setPos(75, 60)
            
    def add_connection(self, conn):
        if conn not in self.connections:
            self.connections.append(conn)
            
    def remove_connection(self, conn):
        if conn in self.connections:
            self.connections.remove(conn)

    def update_connections(self):
        for conn in self.connections:
            conn.update_path()

    def boundingRect(self):
        return QRectF(-self.radius, -self.radius, self.radius*2, self.radius*2)
        
    def paint(self, painter, option, widget):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#fff"))
        painter.drawEllipse(-self.radius, -self.radius, self.radius*2, self.radius*2)

# --- 3. Node Item ---
class NodeItem(QGraphicsItem):
    def __init__(self, text, x, y):
        super().__init__()
        self.text = text
        self.properties = {"value": ""}
        
        # Default Values
        if "Delay" in text:
            self.text = "Delay"
            self.properties["value"] = "5"
            
        self.setPos(x, y)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges |
                      QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        
        # Determine Color
        if text == "Start": self.color = QColor("#39FF14")
        elif text == "End": self.color = QColor("#FF3131")
        else: self.color = QColor("#00FFFF")
        
        # Add Ports
        self.in_port = None
        self.out_port = None
        
        if text != "Start":
            self.in_port = PortItem(self, "in")
        
        if text != "End":
            self.out_port = PortItem(self, "out")
            
    def mouseDoubleClickEvent(self, event):
        # Allow editing properties
        if self.text in ["Speak", "System Command", "Delay"]:
            prompt = f"Enter {self.text} value:"
            val, ok = QInputDialog.getText(None, "Node Properties", prompt, text=self.properties.get("value", ""))
            if ok:
                self.properties["value"] = val
                self.update()
        super().mouseDoubleClickEvent(event)
            
    def boundingRect(self):
        return QRectF(0, 0, 150, 60)
        
    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        
        # Shadow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 50))
        painter.drawRoundedRect(rect.adjusted(2, 2, 2, 2), 8, 8)
        
        # Body
        painter.setPen(QPen(self.color, 2))
        painter.setBrush(QColor(30, 30, 30, 200))
        painter.drawRoundedRect(rect, 8, 8)
        
        # Header
        painter.setBrush(self.color)
        painter.drawRoundedRect(0, 0, 150, 20, 8, 8)
        painter.drawRect(0, 10, 150, 10)
        
        # Label
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(QRectF(0, 0, 150, 20), Qt.AlignmentFlag.AlignCenter, self.text)

        # Property Preview
        if self.properties.get("value"):
            painter.setPen(Qt.GlobalColor.white)
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            painter.drawText(QRectF(10, 25, 130, 30), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, 
                             self.properties["value"])
        
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
             if self.in_port: self.in_port.update_connections()
             if self.out_port: self.out_port.update_connections()
        return super().itemChange(change, value)

# --- 4. Flow View (Interaction Manager) ---
class FlowView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.setScene(scene)
        self.setAcceptDrops(True)
        # Ensure the viewport accepts drops as well
        self.viewport().setAcceptDrops(True)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setSceneRect(0, 0, 5000, 5000)
        
        # Wiring State
        self.temp_line = None
        self.start_port = None
        
    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        
        # Cancellation/Deletion
        if event.button() == Qt.MouseButton.RightButton:
            if self.temp_line:
                self.scene().removeItem(self.temp_line)
                self.temp_line = None
                self.start_port = None
                return
            if isinstance(item, ConnectionPath):
                self._delete_connection(item)
                return
            if isinstance(item, NodeItem):
                self._delete_node(item)
                return

        if isinstance(item, PortItem) and item.port_type == 'out':
            # Support Multiple Connections (removed limit)
            self.start_port = item
            self.start_port = item
            self.temp_line = ConnectionPath(item)
            self.scene().addItem(self.temp_line)
            return 
            
        super().mousePressEvent(event)

    def _delete_connection(self, conn):
        if conn.start_port: conn.start_port.remove_connection(conn)
        if conn.end_port: conn.end_port.remove_connection(conn)
        self.scene().removeItem(conn)

    def _delete_node(self, node):
        if node.in_port:
            for c in list(node.in_port.connections): self._delete_connection(c)
        if node.out_port:
            for c in list(node.out_port.connections): self._delete_connection(c)
        self.scene().removeItem(node)
        
    def mouseMoveEvent(self, event):
        if self.temp_line:
            pos = self.mapToScene(event.pos())
            self.temp_line.update_pos(pos)
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        if self.temp_line:
            item = self.itemAt(event.pos())
            if isinstance(item, PortItem) and item.port_type == 'in' and item.parentItem() != self.start_port.parentItem():
                self.temp_line.end_port = item
                item.add_connection(self.temp_line) # <--- Fix: Register connection with input port
                self.temp_line.update_path()
                self.temp_line = None
            else:
                self.scene().removeItem(self.temp_line)
                self.temp_line = None
            self.start_port = None
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasText():
            node_type = event.mimeData().text()
            pos = self.mapToScene(event.position().toPoint())
            node = NodeItem(node_type, pos.x(), pos.y())
            self.scene().addItem(node)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

class AutomationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neural Sync - Automation Editor")
        self.setGeometry(100, 100, 1000, 700)
        
        # Apply Theme
        try:
            import json, os
            config_path = os.path.join(os.getcwd(), 'data', 'user_config.json')
            with open(config_path, 'r') as f:
                theme = json.load(f).get("theme", "Neon Green")
        except: theme = "Neon Green"
        self.setStyleSheet(get_stylesheet(theme))
        
        # Layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        layout.addWidget(QLabel("Neural Sync: Automation Logic"))
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Toolbox
        tools = NodeList() # Using our custom NodeList
        tools.addItems(["Start", "Speak", "Delay", "System Command", "End"])
        splitter.addWidget(tools)
        
        # Canvas
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 5000, 5000)
        self.view = FlowView(self.scene)
        splitter.addWidget(self.view)
        splitter.setSizes([200, 800])
        
        layout.addWidget(splitter)
        
        # Footer
        footer = QWidget()
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(0, 0, 0, 0)
        
        btn_apply = QPushButton("Apply Workflow")
        btn_apply.clicked.connect(self.save_workflow)
        
        btn_help = QPushButton("?")
        btn_help.setFixedSize(30, 30)
        accent = THEME_COLORS.get(theme, "#39FF14")
        btn_help.setStyleSheet(f"""
            QPushButton {{
                background-color: #333;
                color: {accent};
                border: 2px solid {accent};
                border-radius: 15px;
                font-size: 20px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {accent};
                color: black;
            }}
        """)
        btn_help.clicked.connect(self.show_help)
        
        f_layout.addWidget(btn_apply)
        f_layout.addWidget(btn_help)
        
        layout.addWidget(footer)

    def show_help(self):
        msg = """
        <h3>How to use Neural Sync</h3>
        <p><b>1. Add Nodes:</b> Drag nodes from the left toolbox to the canvas.</p>
        <p><b>2. Connect:</b> Drag from the BOTTOM connected of one node to the TOP connector of another.</p>
        <p><b>3. Logic:</b>
           <ul>
           <li><b>Speak:</b> Double-click to type what Cortex should say.</li>
           <li><b>System Command:</b> Double-click to type a command (e.g., 'notepad', 'calc').</li>
           <li><b>Delay:</b> Double-click to set duration in seconds.</li>
           </ul>
        </p>
        <p><b>4. Control:</b> Right-click a node or wire to delete it.</p>
        <p><b>5. Run:</b> Click 'Apply', then say <b>"Run Workflow"</b>.</p>
        """
        QMessageBox.information(self, "Neural Sync Help", msg)

    def save_workflow(self):
        import uuid
        
        # 1. Collect Nodes
        nodes_data = []
        node_map = {} # item -> uuid
        
        for item in self.scene.items():
            from .automation_window import NodeItem # Avoid circular import if needed
            if isinstance(item, NodeItem):
                node_id = str(uuid.uuid4())
                node_map[item] = node_id
                
                nodes_data.append({
                    "id": node_id,
                    "type": item.text,
                    "x": item.pos().x(),
                    "y": item.pos().y(),
                    "data": item.properties
                })
        
        # 2. Collect Connections
        connections_data = []
        for item in self.scene.items():
            from .automation_window import ConnectionPath
            if isinstance(item, ConnectionPath):
                if item.start_port and item.end_port:
                    start_node = item.start_port.parent_node
                    end_node = item.end_port.parent_node
                    
                    if start_node in node_map and end_node in node_map:
                        connections_data.append({
                            "from": node_map[start_node],
                            "to": node_map[end_node]
                        })
        
        workflow = {
            "nodes": nodes_data,
            "connections": connections_data
        }
        
        # 3. Save to File
        try:
            import json, os
            data_dir = os.path.join(os.getcwd(), 'data')
            if not os.path.exists(data_dir): os.makedirs(data_dir)
            
            file_path = os.path.join(data_dir, 'workflow.json')
            with open(file_path, 'w') as f:
                json.dump(workflow, f, indent=4)
                
            print(f"[Automation] Workflow saved to {file_path}")
            # Placeholder: Notify Engine
            
        except Exception as e:
            print(f"[Automation] Error saving: {e}")
