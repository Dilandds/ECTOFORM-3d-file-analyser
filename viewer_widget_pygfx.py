"""
Minimal 3D Viewer Widget using pygfx + wgpu for STL file visualization.
WebGPU-based (avoids OpenGL) - intended to fix Windows black screen.
Only file upload and display; other features (ruler, annotations, etc.) not implemented.
"""
import sys
import os
import logging
from PyQt5.QtWidgets import QWidget, QStackedLayout, QGridLayout
from PyQt5.QtCore import Qt, pyqtSignal
from ui.drop_zone_overlay import DropZoneOverlay

logger = logging.getLogger(__name__)


def _trimesh_to_pyvista(tm):
    """Convert trimesh (Trimesh or Scene) to PyVista PolyData for MeshCalculator compatibility."""
    import trimesh
    import numpy as np
    import pyvista as pv

    if isinstance(tm, trimesh.Scene):
        all_meshes = [g for g in tm.geometry.values() if isinstance(g, trimesh.Trimesh)]
        if not all_meshes:
            return None
        tm = trimesh.util.concatenate(all_meshes) if len(all_meshes) > 1 else all_meshes[0]

    if not isinstance(tm, trimesh.Trimesh):
        return None

    vertices = np.asarray(tm.vertices, dtype=np.float64)
    faces = np.asarray(tm.faces, dtype=np.int32)
    cells = np.column_stack([np.full(len(faces), 3), faces]).ravel().astype(np.int32)
    return pv.PolyData(vertices, cells)


def _debug_print(msg):
    print(f"[DEBUG] {msg}", file=sys.stderr)
    if sys.stderr:
        try:
            sys.stderr.flush()
        except (AttributeError, OSError):
            pass


