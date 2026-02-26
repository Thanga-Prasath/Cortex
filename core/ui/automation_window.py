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
    def __init__(self, parent, port_type="out", tag=None):
        super().__init__(parent)
        self.parent_node = parent
        self.port_type = port_type # 'in' or 'out'
        self.tag = tag # 'true' or 'false'
        self.radius = 6
        self.connections = []
        self.color = QColor("#fff")
        if tag == "true": self.color = QColor("#39FF14")
        elif tag == "false": self.color = QColor("#FF3131")

        self.setAcceptHoverEvents(True)
        
        # Default positions (will be overridden by parent if special)
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
        painter.setPen(QPen(QColor(0,0,0,100), 1))
        painter.setBrush(self.color)
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
        elif text == "Press Hotkey":
            self.properties["value"] = "ctrl, c"
        elif text == "Type Text":
            self.properties["value"] = "Hello World"
        elif text == "Notify":
            self.properties["value"] = "Automation complete"
        elif text == "Play Sound":
            self.properties["value"] = "beep"
        elif text == "Open Target":
            self.properties["value"] = "notepad"
            
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
        self.out_true = None
        self.out_false = None
        
        if text != "Start":
            self.in_port = PortItem(self, "in")
        
        if text == "If Condition":
            # Diamond shape ports
            self.properties["condition_type"] = "App is Running"
            self.properties["value"] = ""
            if self.in_port: self.in_port.setPos(75, 0) # Top
            self.out_true = PortItem(self, "out", tag="true")
            self.out_true.setPos(0, 40) # Left
            self.out_false = PortItem(self, "out", tag="false")
            self.out_false.setPos(150, 40) # Right
        elif text != "End":
            self.out_port = PortItem(self, "out")

    def mouseDoubleClickEvent(self, event):
        if self.text == "If Condition":
            dlg = ConditionDialog(
                current_type=self.properties.get("condition_type", "App is Running"),
                current_value=self.properties.get("value", "")
            )
            if dlg.exec():
                self.properties["condition_type"] = dlg.target_type
                self.properties["value"] = dlg.target_value
                self.update()
            super().mouseDoubleClickEvent(event)
            return

        # Open Target has a special picker dialog
        if self.text == "Open Target":
            exclude = set()
            try:
                scene = self.scene()
                if scene:
                    for view in scene.views():
                        win = view.window()
                        if hasattr(win, 'current_workflow') and win.current_workflow:
                            exclude.add(win.current_workflow)
                            break
            except Exception:
                pass
            dlg = TargetPickerDialog(
                current_value=self.properties.get("value", ""),
                exclude_names=exclude
            )
            if dlg.exec():
                self.properties["value"] = dlg.selected_path
                self.update()
            super().mouseDoubleClickEvent(event)
            return

        # All other editable nodes use a simple text prompt
        editable_nodes = ["Speak", "System Command", "Delay", "Press Hotkey", "Type Text", "Notify", "Play Sound"]
        if self.text in editable_nodes:
            prompt = f"Enter {self.text} value:"
            val, ok = QInputDialog.getText(None, "Node Properties", prompt, text=self.properties.get("value", ""))
            if ok:
                self.properties["value"] = val
                self.update()
        super().mouseDoubleClickEvent(event)

    def boundingRect(self):
        if self.text == "If Condition":
            return QRectF(0, 0, 150, 80)
        return QRectF(0, 0, 150, 60)
        
    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Shadow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 50))
        if self.text == "If Condition":
            path = QPainterPath()
            path.moveTo(75, 0)
            path.lineTo(150, 40)
            path.lineTo(75, 80)
            path.lineTo(0, 40)
            path.closeSubpath()
            painter.drawPath(path.translated(2, 2))
        else:
            painter.drawRoundedRect(rect.adjusted(2, 2, 2, 2), 8, 8)
        
        # Body
        painter.setPen(QPen(self.color, 2))
        painter.setBrush(QColor(30, 30, 30, 220))
        
        if self.text == "If Condition":
            path = QPainterPath()
            path.moveTo(75, 0)
            path.lineTo(150, 40)
            path.lineTo(75, 80)
            path.lineTo(0, 40)
            path.closeSubpath()
            painter.drawPath(path)
            
            # Label in center
            painter.setPen(self.color)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "IF")
        else:
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
            y_off = 25 if self.text != "If Condition" else 45
            painter.drawText(QRectF(10, y_off, 130, 30), Qt.AlignmentFlag.AlignCenter, 
                             self.properties["value"])
        
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
             if self.in_port: self.in_port.update_connections()
             if self.out_port: self.out_port.update_connections()
             if self.out_true: self.out_true.update_connections()
             if self.out_false: self.out_false.update_connections()
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
        if node.out_true:
            for c in list(node.out_true.connections): self._delete_connection(c)
        if node.out_false:
            for c in list(node.out_false.connections): self._delete_connection(c)
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
        
        btn_rename = QPushButton("✎ Rename")
        btn_rename.clicked.connect(self.on_rename_clicked)
        
        self.btn_primary = QPushButton("Set as Primary")
        self.btn_primary.clicked.connect(self.on_primary_clicked)
        
        self.lbl_primary = QLabel("Primary: Default")
        self.lbl_primary.setStyleSheet("color: #888; font-style: italic;")
        
        tb_layout.addWidget(QLabel("Automations:"))
        tb_layout.addWidget(self.combo_workflows)
        tb_layout.addWidget(btn_new)
        tb_layout.addWidget(btn_rename)
        tb_layout.addWidget(self.btn_primary)
        tb_layout.addStretch()
        tb_layout.addWidget(self.lbl_primary)
        
        layout.addWidget(top_bar)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Toolbox
        tools = NodeList() # Using our custom NodeList
        tools.addItems(["Start", "Delay", "Speak", "System Command", "Press Hotkey", "Type Text", "Notify", "Play Sound", "Open Target", "If Condition", "End"])
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
        
        self.btn_apply = QPushButton("Apply Workflow")
        self.btn_apply.clicked.connect(self.save_workflow)
        
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

        self.lbl_validation = QLabel("")
        self.lbl_validation.setStyleSheet("color: #FF4444; font-weight: bold; font-size: 11px;")
        
        f_layout.addWidget(self.btn_apply)
        f_layout.addWidget(self.lbl_validation)
        f_layout.addStretch()
        f_layout.addWidget(btn_help)
        
        layout.addWidget(footer)
        
        # Load and Initialize Workflows
        self.init_workflows()
        # Re-validate the canvas whenever nodes are added/removed
        self.scene.changed.connect(self._on_scene_changed)

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

    def on_rename_clicked(self):
        old_name = self.current_workflow
        new_name, ok = QInputDialog.getText(self, "Rename Automation", "New name:", text=old_name)
        if not ok or not new_name.strip():
            return
        new_name = new_name.strip()
        if new_name.lower() == "state":
            QMessageBox.warning(self, "Invalid Name", "'state' is a reserved name.")
            return
        if new_name == old_name:
            return
        old_path = os.path.join(self.data_dir, f"{old_name}.json")
        new_path = os.path.join(self.data_dir, f"{new_name}.json")
        if os.path.exists(new_path):
            QMessageBox.warning(self, "Exists", f"An automation named '{new_name}' already exists.")
            return
        try:
            os.rename(old_path, new_path)
        except Exception as e:
            QMessageBox.critical(self, "Rename Failed", str(e))
            return
        # Update primary if needed
        if self.primary_workflow == old_name:
            self.primary_workflow = new_name
        # Update combobox without triggering a save of the old (now gone) file
        self.combo_workflows.blockSignals(True)
        idx = self.combo_workflows.findText(old_name)
        if idx >= 0:
            self.combo_workflows.setItemText(idx, new_name)
        self.combo_workflows.setCurrentText(new_name)
        self.combo_workflows.blockSignals(False)
        self.current_workflow = new_name
        self.save_state()
        self.update_primary_label()

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
                
                if start_node and end_node and end_node.in_port:
                    port = None
                    p_tag = c_data.get("from_port")
                    if p_tag == "true": port = start_node.out_true
                    elif p_tag == "false": port = start_node.out_false
                    else: port = start_node.out_port
                    
                    if port:
                        conn = ConnectionPath(port, end_node.in_port)
                        self.scene.addItem(conn)
                    
            print(f"[Automation] Loaded workflow from {file_path}")
        except Exception as e:
            print(f"[Automation] Error loading workflow: {e}")

    def show_help(self):
        msg = """
        <h2 style='color: #00FFFF;'>Cortex Automation help</h2>
        <p>Build powerful workflows by dragging nodes from the sidebar and connecting them.</p>
        
        <h3 style='color: #39FF14;'>Node Guide:</h3>
        <table border='0' cellpadding='5' cellspacing='0' style='color: #ccc; font-size: 13px;'>
          <tr><td><b>Start / End</b></td><td>The beginning and finale of your automation.</td></tr>
          <tr><td><b>Delay</b></td><td>Wait for X seconds before the next step.</td></tr>
          <tr><td><b>Speak</b></td><td>Cortex will announce your message via TTS.</td></tr>
          <tr><td><b>System Command</b></td><td>Runs a terminal command (use with caution).</td></tr>
          <tr><td><b>Press Hotkey</b></td><td>Simulates keyboard shortcut (e.g. <i>ctrl, c</i>).</td></tr>
          <tr><td><b>Type Text</b></td><td>Types out text as if you were typing on the keyboard.</td></tr>
          <tr><td><b>Notify</b></td><td>Shows a desktop notification window.</td></tr>
          <tr><td><b>Play Sound</b></td><td>Plays a .wav file or a default 'beep'.</td></tr>
          <tr><td><b>Open Target</b></td><td>Opens an app, file, or runs ANOTHER automation.</td></tr>
          <tr><td><b style='color: #39FF14;'>If Condition</b></td><td><b>The Diamond Node.</b> Evaluates a condition.
              <ul>
                <li><b>Green Port (Left)</b>: Executed if the condition is TRUE.</li>
                <li><b>Red Port (Right)</b>: Executed if the condition is FALSE.</li>
              </ul>
          </td></tr>
        </table>

        <h3 style='color: #39FF14;'>Condition Types:</h3>
        <ul style='color: #ccc; font-size: 12px;'>
          <li><b>App is Running</b>: True if the process name is active.</li>
          <li><b>File or Folder Exists</b>: True if the path is found on disk.</li>
          <li><b>Time of Day</b>: True if current time is after the specified HH:MM.</li>
          <li><b>Active Window</b>: True if the current focused window title matches.</li>
          <li><b>Text Area Active</b>: True if the mouse cursor is on a text input (I-Beam).</li>
        </ul>

        <p><b style='color: #FF3131;'>Pro Tip:</b> Right-click any node or wire to delete it instantly.</p>
        """
        QMessageBox.information(self, "Neural Sync Help", msg)

    def _on_scene_changed(self, _=None):
        """Called whenever the scene changes — re-runs live validation."""
        self.validate_canvas(save_blocked=False)

    def validate_canvas(self, save_blocked=True):
        """
        DFS from Start. Every possible output path must terminate at an End node.
        - Regular nodes: must have exactly one outgoing connection.
        - If Condition: must have BOTH 'true' and 'false' outgoing connections.
        Returns True if fully valid, False otherwise.
        """
        # Collect nodes and connections
        all_nodes = []
        conn_list = []  # (src_node, tag, dst_node)
        for item in self.scene.items():
            if isinstance(item, NodeItem):
                all_nodes.append(item)
            elif isinstance(item, ConnectionPath):
                if item.start_port and item.end_port:
                    conn_list.append((
                        item.start_port.parent_node,
                        item.start_port.tag,  # None, "true", or "false"
                        item.end_port.parent_node
                    ))

        def _set_error(msg):
            self.lbl_validation.setText(f"⚠ {msg}")
            self.btn_apply.setEnabled(False)
            self.btn_apply.setStyleSheet("background-color: #444; color: #777; border: 1px solid #555;")

        def _set_ok():
            self.lbl_validation.setText("")
            self.btn_apply.setEnabled(True)
            self.btn_apply.setStyleSheet("")

        # Check mandatory nodes exist
        types_present = {n.text for n in all_nodes}
        if "Start" not in types_present:
            _set_error("Missing START node"); return False
        if "End" not in types_present:
            _set_error("Missing END node"); return False

        # Build adjacency: node -> {tag: [dst_nodes]}
        adj = {n: {} for n in all_nodes}
        for (src, tag, dst) in conn_list:
            if src in adj:
                adj[src].setdefault(tag, []).append(dst)

        # DFS traversal
        start_node = next(n for n in all_nodes if n.text == "Start")
        open_issues = []

        def dfs(node, visited):
            if node in visited:
                return  # Cycle — skip, engine handles this
            visited = visited | {node}

            if node.text == "End":
                return  # ✅ Path closed

            if node.text == "If Condition":
                true_next  = adj.get(node, {}).get("true",  [])
                false_next = adj.get(node, {}).get("false", [])
                if not true_next:
                    open_issues.append("IF True (green) branch has no connection")
                else:
                    for n in true_next: dfs(n, visited)
                if not false_next:
                    open_issues.append("IF False (red) branch has no connection")
                else:
                    for n in false_next: dfs(n, visited)
            else:
                # Regular node — follow None-tagged outgoing wire
                next_nodes = adj.get(node, {}).get(None, [])
                if not next_nodes:
                    open_issues.append(f"'{node.text}' output is not connected")
                else:
                    for n in next_nodes: dfs(n, visited)

        dfs(start_node, set())

        if open_issues:
            unique = list(dict.fromkeys(open_issues))
            msg = unique[0]
            if len(unique) > 1:
                msg += f"  (+{len(unique)-1} more)"
            _set_error(msg)
            return False

        _set_ok()
        return True

    def save_workflow(self):
        import uuid
        
        # Validate before saving
        if not self.validate_canvas():
            return

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
        
        # Guard: never overwrite with an empty canvas
        if not nodes_data:
            return
        
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
                            "from_port": item.start_port.tag if item.start_port else None,
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


