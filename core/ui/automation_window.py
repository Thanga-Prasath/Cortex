from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFrame, QSplitter, QListWidget,
                             QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsPathItem,
                             QInputDialog, QMenu, QMessageBox, QComboBox, QDialog)
from PyQt6.QtCore import Qt, QRectF, QPointF, QMimeData
from PyQt6.QtGui import QBrush, QPen, QColor, QPainter, QPainterPath, QDrag, QPainterPathStroker
from .styles import get_stylesheet, THEME_COLORS
import os
import json

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

class ZoomableView(QGraphicsView):
    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            zoom_in = event.angleDelta().y() > 0
            factor = 1.15 if zoom_in else 1 / 1.15
            self.scale(factor, factor)
            event.accept()
        else:
            super().wheelEvent(event)

# --- 4. Flow View (Interaction Manager) ---
class FlowView(ZoomableView):
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
        
        # Determine Automation Directory and State
        self.data_dir = os.path.join(os.getcwd(), 'data', 'automations')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self.state_file = os.path.join(self.data_dir, 'state.json')
        self.current_workflow = "Default"
        self.primary_workflow = "Default"
        
        # Migrate old workflow if it exists
        old_wf = os.path.join(os.getcwd(), 'data', 'workflow.json')
        if os.path.exists(old_wf):
            import shutil
            shutil.move(old_wf, os.path.join(self.data_dir, 'Default.json'))
            
        # Top Bar for Automation Management
        top_bar = QWidget()
        tb_layout = QHBoxLayout(top_bar)
        tb_layout.setContentsMargins(0, 0, 0, 0)
        
        self.combo_workflows = QComboBox()
        self.combo_workflows.setMinimumWidth(200)
        self.combo_workflows.currentTextChanged.connect(self.on_combo_changed)
        
        btn_new = QPushButton("+ New")
        btn_new.clicked.connect(self.on_new_clicked)
        
        self.btn_primary = QPushButton("Set as Primary")
        self.btn_primary.clicked.connect(self.on_primary_clicked)
        
        self.lbl_primary = QLabel("Primary: Default")
        self.lbl_primary.setStyleSheet("color: #888; font-style: italic;")
        
        tb_layout.addWidget(QLabel("Automations:"))
        tb_layout.addWidget(self.combo_workflows)
        tb_layout.addWidget(btn_new)
        tb_layout.addWidget(self.btn_primary)
        tb_layout.addStretch()
        tb_layout.addWidget(self.lbl_primary)
        
        layout.addWidget(top_bar)
        
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
        
        # Load and Initialize Workflows
        self.init_workflows()

    def init_workflows(self):
        import json, glob
        # Load State
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.primary_workflow = state.get("primary", "Default")
                    self.current_workflow = state.get("last_edited", "Default")
            except:
                pass
                
        # Populate Combobox
        self.combo_workflows.blockSignals(True)
        self.combo_workflows.clear()
        
        json_files = glob.glob(os.path.join(self.data_dir, "*.json"))
        for f in json_files:
            name = os.path.basename(f).replace(".json", "")
            if name != "state":
                self.combo_workflows.addItem(name)
                
        # Add Default if empty
        if self.combo_workflows.count() == 0:
            self.combo_workflows.addItem("Default")
            
        # Select Last Edited
        idx = self.combo_workflows.findText(self.current_workflow)
        if idx >= 0:
            self.combo_workflows.setCurrentIndex(idx)
        else:
            self.current_workflow = self.combo_workflows.itemText(0)
            self.combo_workflows.setCurrentIndex(0)
            
        self.combo_workflows.blockSignals(False)
        
        self.update_primary_label()
        self.load_workflow(self.current_workflow)
        
    def update_primary_label(self):
        self.lbl_primary.setText(f"Primary: {self.primary_workflow}")
        
    def save_state(self):
        import json
        state = {
            "primary": self.primary_workflow,
            "last_edited": self.current_workflow
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=4)
            
    def on_combo_changed(self, text):
        if not text: return
        # Auto-save current before switching
        self.save_workflow()
        self.current_workflow = text
        self.save_state()
        self.load_workflow(self.current_workflow)
        
    def on_new_clicked(self):
        text, ok = QInputDialog.getText(self, "New Automation", "Enter automation name:")
        if ok and text.strip():
            name = text.strip()
            # Prevent 'state' keyword
            if name.lower() == "state":
                QMessageBox.warning(self, "Invalid Name", "'state' is a reserved name.")
                return
                
            file_path = os.path.join(self.data_dir, f"{name}.json")
            if os.path.exists(file_path):
                QMessageBox.warning(self, "Exists", "An automation with this name already exists.")
                return
                
            import json
            with open(file_path, 'w') as f:
                json.dump({"nodes": [], "connections": []}, f)
                
            self.combo_workflows.blockSignals(True)
            self.combo_workflows.addItem(name)
            self.combo_workflows.setCurrentText(name)
            self.combo_workflows.blockSignals(False)
            
            self.current_workflow = name
            self.save_state()
            self.load_workflow(name)
            
    def on_primary_clicked(self):
        self.primary_workflow = self.current_workflow
        self.save_state()
        self.update_primary_label()
        # Notify the UI process so open AutomationListDialog can refresh in real-time
        try:
            # Import through parent window reference if needed
            from multiprocessing import current_process
            if hasattr(self, '_status_queue') and self._status_queue:
                self._status_queue.put(("PRIMARY_UPDATED", self.primary_workflow))
        except: pass
        QMessageBox.information(self, "Primary Set", f"'{self.primary_workflow}' is now the primary automation.")

    def load_workflow(self, name=None):
        import json, os
        if not name:
            name = self.current_workflow
            
        file_path = os.path.join(self.data_dir, f"{name}.json")
        
        # Clear existing scene
        self.scene.clear()
        
        if not os.path.exists(file_path):
            return
            
        try:
            with open(file_path, 'r') as f:
                workflow = json.load(f)
                
            nodes_data = workflow.get("nodes", [])
            connections_data = workflow.get("connections", [])
            
            node_map = {} # uuid -> NodeItem
            
            # 1. Create Nodes
            for n_data in nodes_data:
                node_id = n_data.get("id")
                n_type = n_data.get("type", "Start")
                x = n_data.get("x", 0)
                y = n_data.get("y", 0)
                data = n_data.get("data", {})
                
                node = NodeItem(n_type, x, y)
                node.properties = data
                self.scene.addItem(node)
                node_map[node_id] = node
                
            # 2. Create Connections
            for c_data in connections_data:
                from_id = c_data.get("from")
                to_id = c_data.get("to")
                
                start_node = node_map.get(from_id)
                end_node = node_map.get(to_id)
                
                if start_node and end_node and start_node.out_port and end_node.in_port:
                    conn = ConnectionPath(start_node.out_port, end_node.in_port)
                    self.scene.addItem(conn)
                    
            print(f"[Automation] Loaded workflow from {file_path}")
        except Exception as e:
            print(f"[Automation] Error loading workflow: {e}")

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
            
            file_path = os.path.join(self.data_dir, f"{self.current_workflow}.json")
            with open(file_path, 'w') as f:
                json.dump(workflow, f, indent=4)
                
            print(f"[Automation] Workflow saved to {file_path}")
            # Placeholder: Notify Engine
            
        except Exception as e:
            print(f"[Automation] Error saving: {e}")