class STLViewerWidget(QWidget):
    """Minimal pygfx-based 3D viewer for STL files. File upload and display only."""

    file_dropped = pyqtSignal(str)
    click_to_upload = pyqtSignal()
    drop_error = pyqtSignal(str)

    def __init__(self, parent=None):
        _debug_print("STLViewerWidget (pygfx): Initializing...")
        logger.info("STLViewerWidget (pygfx): Initializing...")
        super().__init__(parent)

        self.layout = QStackedLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setStackingMode(QStackedLayout.StackAll)

        self.viewer_container = QWidget()
        self.viewer_layout = QGridLayout(self.viewer_container)
        self.viewer_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.viewer_container)

        self.drop_overlay = DropZoneOverlay()
        self.drop_overlay.file_dropped.connect(self._on_file_dropped)
        self.drop_overlay.click_to_upload.connect(self._on_click_upload)
        self.drop_overlay.error_occurred.connect(self._on_drop_error)
        self.layout.addWidget(self.drop_overlay)

        self.layout.setCurrentWidget(self.drop_overlay)

        self._canvas = None
        self._renderer = None
        self._scene = None
        self._camera = None
        self._controller = None
        self._mesh_obj = None
        self.current_mesh = None  # Trimesh object for compatibility
        self.current_actor = None  # Not used; kept for hasattr checks
        self.plotter = None  # Not used; kept for hasattr checks
        self._model_loaded = False
        self._initialized = False

        _debug_print("STLViewerWidget (pygfx): Basic init complete")

    def showEvent(self, event):
        super().showEvent(event)
        if not self._initialized:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, self._init_pygfx)

    def _init_pygfx(self):
        if self._initialized:
            return
        try:
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()

            if not self.isVisible() or not self.window().isVisible():
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(200, self._init_pygfx)
                return

            _debug_print("STLViewerWidget (pygfx): Creating pygfx canvas...")
            import pygfx as gfx
            from rendercanvas.qt import QRenderWidget

            self._canvas = QRenderWidget(parent=self.viewer_container)
            self.viewer_layout.addWidget(self._canvas)

            self._renderer = gfx.WgpuRenderer(self._canvas)
            self._scene = gfx.Scene()
            self._scene.add(gfx.AmbientLight())
            self._scene.add(gfx.DirectionalLight())

            w, h = max(400, self.width()), max(300, self.height())
            self._camera = gfx.PerspectiveCamera(50, w / h)
            self._camera.local.position = (0, 0, 5)
            self._camera.show_pos((0, 0, 0))

            self._controller = gfx.OrbitController(
                self._camera, register_events=self._renderer
            )

            def animate():
                if self._renderer and self._scene and self._camera:
                    self._renderer.render(self._scene, self._camera)

            self._canvas.request_draw(animate)
            self._initialized = True
            _debug_print("STLViewerWidget (pygfx): pygfx initialized")
            logger.info("STLViewerWidget (pygfx): pygfx initialized")

        except Exception as e:
            _debug_print(f"STLViewerWidget (pygfx): ERROR: {e}")
            logger.error(f"STLViewerWidget (pygfx): Init failed: {e}", exc_info=True)

    def load_stl(self, file_path):
        """Load and display an STL file. Returns True if successful."""
        logger.info(f"load_stl (pygfx): Loading {file_path}")

        if not self._initialized or self._scene is None:
            logger.warning("load_stl (pygfx): Not initialized yet")
            from PyQt5.QtWidgets import QApplication
            for _ in range(50):
                QApplication.processEvents()
                if self._initialized and self._scene is not None:
                    break
                import time
                time.sleep(0.1)
            if not self._initialized or self._scene is None:
                logger.error("load_stl (pygfx): Init failed")
                return False

        file_ext = file_path.lower()
        supported = ('.stl', '.obj', '.ply')
        if not any(file_ext.endswith(ext) for ext in supported):
            logger.warning(f"load_stl (pygfx): Only STL/OBJ/PLY supported, got {file_ext}")
            return False

        try:
            import pygfx as gfx

            if self._mesh_obj is not None:
                self._scene.remove(self._mesh_obj)
                self._mesh_obj = None

            meshes = gfx.load_mesh(file_path)
            if not meshes:
                raise ValueError("No meshes in file")

            mesh_group = gfx.Group()
            for m in meshes:
                m.material = gfx.MeshPhongMaterial(color="#add8e6")
                mesh_group.add(m)
            self._mesh_obj = mesh_group
            self._scene.add(self._mesh_obj)

            import trimesh
            mesh_tri = trimesh.load(file_path, force='mesh')
            # Convert to PyVista for MeshCalculator compatibility (expects .bounds, .volume, .area)
            pv_mesh = _trimesh_to_pyvista(mesh_tri)
            if pv_mesh is None:
                raise ValueError("Could not convert mesh for dimensions/volume calculation")
            self.current_mesh = pv_mesh
            self._model_loaded = True
            self._show_overlay(False)

            self._camera.show_object(self._mesh_obj)
            if self._canvas:
                self._canvas.update()

            logger.info("load_stl (pygfx): Loaded successfully")
            return True

        except Exception as e:
            logger.error(f"load_stl (pygfx): Error: {e}", exc_info=True)
            return False

    def clear_viewer(self):
        """Clear the 3D viewer."""
        if self._scene and self._mesh_obj:
            self._scene.remove(self._mesh_obj)
            self._mesh_obj = None
        self.current_mesh = None
        self._model_loaded = False
        self._show_overlay(True)
        if self._canvas:
            self._canvas.update()
        logger.info("clear_viewer (pygfx): Cleared")

    def _on_file_dropped(self, file_path):
        self.file_dropped.emit(file_path)

    def _on_click_upload(self):
        self.click_to_upload.emit()

    def _on_drop_error(self, error_msg):
        self.drop_error.emit(error_msg)

    def _show_overlay(self, show):
        if show:
            self.drop_overlay.show()
            self.drop_overlay.raise_()
        else:
            self.drop_overlay.hide()
