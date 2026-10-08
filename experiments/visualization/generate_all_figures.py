import argparse
import logging
import json
from datetime import datetime
from pathlib import Path

from .data_validator import validate_full_benchmark_dataset
from .data_loader import load_full_benchmark_data
from .plot_sat_runtime import plot_sat_runtime_vs_n
from .plot_exact_runtime import plot_exact_solver_runtime_vs_n
from .plot_all_methods import plot_all_methods_n20
from .plot_sat_structure import plot_sat_clause_growth, plot_sat_variable_overhead_n100
from .plot_completion_matrix import plot_completion_matrix
from .plot_runtime_variability import plot_runtime_variability
from .export_tables import export_all_tables

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def generate_all_figures(
    input_path: str | Path,
    metadata_path: str | Path,
    output_dir: str | Path,
    experiment_id: str = "nqueens_primary_full",
    validate_only: bool = False
):
    input_path = Path(input_path)
    metadata_path = Path(metadata_path)
    output_dir = Path(output_dir)
    
    # 1. Validation
    logging.info(f"Validating dataset: {input_path}")
    val_result = validate_full_benchmark_dataset(input_path, metadata_path)
    
    if not val_result["valid"]:
        logging.error("Validation failed:")
        for prob in val_result["problems"]:
            logging.error(f"  - {prob}")
        logging.warning("Data is invalid or incomplete. Figures will not be generated.")
        
        # Even if validate_only is False, if the dataset is not valid we should abort officially.
        # Since prompt asks not to plot official if not valid.
        return False
        
    logging.info("Validation passed. Dataset is complete and valid.")
    
    if validate_only:
        logging.info("Validate-only mode. Exiting.")
        return True
        
    # 2. Loading
    logging.info("Loading dataset...")
    df = load_full_benchmark_data(input_path)
    if df.empty:
        logging.error("Loaded dataframe is empty.")
        return False
        
    metadata = {}
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as e:
            logging.warning(f"Could not read metadata: {e}")
            
    output_dir.mkdir(parents=True, exist_ok=True)
    table_dir = output_dir.parent.parent / "tables"
    if not table_dir.exists():
        table_dir = output_dir
        
    # 3. Generating plots
    logging.info("Generating Figure 1: SAT runtime...")
    plot_sat_runtime_vs_n(df, output_dir)
    
    logging.info("Generating Figure 2: Exact solver runtime...")
    plot_exact_solver_runtime_vs_n(df, output_dir)
    
    logging.info("Generating Figure 3: All-nine-method comparison...")
    plot_all_methods_n20(df, output_dir)
    
    logging.info("Generating Figure 4: SAT clause growth...")
    plot_sat_clause_growth(df, output_dir)
    
    logging.info("Generating Figure 5: SAT variable overhead...")
    plot_sat_variable_overhead_n100(df, output_dir)
    
    logging.info("Generating Figure 6: Completion matrix...")
    plot_completion_matrix(df, output_dir)
    
    logging.info("Generating Figure 7: Runtime variability...")
    plot_runtime_variability(df, output_dir)
    
    # 4. Generating tables
    logging.info("Exporting tables...")
    export_all_tables(df, table_dir, metadata)
    
    # 5. Generate Manifest
    logging.info("Generating manifest...")
    manifest = {
        "input_dataset": str(input_path),
        "experiment_id": experiment_id,
        "data_validation_status": "PASS",
        "figure_names": [
            "fig01_sat_runtime_vs_n.png", "fig01_sat_runtime_vs_n.pdf",
            "fig02_exact_solver_runtime_vs_n.png", "fig02_exact_solver_runtime_vs_n.pdf",
            "fig03_all_methods_n20.png", "fig03_all_methods_n20.pdf",
            "fig04_sat_clause_growth.png", "fig04_sat_clause_growth.pdf",
            "fig05_sat_variable_overhead_n100.png", "fig05_sat_variable_overhead_n100.pdf",
            "fig06_completion_matrix.png", "fig06_completion_matrix.pdf",
            "fig07_runtime_variability.png", "fig07_runtime_variability.pdf"
        ],
        "figure_generation_timestamp": datetime.utcnow().isoformat() + "Z",
        "primary_timing_metric": "pipeline_total_time",
        "configuration_fingerprint": metadata.get("experiment_config", {}).get("config_fingerprint", "Unknown")
    }
    
    with open(output_dir / "figure_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
        
    logging.info("All visualization tasks completed successfully.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate full benchmark scientific figures")
    parser.add_argument("--input", type=str, default="results/raw/benchmark_nqueens_primary_full.jsonl")
    parser.add_argument("--metadata", type=str, default="results/metadata/benchmark_nqueens_primary_full_metadata.json")
    parser.add_argument("--output-dir", type=str, default="results/figures/full")
    parser.add_argument("--experiment-id", type=str, default="nqueens_primary_full")
    parser.add_argument("--validate-only", action="store_true")
    
    args = parser.parse_args()
    
    generate_all_figures(
        input_path=args.input,
        metadata_path=args.metadata,
        output_dir=args.output_dir,
        experiment_id=args.experiment_id,
        validate_only=args.validate_only
    )
