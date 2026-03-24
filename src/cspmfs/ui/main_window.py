from __future__ import annotations

from dataclasses import asdict
import logging
from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from cspmfs.core.project_manager import ProjectManager
from cspmfs.geometry.preprocess import CropRange, PreprocessConfig, PreprocessResult, preprocess_image
from cspmfs.io.exporter import (
    build_summary_lines,
    copy_runtime_log,
    export_array_csv,
    export_json,
    export_rev_stats_csv,
    make_export_root,
    write_summary_report,
)
from cspmfs.lbm.d2q9_solver import SimulationConfig, SimulationResult
from cspmfs.lbm.simulation import run_simulation
from cspmfs.upscaling.permeability import PermeabilityInput, PermeabilityResult, compute_effective_permeability
from cspmfs.upscaling.rev_analysis import REVAnalyzer, REVConfig, REVResult
from cspmfs.visualization.plots import plot_rev_curves, save_all_figures
from cspmfs.visualization.viewer import VisualizationArea


class MainWindow(QMainWindow):
    """Main application window for Phase 6."""

    def __init__(self, project_manager: ProjectManager, logger: logging.Logger) -> None:
        super().__init__()
        self.project_manager = project_manager
        self.logger = logger
        self.current_image: Path | None = None
        self.preprocess_result: PreprocessResult | None = None
        self.simulation_result: SimulationResult | None = None
        self.perm_result: PermeabilityResult | None = None
        self.rev_result: REVResult | None = None
        self.last_export_root: Path | None = None

        self.setWindowTitle("Cross-Scale Porous Media Flow Simulation Platform")
        self.resize(1480, 920)

        self._build_menu()
        self._build_toolbar()
        self._build_layout()

    def _build_menu(self) -> None:
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        sim_menu = menu.addMenu("Simulation")
        export_menu = menu.addMenu("Export")

        self.action_new = QAction("New Project", self)
        self.action_open = QAction("Open Project", self)
        self.action_save = QAction("Save Project", self)
        self.action_import = QAction("Import 2D Image", self)
        self.action_preprocess = QAction("Preprocess Geometry", self)
        self.action_run_sim = QAction("Run Simulation", self)
        self.action_run_rev = QAction("Run REV Analysis", self)
        self.action_export = QAction("Export Full Package", self)
        self.action_export_fig = QAction("Export Figures Only", self)

        file_menu.addActions([self.action_new, self.action_open, self.action_save, self.action_import])
        sim_menu.addActions([self.action_preprocess, self.action_run_sim, self.action_run_rev])
        export_menu.addActions([self.action_export, self.action_export_fig])

        self._connect_actions()

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar", self)
        self.addToolBar(toolbar)
        toolbar.addActions([
            self.action_new,
            self.action_open,
            self.action_save,
            self.action_import,
            self.action_preprocess,
            self.action_run_sim,
            self.action_run_rev,
            self.action_export,
            self.action_export_fig,
        ])

    def _build_layout(self) -> None:
        container = QWidget(self)
        root = QVBoxLayout(container)

        horizontal = QSplitter(Qt.Orientation.Horizontal)
        horizontal.addWidget(self._create_left_panel())
        self.viewer = VisualizationArea()
        horizontal.addWidget(self.viewer)
        horizontal.addWidget(self._create_right_panel())
        horizontal.setSizes([400, 740, 340])

        self.log_text = QTextEdit(); self.log_text.setReadOnly(True); self.log_text.setMinimumHeight(150)
        root.addWidget(horizontal)
        root.addWidget(QLabel("Runtime Log"))
        root.addWidget(self.log_text)
        self.setCentralWidget(container)

    def _create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        summary_form = QFormLayout()
        self.lbl_project = QLabel("No project")
        self.lbl_image = QLabel("No image")
        summary_form.addRow("Project", self.lbl_project)
        summary_form.addRow("Image", self.lbl_image)

        preprocess_form = QFormLayout()
        self.threshold_spin = QSpinBox(); self.threshold_spin.setRange(0, 255); self.threshold_spin.setValue(128)
        self.invert_check = QCheckBox("Invert binary")
        self.min_component_spin = QSpinBox(); self.min_component_spin.setRange(0, 1_000_000); self.min_component_spin.setValue(0)
        self.fill_hole_check = QCheckBox("Fill small holes")
        self.max_hole_spin = QSpinBox(); self.max_hole_spin.setRange(0, 1_000_000); self.max_hole_spin.setValue(0)
        preprocess_form.addRow("Threshold", self.threshold_spin)
        preprocess_form.addRow(self.invert_check)
        preprocess_form.addRow("Min component size", self.min_component_spin)
        preprocess_form.addRow(self.fill_hole_check)
        preprocess_form.addRow("Max hole size", self.max_hole_spin)

        crop_widget = QWidget(); crop_grid = QGridLayout(crop_widget)
        self.crop_xmin = QSpinBox(); self.crop_xmin.setRange(0, 100000); self.crop_xmin.setValue(0)
        self.crop_xmax = QSpinBox(); self.crop_xmax.setRange(1, 100000); self.crop_xmax.setValue(100000)
        self.crop_ymin = QSpinBox(); self.crop_ymin.setRange(0, 100000); self.crop_ymin.setValue(0)
        self.crop_ymax = QSpinBox(); self.crop_ymax.setRange(1, 100000); self.crop_ymax.setValue(100000)
        crop_grid.addWidget(QLabel("Crop x_min"), 0, 0); crop_grid.addWidget(self.crop_xmin, 0, 1)
        crop_grid.addWidget(QLabel("Crop x_max"), 1, 0); crop_grid.addWidget(self.crop_xmax, 1, 1)
        crop_grid.addWidget(QLabel("Crop y_min"), 2, 0); crop_grid.addWidget(self.crop_ymin, 2, 1)
        crop_grid.addWidget(QLabel("Crop y_max"), 3, 0); crop_grid.addWidget(self.crop_ymax, 3, 1)

        solver_form = QFormLayout()
        self.tau_spin = QDoubleSpinBox(); self.tau_spin.setRange(0.51, 3.0); self.tau_spin.setDecimals(3); self.tau_spin.setValue(0.8)
        self.rho_in_spin = QDoubleSpinBox(); self.rho_in_spin.setRange(1.0, 2.0); self.rho_in_spin.setDecimals(4); self.rho_in_spin.setValue(1.01)
        self.rho_out_spin = QDoubleSpinBox(); self.rho_out_spin.setRange(0.5, 1.5); self.rho_out_spin.setDecimals(4); self.rho_out_spin.setValue(1.0)
        self.max_iter_spin = QSpinBox(); self.max_iter_spin.setRange(100, 200000); self.max_iter_spin.setValue(5000)
        self.tol_spin = QDoubleSpinBox(); self.tol_spin.setRange(1e-10, 1e-2); self.tol_spin.setDecimals(10); self.tol_spin.setValue(1e-6)
        self.dx_spin = QDoubleSpinBox(); self.dx_spin.setRange(0.0, 1.0); self.dx_spin.setDecimals(9); self.dx_spin.setValue(0.0)
        solver_form.addRow("Tau", self.tau_spin)
        solver_form.addRow("Rho in", self.rho_in_spin)
        solver_form.addRow("Rho out", self.rho_out_spin)
        solver_form.addRow("Max iterations", self.max_iter_spin)
        solver_form.addRow("Convergence tol", self.tol_spin)
        solver_form.addRow("dx [m/lu] (optional)", self.dx_spin)

        rev_form = QFormLayout()
        self.rev_min_size = QSpinBox(); self.rev_min_size.setRange(4, 512); self.rev_min_size.setValue(16)
        self.rev_num_sizes = QSpinBox(); self.rev_num_sizes.setRange(2, 10); self.rev_num_sizes.setValue(5)
        self.rev_stride_factor = QDoubleSpinBox(); self.rev_stride_factor.setRange(0.1, 1.0); self.rev_stride_factor.setValue(0.5)
        self.rev_max_samples = QSpinBox(); self.rev_max_samples.setRange(10, 2000); self.rev_max_samples.setValue(80)
        rev_form.addRow("REV min size", self.rev_min_size)
        rev_form.addRow("REV num sizes", self.rev_num_sizes)
        rev_form.addRow("REV stride factor", self.rev_stride_factor)
        rev_form.addRow("REV max samples/size", self.rev_max_samples)

        layout.addWidget(QLabel("Project")); layout.addLayout(summary_form)
        layout.addWidget(QLabel("Preprocess Parameters")); layout.addLayout(preprocess_form); layout.addWidget(crop_widget)
        layout.addWidget(QLabel("LBM/Permeability Parameters")); layout.addLayout(solver_form)
        layout.addWidget(QLabel("REV Parameters")); layout.addLayout(rev_form)
        layout.addStretch(1)
        return panel

    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("Result Summary"))
        self.result_box = QTextEdit(); self.result_box.setReadOnly(True); self.result_box.setPlainText("No results yet.")
        btn_refresh = QPushButton("Refresh Summary"); btn_refresh.clicked.connect(self._refresh_summary)
        layout.addWidget(self.result_box); layout.addWidget(btn_refresh)
        return panel

    def append_gui_log(self, msg: str) -> None:
        self.log_text.append(msg)

    def _connect_actions(self) -> None:
        self.action_new.triggered.connect(self.on_new_project)
        self.action_open.triggered.connect(self.on_open_project)
        self.action_save.triggered.connect(self.on_save_project)
        self.action_import.triggered.connect(self.on_import_image)
        self.action_preprocess.triggered.connect(self.on_preprocess)
        self.action_run_sim.triggered.connect(self.on_run_simulation)
        self.action_run_rev.triggered.connect(self.on_run_rev)
        self.action_export.triggered.connect(self.on_export)
        self.action_export_fig.triggered.connect(self.on_export_figures_only)

    def _error(self, exc: Exception) -> None:
        self.logger.exception("Operation failed: %s", exc)
        QMessageBox.critical(self, "Error", str(exc))

    def on_new_project(self) -> None:
        try:
            directory = QFileDialog.getExistingDirectory(self, "Choose empty directory")
            if not directory:
                return
            session = self.project_manager.new_project(Path(directory), name="Phase6Project")
            self.lbl_project.setText(str(session.root))
            self.logger.info("Created project: %s", session.root)
            self._refresh_summary()
        except Exception as exc:
            self._error(exc)

    def on_open_project(self) -> None:
        try:
            directory = QFileDialog.getExistingDirectory(self, "Open project directory")
            if not directory:
                return
            session = self.project_manager.open_project(Path(directory))
            self.lbl_project.setText(str(session.root)); self.lbl_image.setText(session.model.image_path or "No image")
            self.logger.info("Opened project: %s", session.root)
            self._refresh_summary()
        except Exception as exc:
            self._error(exc)

    def on_save_project(self) -> None:
        try:
            path = self.project_manager.save_project(); self.logger.info("Saved project: %s", path)
        except Exception as exc:
            self._error(exc)

    def on_import_image(self) -> None:
        try:
            if self.project_manager.current is None:
                raise RuntimeError("Create or open a project first.")
            image, _ = QFileDialog.getOpenFileName(self, "Import 2D Image", filter="Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
            if not image:
                return
            self.current_image = Path(image)
            self.project_manager.current.model.image_path = image
            self.lbl_image.setText(image)
            self.preprocess_result = preprocess_image(self.current_image, self._build_preprocess_config())
            self.viewer.set_original_image(self.preprocess_result.original_rgb)
            self.viewer.set_binary_image(self.preprocess_result.binary)
            self.logger.info("Imported image and created initial preview: %s", image)
            self._refresh_summary()
        except Exception as exc:
            self._error(exc)

    def _build_preprocess_config(self) -> PreprocessConfig:
        return PreprocessConfig(
            threshold=self.threshold_spin.value(),
            invert_binary=self.invert_check.isChecked(),
            min_component_size=self.min_component_spin.value(),
            fill_holes=self.fill_hole_check.isChecked(),
            max_hole_size=self.max_hole_spin.value(),
            crop=CropRange(self.crop_xmin.value(), self.crop_ymin.value(), self.crop_xmax.value(), self.crop_ymax.value()),
        )

    def _build_simulation_config(self, max_iterations: int | None = None) -> SimulationConfig:
        return SimulationConfig(
            tau=self.tau_spin.value(),
            rho_in=self.rho_in_spin.value(),
            rho_out=self.rho_out_spin.value(),
            max_iterations=max_iterations if max_iterations is not None else self.max_iter_spin.value(),
            convergence_tol=self.tol_spin.value(),
            report_interval=100,
        )

    def _exportable_preprocess_config(self) -> dict[str, object]:
        """Return current preprocessing config as a plain-serializable dict."""

        return asdict(self._build_preprocess_config())

    def _exportable_simulation_config(self) -> dict[str, object]:
        """Return current simulation config as a plain-serializable dict."""

        return asdict(self._build_simulation_config())

    def _compute_permeability_from_binary(self, binary_window: np.ndarray, fast_mode: bool = False) -> float | None:
        cfg = self._build_simulation_config(max_iterations=min(1200, self.max_iter_spin.value()) if fast_mode else None)
        sim = run_simulation(binary_window, cfg)
        mask = binary_window.astype(bool)
        if not np.any(mask):
            return None
        avg_ux = float(np.mean(sim.ux[mask]))
        nu_lu = (cfg.tau - 0.5) / 3.0
        perm_in = PermeabilityInput(avg_ux, cfg.rho_in, cfg.rho_out, nu_lu, float(binary_window.shape[1]), self.dx_spin.value() if self.dx_spin.value() > 0 else None)
        return compute_effective_permeability(perm_in).permeability_lu

    def on_preprocess(self) -> None:
        try:
            if self.project_manager.current is None:
                raise RuntimeError("Create or open a project first.")
            image_path = self.current_image or (Path(self.project_manager.current.model.image_path) if self.project_manager.current.model.image_path else None)
            if image_path is None:
                raise RuntimeError("Import an image first.")
            self.preprocess_result = preprocess_image(image_path, self._build_preprocess_config())
            self.viewer.set_original_image(self.preprocess_result.original_rgb)
            self.viewer.set_binary_image(self.preprocess_result.binary)
            self.project_manager.current.model.geometry_preprocessed = True
            self.logger.info("Preprocess complete. porosity=%.6f", self.preprocess_result.porosity)
            self._refresh_summary()
        except Exception as exc:
            self._error(exc)

    def on_run_simulation(self) -> None:
        try:
            if self.project_manager.current is None or self.preprocess_result is None:
                raise RuntimeError("Prepare project and preprocessing first.")
            cfg = self._build_simulation_config()
            self.simulation_result = run_simulation(self.preprocess_result.binary, cfg, progress_callback=lambda i, r: self.logger.info("LBM iter=%d res=%.3e", i, r))

            mask = self.preprocess_result.binary.astype(bool)
            avg_ux = float(np.mean(self.simulation_result.ux[mask])) if np.any(mask) else 0.0
            self.perm_result = compute_effective_permeability(
                PermeabilityInput(avg_ux, cfg.rho_in, cfg.rho_out, (cfg.tau - 0.5) / 3.0, float(self.preprocess_result.width), self.dx_spin.value() if self.dx_spin.value() > 0 else None)
            )
            self.project_manager.current.model.simulation_ran = True
            self.logger.info("Simulation complete. k_lu=%.6e", self.perm_result.permeability_lu)
            self._refresh_summary()
        except Exception as exc:
            self._error(exc)

    def on_run_rev(self) -> None:
        try:
            if self.project_manager.current is None or self.preprocess_result is None:
                raise RuntimeError("Prepare project and preprocessing first.")
            h, w = self.preprocess_result.binary.shape
            base, n, max_size = self.rev_min_size.value(), self.rev_num_sizes.value(), min(h, w)
            sizes: list[int] = []
            s = base
            while len(sizes) < n and s <= max_size:
                sizes.append(s); s += base
            if len(sizes) < 2:
                raise RuntimeError("Not enough valid REV window sizes.")

            analyzer = REVAnalyzer(lambda win: self._compute_permeability_from_binary(win, fast_mode=True))
            self.rev_result = analyzer.run(
                self.preprocess_result.binary,
                REVConfig(sizes, self.rev_stride_factor.value(), 0.01, self.rev_max_samples.value(), 0.05, 0.10),
                progress_callback=lambda msg: self.logger.info(msg),
            )

            if self.rev_result.stats_by_size:
                fig = plot_rev_curves(self.rev_result)
                fig.show()
            self.logger.info("REV complete. suggested_size=%s", self.rev_result.suggested_rev_size)
            self._refresh_summary(extra_note=self.rev_result.criterion_note)
        except Exception as exc:
            self._error(exc)

    def _do_export(self, figures_only: bool) -> None:
        if self.project_manager.current is None:
            raise RuntimeError("Create or open a project first.")
        project_name = self.project_manager.current.model.name
        root = make_export_root(self.project_manager.current.root, project_name)
        self.last_export_root = root

        figure_paths = save_all_figures(
            root / "figures",
            self.preprocess_result.original_rgb if self.preprocess_result else None,
            self.preprocess_result.binary if self.preprocess_result else None,
            self.simulation_result.ux if self.simulation_result else None,
            self.simulation_result.uy if self.simulation_result else None,
            self.simulation_result.velocity_magnitude if self.simulation_result else None,
            self.rev_result,
        )

        if figures_only:
            self.logger.info("Exported figures to %s", root / "figures")
            return

        output_paths: list[Path] = list(figure_paths)

        if self.simulation_result is not None:
            output_paths.append(export_array_csv(root / "tables" / "ux.csv", self.simulation_result.ux))
            output_paths.append(export_array_csv(root / "tables" / "uy.csv", self.simulation_result.uy))
            output_paths.append(export_array_csv(root / "tables" / "velocity_magnitude.csv", self.simulation_result.velocity_magnitude))
        if self.preprocess_result is not None:
            output_paths.append(export_array_csv(root / "tables" / "binary_geometry.csv", self.preprocess_result.binary))
        if self.rev_result is not None:
            output_paths.append(export_rev_stats_csv(root / "tables" / "rev_stats.csv", self.rev_result.stats_by_size))

        summary_json = {
            "project_name": project_name,
            "input_file": self.project_manager.current.model.image_path,
            "preprocess_config": self._exportable_preprocess_config(),
            "porosity": self.preprocess_result.porosity if self.preprocess_result else None,
            "simulation_config": self._exportable_simulation_config(),
            "average_velocity": self.simulation_result.average_velocity if self.simulation_result else None,
            "permeability_lu": self.perm_result.permeability_lu if self.perm_result else None,
            "permeability_m2": self.perm_result.permeability_m2 if self.perm_result else None,
            "rev": {
                "suggested_rev_size": self.rev_result.suggested_rev_size,
                "criterion_note": self.rev_result.criterion_note,
            }
            if self.rev_result
            else None,
        }
        output_paths.append(export_json(root / "reports" / "summary.json", summary_json))

        log_copy = copy_runtime_log(Path.cwd() / "logs" / "application.log", root / "logs" / "runtime.log")
        if log_copy:
            output_paths.append(log_copy)

        summary_lines = build_summary_lines(
            project_name=project_name,
            input_file=self.project_manager.current.model.image_path,
            preprocess_params=self._exportable_preprocess_config(),
            porosity=self.preprocess_result.porosity if self.preprocess_result else None,
            simulation_params=self._exportable_simulation_config(),
            average_velocity=self.simulation_result.average_velocity if self.simulation_result else None,
            permeability_lu=self.perm_result.permeability_lu if self.perm_result else None,
            permeability_m2=self.perm_result.permeability_m2 if self.perm_result else None,
            rev_result=self.rev_result,
            output_paths=output_paths,
        )
        output_paths.append(write_summary_report(root / "reports" / "summary_report.md", summary_lines))

        export_json(root / "reports" / "project_snapshot.json", {"project": self.project_manager.current.model.__dict__})
        self.logger.info("Export package created at %s", root)

    def on_export(self) -> None:
        try:
            self._do_export(figures_only=False)
        except Exception as exc:
            self._error(exc)

    def on_export_figures_only(self) -> None:
        try:
            self._do_export(figures_only=True)
        except Exception as exc:
            self._error(exc)

    def _refresh_summary(self, extra_note: str | None = None) -> None:
        session = self.project_manager.current
        if session is None:
            self.result_box.setPlainText("No project loaded.")
            return

        lines = [
            f"Project: {session.model.name}",
            f"Root: {session.root}",
            f"Image: {session.model.image_path or 'None'}",
            f"Geometry preprocessed: {session.model.geometry_preprocessed}",
            f"Simulation ran: {session.model.simulation_ran}",
        ]
        if self.preprocess_result is not None:
            lines.extend(["--- Preprocess ---", f"Size: {self.preprocess_result.width}x{self.preprocess_result.height}", f"Porosity: {self.preprocess_result.porosity:.6f}"])
        if self.perm_result is not None:
            lines.extend([
                "--- Permeability ---",
                f"k_lu: {self.perm_result.permeability_lu:.6e}",
                f"k_m2: {self.perm_result.permeability_m2:.6e}" if self.perm_result.permeability_m2 is not None else "k_m2: not computed",
            ])
        if self.rev_result is not None:
            lines.extend(["--- REV ---", f"sizes analyzed: {len(self.rev_result.stats_by_size)}", f"suggested REV size: {self.rev_result.suggested_rev_size}", self.rev_result.criterion_note])
        if self.last_export_root is not None:
            lines.append(f"Last export: {self.last_export_root}")
        if extra_note:
            lines.append(extra_note)
        self.result_box.setPlainText("\n".join(lines))