# ---------------------------------------------------------------------------
# Cross-platform Application Discovery
# ---------------------------------------------------------------------------
def get_installed_applications():
    """
    Returns a dict: { display_name: executable_path_or_command }
    Works on Windows, macOS, and Linux.
    """
    import platform, os, glob
    apps = {}
    sys_os = platform.system()

    if sys_os == "Windows":
        # ---- God Mode via PowerShell Get-StartApps ----
        # This returns ALL apps: classic EXEs, UWP (Settings, Store), and shortcuts
        try:
            import subprocess as _sp
            ps_cmd = (
                "Get-StartApps | ForEach-Object { $_.Name + '|' + $_.AppID } | "
                "Out-String -Width 4096"
            )
            result = _sp.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=15
            )
            for line in result.stdout.splitlines():
                line = line.strip()
                if "|" in line:
                    name, app_id = line.split("|", 1)
                    name, app_id = name.strip(), app_id.strip()
                    if name and app_id:
                        apps[name] = app_id  # app_id can be an AUMID or a path
        except Exception:
            pass

        # ---- Fallback: Classic Registry scan ----
        if not apps:
            import winreg, glob
            hives = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            ]
            for hive, subkey in hives:
                try:
                    with winreg.OpenKey(hive, subkey) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                with winreg.OpenKey(key, winreg.EnumKey(key, i)) as sub:
                                    name = winreg.QueryValueEx(sub, "DisplayName")[0]
                                    try:
                                        exe = winreg.QueryValueEx(sub, "DisplayIcon")[0].split(",")[0].strip('"')
                                    except:
                                        exe = ""
                                    if name and exe and os.path.exists(exe):
                                        apps[name] = exe
                            except:
                                pass
                except:
                    pass
            for sm in [
                os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
                os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs"),
            ]:
                for lnk in glob.glob(os.path.join(sm, "**", "*.lnk"), recursive=True):
                    name = os.path.splitext(os.path.basename(lnk))[0]
                    if name not in apps:
                        apps[name] = lnk


    elif sys_os == "Darwin":
        for d in ["/Applications", "/System/Applications", os.path.expanduser("~/Applications")]:
            for app in glob.glob(os.path.join(d, "*.app")):
                name = os.path.splitext(os.path.basename(app))[0]
                apps[name] = app

    else:  # Linux
        desktop_dirs = [
            "/usr/share/applications",
            "/usr/local/share/applications",
            os.path.expanduser("~/.local/share/applications"),
        ]
        for d in desktop_dirs:
            for desk in glob.glob(os.path.join(d, "*.desktop")):
                name, exe = "", ""
                try:
                    with open(desk, encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if line.startswith("Name=") and not name:
                                name = line.strip().split("=", 1)[1]
                            if line.startswith("Exec=") and not exe:
                                exe = line.strip().split("=", 1)[1].split()[0].replace("%U", "").replace("%F", "").strip()
                except:
                    pass
                if name and exe:
                    apps[name] = exe

    return dict(sorted(apps.items()))


# ---------------------------------------------------------------------------
# Condition Config Dialog
# ---------------------------------------------------------------------------
class ConditionDialog(QDialog):
    def __init__(self, parent=None, current_type="App is Running", current_value=""):
        super().__init__(parent)
        from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QPushButton, QLabel
        self.setWindowTitle("Configure If Condition")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Condition Type:"))
        self.combo_type = QComboBox()
        self.combo_type.addItems([
            "App is Running",
            "File or Folder Exists",
            "Time of Day (HH:MM)",
            "Active Window Title Contains",
            "Text Area is Active"
        ])
        self.combo_type.setCurrentText(current_type)
        layout.addWidget(self.combo_type)
        
        layout.addWidget(QLabel("Target Value:"))
        
        # Target Value layout
        val_layout = QHBoxLayout()
        self.edit_value = QLineEdit()
        self.edit_value.setText(current_value)
        self.edit_value.setPlaceholderText("e.g. spotify.exe, C:\\notes.txt, 18:00")
        val_layout.addWidget(self.edit_value)
        
        self.btn_browse = QPushButton("Browse")
        self.btn_browse.clicked.connect(self.on_browse)
        val_layout.addWidget(self.btn_browse)
        
        layout.addLayout(val_layout)
        
        self.hint = QLabel("Note: 'Text Area is Active' does not require a value.")
        self.hint.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.hint)
        
        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)
        
        self.target_type = current_type
        self.target_value = current_value
        
    def on_browse(self):
        import os
        ctype = self.combo_type.currentText()
        if ctype in ["App is Running", "File or Folder Exists"]:
            dlg = TargetPickerDialog(self, current_value=self.edit_value.text())
            if ctype == "App is Running":
                dlg.mode_combo.setCurrentText("Application")
            else:
                dlg.mode_combo.setCurrentText("File / Folder")
            if dlg.exec():
                path = dlg.selected_path
                if ctype == "App is Running" and ("\\" in path or "/" in path):
                    self.edit_value.setText(os.path.basename(path))
                else:
                    self.edit_value.setText(path)

        elif ctype == "Active Window Title Contains":
            # Show a live list of open window titles
            try:
                import pywinctl
                titles = [t for t in pywinctl.getAllTitles() if t.strip()]
            except Exception:
                titles = []

            if not titles:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "No Windows", "No open windows detected.")
                return

            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QLabel, QAbstractItemView
            picker = QDialog(self)
            picker.setWindowTitle("Select Active Window")
            picker.setMinimumSize(420, 300)
            pl = QVBoxLayout(picker)
            pl.addWidget(QLabel("Pick an open window title:"))
            lst = QListWidget()
            lst.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            for t in sorted(set(titles)):
                lst.addItem(t)
            pl.addWidget(lst)
            btn_pick = QPushButton("Select")
            btn_pick.clicked.connect(picker.accept)
            pl.addWidget(btn_pick)
            lst.itemDoubleClicked.connect(lambda: picker.accept())

            if picker.exec() and lst.currentItem():
                self.edit_value.setText(lst.currentItem().text())
                    
    def accept(self):
        self.target_type = self.combo_type.currentText()
        self.target_value = self.edit_value.text().strip()
        super().accept()

