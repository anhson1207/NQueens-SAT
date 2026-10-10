import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

def load_full_benchmark_data(raw_path: str | Path) -> pd.DataFrame:
    raw_path = Path(raw_path)
    records = []
    
    if not raw_path.exists():
        return pd.DataFrame()
        
    with open(raw_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if not record.get("is_warmup", False) and record.get("experiment_id") == "nqueens_primary_full":
                    records.append(record)
            except json.JSONDecodeError:
                pass
                
    if not records:
        return pd.DataFrame()
        
    df = pd.DataFrame(records)
    
    # Process some columns if needed
    if "pipeline_total_time" not in df.columns:
        df["pipeline_total_time"] = None
        
    return df