class AutomationListDialog(QDialog):
    """
    Compact automation list. Right panel appears only when an item is clicked.
    The right panel is independently closable. Editing happens inline â€” no dialog close needed.
    """

    COMPACT_W  = 340
    EXPANDED_W = 860
    HEIGHT     = 520

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neural Sync: Automation Manager")
        self.resize(self.COMPACT_W, self.HEIGHT)
        self.setMinimumSize(self.COMPACT_W, self.HEIGHT)
        # Removed WindowStaysOnTopHint so it behaves as a normal window

        # â”€â”€ Theming â”€â”€
        try:
            config_path = os.path.join(os.getcwd(), 'data', 'user_config.json')
            with open(config_path, 'r') as f:
                theme = json.load(f).get("theme", "Neon Green")
        except: theme = "Neon Green"
        self.setStyleSheet(get_stylesheet(theme))
        self.accent  = THEME_COLORS.get(theme, "#39FF14")
        self.data_dir   = os.path.join(os.getcwd(), 'data', 'automations')
        self.state_file = os.path.join(self.data_dir, 'state.json')
        self.current_primary = None
        self.selected_name   = None
        self._edit_mode      = False          # track if inline editor is active
        self._edit_scene     = None
        self._edit_view      = None

        # â”€â”€ Root horizontal layout â”€â”€
        root_h = QHBoxLayout(self)
        root_h.setContentsMargins(0, 0, 0, 0)
        root_h.setSpacing(0)

        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        # LEFT COLUMN  (always visible)
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        left_col = QWidget()
        left_col.setMinimumWidth(self.COMPACT_W)
        left_col.setStyleSheet("background: #111;")
        lc_layout = QVBoxLayout(left_col)
        lc_layout.setContentsMargins(12, 12, 12, 12)

        # Title
        title = QLabel("Your Automations")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding-bottom: 4px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lc_layout.addWidget(title)

        # Hint
        hint = QLabel("Click to preview  Â·  Double-click to rename")
        hint.setStyleSheet("color: #555; font-size: 10px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lc_layout.addWidget(hint)

        # List
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background: #181818;
                border: 1px solid {self.accent}55;
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }}
            QListWidget::item {{ border-bottom: 1px solid #252525; }}
            QListWidget::item:selected {{
                background: {self.accent}18;
                border-left: 3px solid {self.accent};
            }}
            QListWidget::item:hover {{ background: {self.accent}0d; }}
        """)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self.on_rename)
        lc_layout.addWidget(self.list_widget, stretch=1)

        # Close dialog button
        btn_close = QPushButton("Close Window")
        btn_close.setStyleSheet("margin-top: 8px;")
        btn_close.clicked.connect(self.accept)
        lc_layout.addWidget(btn_close)

        root_h.addWidget(left_col, stretch=0)

        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        # RIGHT PANEL  (hidden by default)
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        self.right_panel = QWidget()
        self.right_panel.setMinimumWidth(self.EXPANDED_W - self.COMPACT_W)
        self.right_panel.setStyleSheet(f"background: #141414; border-left: 1px solid {self.accent}44;")
        self.right_panel.setVisible(False)
        rp_layout = QVBoxLayout(self.right_panel)
        rp_layout.setContentsMargins(12, 10, 12, 12)
        rp_layout.setSpacing(6)

        # Top bar: name + x close
        top_bar = QHBoxLayout()
        self.lbl_right_name = QLabel("")
        self.lbl_right_name.setStyleSheet("font-size: 15px; font-weight: bold;")
        top_bar.addWidget(self.lbl_right_name, stretch=1)

        btn_close_panel = QPushButton("✕")
        btn_close_panel.setFixedSize(26, 26)
        btn_close_panel.setToolTip("Close preview")
        btn_close_panel.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: #777; font-size: 14px; border: none; border-radius: 13px; }}
            QPushButton:hover {{ background: #ff444433; color: #ff4444; }}
        """)
        btn_close_panel.clicked.connect(self.close_right_panel)
        top_bar.addWidget(btn_close_panel)
        rp_layout.addLayout(top_bar)

        # â”€â”€ Preview / Editor area (stacked) â”€â”€
        # Preview scene (read-only)
        self.preview_scene = QGraphicsScene()
        self.preview_view  = ZoomableView(self.preview_scene)
        self.preview_view.setStyleSheet("background: #0e0e0e; border: 1px solid #232323; border-radius: 6px;")
        self.preview_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.preview_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        rp_layout.addWidget(self.preview_view, stretch=1)

        # Inline editor (FlowView â€” hidden until Edit is clicked)
        self._edit_scene = QGraphicsScene()
        self._edit_scene.setSceneRect(0, 0, 5000, 5000)
        self._edit_view  = FlowView(self._edit_scene)
        self._edit_view.setStyleSheet("background: #0e0e0e; border: 1px solid #232323; border-radius: 6px;")
        self._edit_view.setVisible(False)
        rp_layout.addWidget(self._edit_view, stretch=1)

        # Action buttons row
        actions = QHBoxLayout()
        actions.setSpacing(6)

        self.btn_run = QPushButton("▶  Run")
        self.btn_run.setEnabled(False)
        self.btn_run.setStyleSheet(
            f"QPushButton {{ color:{self.accent}; border:1px solid {self.accent}; }}"
            f"QPushButton:enabled:hover {{ background:{self.accent}; color:black; }}"
        )
        self.btn_run.clicked.connect(self.on_run_selected)

        self.btn_set_primary = QPushButton("★ Set as Primary")
        self.btn_set_primary.setEnabled(False)
        self.btn_set_primary.clicked.connect(self.on_set_primary)

        self.btn_edit = QPushButton("Edit")
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self.on_toggle_edit)

        self.btn_save = QPushButton("Save")
        self.btn_save.setVisible(False)
        self.btn_save.clicked.connect(self.on_save_inline)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setEnabled(False)
        self.btn_delete.setStyleSheet(
            "QPushButton { color:#ff5555; border:1px solid #ff5555; }"
            "QPushButton:enabled:hover { background:#ff5555; color:black; }"
        )
        self.btn_delete.clicked.connect(self.on_delete)

        actions.addWidget(self.btn_run)
        actions.addWidget(self.btn_set_primary)
        actions.addWidget(self.btn_edit)
        actions.addWidget(self.btn_save)
        actions.addStretch()
        actions.addWidget(self.btn_delete)
        rp_layout.addLayout(actions)

        root_h.addWidget(self.right_panel, stretch=1)

        # Load list
        self.load_data()

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # Panel show / hide
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    def _show_right_panel(self):
        if not self.right_panel.isVisible():
            self.right_panel.setVisible(True)
            self.resize(self.EXPANDED_W, self.height())

    def close_right_panel(self):
        self._exit_edit_mode()
        self.right_panel.setVisible(False)
        self.resize(self.COMPACT_W, self.height())
        self.list_widget.clearSelection()
        self.selected_name = None

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # Data helpers
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except: pass
        return {}

    def _save_state(self, state):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=4)

    def _sorted_names(self, primary=None):
        import glob
        json_files = glob.glob(os.path.join(self.data_dir, "*.json"))
        names = [os.path.basename(f).replace(".json", "") for f in json_files
                 if os.path.basename(f) != "state.json"]
        names.sort()
        if primary and primary in names:
            names.remove(primary)
            names.insert(0, primary)
        return names

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # List population
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    def load_data(self):
        state = self._load_state()
        self.current_primary = state.get("primary", None)
        self.list_widget.clear()

        from PyQt6.QtWidgets import QListWidgetItem
        for serial, name in enumerate(self._sorted_names(self.current_primary), start=1):
            item = QListWidgetItem(self.list_widget)
            item.setData(Qt.ItemDataRole.UserRole, name)

            row = QWidget()
            row.setStyleSheet("background: transparent;")
            h = QHBoxLayout(row)
            h.setContentsMargins(6, 7, 6, 7)
            h.setSpacing(6)

            num = QLabel(f"{serial}.")
            num.setStyleSheet("color:#555; font-size:12px; min-width:18px;")
            h.addWidget(num)

            lbl = QLabel(name)
            lbl.setStyleSheet("color:#ddd; font-size:13px;")
            h.addWidget(lbl, stretch=1)

            if name == self.current_primary:
                badge = QLabel("Primary")
                badge.setStyleSheet(
                    f"color:{self.accent}; font-size:10px; border:1px solid {self.accent};"
                    f" padding:1px 5px; border-radius:3px;"
                )
                h.addWidget(badge)

            item.setSizeHint(row.sizeHint())
            self.list_widget.setItemWidget(item, row)

    def refresh_list(self):
        self.load_data()
        if self.selected_name:
            for i in range(self.list_widget.count()):
                it = self.list_widget.item(i)
                if it and it.data(Qt.ItemDataRole.UserRole) == self.selected_name:
                    self.list_widget.setCurrentItem(it)
                    break

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # Selection & preview
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    def on_item_clicked(self, item):
        if not item: return

        name = item.data(Qt.ItemDataRole.UserRole)
        # If clicking the currently selected item while the panel is open, close it
        if self.selected_name == name and self.right_panel.isVisible():
            self.close_right_panel()
            return

        self.selected_name = name
        self.lbl_right_name.setText(name)

        self.btn_set_primary.setEnabled(name != self.current_primary)
        self.btn_run.setEnabled(True)
        self.btn_edit.setEnabled(True)
        self.btn_delete.setEnabled(True)

        # Exit edit mode for previous selection before showing preview
        self._exit_edit_mode()
        self._load_preview(name)
        self._show_right_panel()

    def on_run_selected(self):
        """Run the currently selected automation immediately (non-blocking)."""
        if not self.selected_name:
            return
        import threading
        from core.engines.automation import AutomationEngine

        # Use a lightweight stub speaker — the real TTS process belongs to the engine
        # process. Spawning a full Speaker() here would start a second TTS worker.
        class _StubSpeaker:
            def speak(self, text, **_):
                print(f"[Automation Run] {text}")

        def _run():
            try:
                engine = AutomationEngine(speaker=_StubSpeaker())
                engine.execute_workflow(workflow_name=self.selected_name)
            except Exception as e:
                print(f"[AutomationListDialog] Run error: {e}")

        threading.Thread(target=_run, daemon=True).start()

    def _load_preview(self, name):
        self.preview_scene.clear()
        wf_path = os.path.join(self.data_dir, f"{name}.json")
        if not os.path.exists(wf_path): return
        try:
            with open(wf_path, 'r') as f:
                data = json.load(f)
        except: return

        from PyQt6.QtGui import QBrush, QPen, QColor
        NODE_COLORS = {
            "Start": "#39FF14", "End": "#FF4444",
            "Speak": "#00BFFF", "Delay": "#FFD700",
            "System Command": "#FF8C00",
        }
        node_bottoms = {}
        for node in data.get("nodes", []):
            x, y   = node.get("x", 0), node.get("y", 0)
            ntype  = node.get("type", "")
            color  = NODE_COLORS.get(ntype, "#888")
            self.preview_scene.addRect(x, y, 160, 58,
                QPen(QColor(color), 2), QBrush(QColor(color + "22")))
            t = self.preview_scene.addText(ntype)
            t.setDefaultTextColor(QColor(color))
            t.setPos(x + 6, y + 6)
            props  = node.get("properties", {})
            detail = props.get("text") or props.get("duration") or props.get("command") or ""
            if detail:
                s = self.preview_scene.addText(str(detail)[:22])
                s.setDefaultTextColor(QColor("#999"))
                s.setPos(x + 6, y + 30)
            node_bottoms[node["id"]] = (x + 80, y + 58)

        for conn in data.get("connections", []):
            src = node_bottoms.get(conn.get("from"))
            dst = node_bottoms.get(conn.get("to"))
            if src and dst:
                p = QPainterPath()
                p.moveTo(*src)
                p.lineTo(dst[0], dst[1] - 58)
                self.preview_scene.addPath(p, QPen(QColor(self.accent), 1.5))

        self.preview_view.fitInView(
            self.preview_scene.itemsBoundingRect(),
            Qt.AspectRatioMode.KeepAspectRatio
        )

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # Inline editing
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    def on_toggle_edit(self):
        if self._edit_mode:
            self._exit_edit_mode()
        else:
            self._enter_edit_mode()

    def _enter_edit_mode(self):
        """Switch right panel from read-only preview to interactive FlowView."""
        if not self.selected_name: return
        self._edit_mode = True
        self.btn_edit.setText("Cancel Edit")
        self.btn_save.setVisible(True)

        # Load workflow into edit scene (reusing AutomationWindow's load logic)
        self._edit_scene.clear()
        wf_path = os.path.join(self.data_dir, f"{self.selected_name}.json")
        if os.path.exists(wf_path):
            try:
                with open(wf_path, 'r') as f:
                    data = json.load(f)
                node_map = {}
                for nd in data.get("nodes", []):
                    n_type = nd.get("type", "Start")
                    x = nd.get("x", 0)
                    y = nd.get("y", 0)
                    props = nd.get("data", {})
                    
                    node_item = NodeItem(n_type, x, y)
                    node_item.properties = props
                    self._edit_scene.addItem(node_item)
                    node_map[nd["id"]] = node_item
                for conn in data.get("connections", []):
                    src = node_map.get(conn["from"])
                    dst = node_map.get(conn["to"])
                    if src and dst and src.out_port and dst.in_port:
                        cp = ConnectionPath(src.out_port, dst.in_port)
                        self._edit_scene.addItem(cp)
            except Exception as e:
                print(f"[Inline Edit] Load error: {e}")

        self.preview_view.setVisible(False)
        self._edit_view.setVisible(True)

    def _exit_edit_mode(self):
        """Return to preview mode without saving."""
        self._edit_mode = False
        self.btn_edit.setText("Edit")
        self.btn_save.setVisible(False)
        self._edit_view.setVisible(False)
        self.preview_view.setVisible(True)

    def on_save_inline(self):
        """Serialize the inline edit scene and save to disk."""
        if not self.selected_name: return
        import uuid
        nodes_data, connections_data = [], []
        node_map = {}
        for item in self._edit_scene.items():
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
        # Build edges from ConnectionPath items
        for item in self._edit_scene.items():
            if isinstance(item, ConnectionPath):
                if item.start_port and item.end_port:
                    src_node = item.start_port.parent_node
                    dst_node = item.end_port.parent_node
                    if src_node in node_map and dst_node in node_map:
                        connections_data.append({
                            "from": node_map[src_node],
                            "to": node_map[dst_node]
                        })

        wf = {"nodes": nodes_data, "connections": connections_data}
        try:
            with open(os.path.join(self.data_dir, f"{self.selected_name}.json"), 'w') as f:
                json.dump(wf, f, indent=4)
            print(f"[Inline Edit] Saved: {self.selected_name}")
        except Exception as e:
            print(f"[Inline Edit] Save error: {e}")

        # Refresh preview
        self._exit_edit_mode()
        self._load_preview(self.selected_name)

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # Actions
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    def on_set_primary(self):
        if not self.selected_name: return
        state = self._load_state()
        state['primary'] = self.selected_name
        self._save_state(state)
        self.current_primary = self.selected_name
        self.refresh_list()
        self.btn_set_primary.setEnabled(False)

    def on_delete(self):
        if not self.selected_name: return
        from PyQt6.QtWidgets import QMessageBox
        if QMessageBox.question(
            self, "Delete", f"Delete '{self.selected_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes: return

        try: os.remove(os.path.join(self.data_dir, f"{self.selected_name}.json"))
        except Exception as e: print(f"[Manager] Delete error: {e}")

        state = self._load_state()
        for k in ('primary', 'last_edited'):
            if state.get(k) == self.selected_name: state.pop(k, None)
        self._save_state(state)
        self.close_right_panel()
        self.load_data()

    def on_rename(self, item):
        if not item: return
        name = item.data(Qt.ItemDataRole.UserRole)
        from PyQt6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(
            self, "Rename", "New name:", text=name)
        if not ok or not new_name.strip() or new_name.strip() == name: return
        new_name = new_name.strip()

        new_path = os.path.join(self.data_dir, f"{new_name}.json")
        if os.path.exists(new_path):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Name Taken",
                f"'{new_name}' already exists.")
            return
        try:
            os.rename(os.path.join(self.data_dir, f"{name}.json"), new_path)
        except Exception as e:
            print(f"[Manager] Rename error: {e}"); return

        state = self._load_state()
        for k in ('primary', 'last_edited'):
            if state.get(k) == name: state[k] = new_name
        self._save_state(state)

        if self.current_primary == name: self.current_primary = new_name
        if self.selected_name   == name:
            self.selected_name = new_name
            self.lbl_right_name.setText(new_name)
        self.load_data()

        # â”€â”€ Data helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except: pass
        return {}

    def _save_state(self, state):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=4)

    def _sorted_names(self, primary=None):
        import glob
        json_files = glob.glob(os.path.join(self.data_dir, "*.json"))
        names = [os.path.basename(f).replace(".json", "") for f in json_files
                 if os.path.basename(f) != "state.json"]
        names.sort()
        if primary and primary in names:
            names.remove(primary)
            names.insert(0, primary)
        return names

    # â”€â”€ List population â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def load_data(self):
        state = self._load_state()
        self.current_primary = state.get("primary", None)
        self.list_widget.clear()

        names = self._sorted_names(self.current_primary)
        from PyQt6.QtWidgets import QListWidgetItem
        for serial, name in enumerate(names, start=1):
            item = QListWidgetItem(self.list_widget)
            item.setData(Qt.ItemDataRole.UserRole, name)

            widget = QWidget()
            widget.setStyleSheet("background: transparent;")
            h = QHBoxLayout(widget)
            h.setContentsMargins(8, 8, 8, 8)

            # Serial number
            lbl_num = QLabel(f"{serial}.")
            lbl_num.setStyleSheet("color: #666; font-size: 13px; min-width: 22px;")
            h.addWidget(lbl_num)

            # Automation name
            lbl_name = QLabel(name)
            lbl_name.setProperty("is_name_label", True)
            lbl_name.setStyleSheet("color: #fff; font-size: 14px;")
            h.addWidget(lbl_name, stretch=1)

            # Primary badge
            if name == self.current_primary:
                lbl_p = QLabel("Primary")
                lbl_p.setProperty("is_badge", True)
                lbl_p.setStyleSheet(
                    f"color: {self.accent}; font-size: 11px; border: 1px solid {self.accent};"
                    f" padding: 2px 6px; border-radius: 4px;"
                )
                h.addWidget(lbl_p, alignment=Qt.AlignmentFlag.AlignRight)

            item.setSizeHint(widget.sizeHint())
            self.list_widget.setItemWidget(item, widget)

    # (refresh_list and all action methods live in the new class above)