# ---------------------------------------------------------------------------
# Target Picker Dialog
# ---------------------------------------------------------------------------
class TargetPickerDialog(QDialog):
    """Dialog to select an Application or File for the Open Target node."""

    def __init__(self, parent=None, current_value="", exclude_names=None):
        super().__init__(parent)
        self._exclude_names = exclude_names or set()
        from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QComboBox,
                                     QLineEdit, QListWidget, QPushButton,
                                     QLabel, QFileDialog, QAbstractItemView)
        from PyQt6.QtCore import Qt
        self.setWindowTitle("Select Target")
        self.setMinimumSize(480, 420)
        self.selected_path = current_value
        self._apps = {}

        layout = QVBoxLayout(self)

        # Mode picker
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Open:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Application", "File / Folder", "Automation"])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.mode_combo)
        layout.addLayout(mode_row)

        # Search bar (shared for App and Automation modes)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self._filter_list)
        layout.addWidget(self.search_bar)

        # Shared list (used for App mode AND Automation mode)
        self.app_list = QListWidget()
        self.app_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.app_list.itemDoubleClicked.connect(self._accept_list_item)
        layout.addWidget(self.app_list)

        # File browse widget (hidden initially)
        self.file_row = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("Path to file or folder...")
        self.file_edit.setText(current_value if not current_value.startswith("automations://") else "")
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse_file)
        self.file_row.addWidget(self.file_edit)
        self.file_row.addWidget(btn_browse)
        layout.addLayout(self.file_row)

        # Buttons
        btn_row = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self._on_ok)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

        # Detect initial mode from existing value
        if current_value.startswith("automations://"):
            self.mode_combo.setCurrentIndex(2)
        else:
            self.mode_combo.setCurrentIndex(0)

        self._on_mode_changed(self.mode_combo.currentIndex())

    def _show_app_mode(self):
        self.search_bar.setVisible(True)
        self.app_list.setVisible(True)
        self._set_file_row_visible(False)

    def _show_file_mode(self):
        self.search_bar.setVisible(False)
        self.app_list.setVisible(False)
        self._set_file_row_visible(True)

    def _show_automation_mode(self):
        self.search_bar.setVisible(True)
        self.app_list.setVisible(True)
        self._set_file_row_visible(False)
        self._load_automations()

    def _set_file_row_visible(self, visible):
        for i in range(self.file_row.count()):
            w = self.file_row.itemAt(i).widget()
            if w:
                w.setVisible(visible)

    def _on_mode_changed(self, idx):
        if idx == 0:
            self._show_app_mode()
            self._load_apps()
        elif idx == 1:
            self._show_file_mode()
        else:  # 2 = Automation
            self._show_automation_mode()

    def _load_apps(self):
        self.app_list.clear()
        self.app_list.addItem("Loading applications...")
        self.app_list.setEnabled(False)
        from PyQt6.QtCore import QThread, pyqtSignal

        class Loader(QThread):
            done = pyqtSignal(dict)
            def run(self):
                self.done.emit(get_installed_applications())

        self._loader = Loader()
        self._loader.done.connect(self._on_apps_loaded)
        self._loader.start()

    def _on_apps_loaded(self, apps):
        self._apps = apps
        self.app_list.clear()
        self.app_list.setEnabled(True)
        for name in apps:
            self.app_list.addItem(name)

    def _load_automations(self):
        """Populate the list with names of saved automations, excluding self-references."""
        import glob
        self.app_list.clear()
        self._apps = {}
        data_dir = os.path.join(os.getcwd(), 'data', 'automations')
        for f in glob.glob(os.path.join(data_dir, "*.json")):
            name = os.path.splitext(os.path.basename(f))[0]
            if name != "state" and name not in self._exclude_names:
                self.app_list.addItem(name)
                self._apps[name] = f"automations://{name}"

    def _filter_list(self, text):
        for i in range(self.app_list.count()):
            item = self.app_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def _browse_file(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if path:
            self.file_edit.setText(path)

    def _accept_list_item(self, item):
        self.selected_path = self._apps.get(item.text(), item.text())
        self.accept()

    def _on_ok(self):
        idx = self.mode_combo.currentIndex()
        if idx == 1:  # File mode
            self.selected_path = self.file_edit.text().strip()
        else:  # App or Automation mode — use list selection
            items = self.app_list.selectedItems()
            if items:
                self.selected_path = self._apps.get(items[0].text(), items[0].text())
            else:
                self.selected_path = ""
        self.accept()



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
