"""
Automated Data Validation Gate Engine (Great Expectations)
Fulfills Sections 6.5, 6.6, 6.7, 6.9, 7.2.
Course: ETL (UAO) - Workshop 2
"""
import json
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
import great_expectations as gx
from src.config import EVIDENCE_DIR

logger = logging.getLogger("validation")

class QualityGateFailureError(Exception):
    """Raised when a Critical Data Quality rule fails, blocking downstream pipeline execution."""
    def __init__(self, message, rule_id, evidence):
        super().__init__(message)
        self.rule_id = rule_id
        self.evidence = evidence

def run_gx_suite_on_df(df: pd.DataFrame, suite_name: str, expectations_def: list) -> dict:
    """
    Executes a Great Expectations validation run on a DataFrame using GX 1.x API.
    Returns comprehensive structured result report.
    """
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(f"source_{suite_name}")
    data_asset = data_source.add_dataframe_asset(name=f"asset_{suite_name}")
    batch_def = data_asset.add_batch_definition_whole_dataframe(f"batch_{suite_name}")
    
    suite = context.suites.add(gx.ExpectationSuite(name=suite_name))
    
    rule_map = {}
    for rule_id, severity, exp_obj in expectations_def:
        suite.add_expectation(exp_obj)
        # Store metadata mapping rule_id and severity
        rule_map[exp_obj.expectation_type + "_" + str(getattr(exp_obj, "column", ""))] = {
            "rule_id": rule_id,
            "severity": severity
        }
        
    val_def = context.validation_definitions.add(
        gx.ValidationDefinition(name=f"val_{suite_name}", data=batch_def, suite=suite)
    )
    
    val_result = val_def.run(batch_parameters={"dataframe": df})
    result_dict = val_result.describe_dict()
    
    # Enrich result with Rule IDs and Severity
    evaluated_rules = []
    overall_critical_passed = True
    critical_failures = []
    warning_failures = []
    
    for exp_res in result_dict.get("expectations", []):
        exp_type = exp_res.get("expectation_type")
        col = exp_res.get("kwargs", {}).get("column", "")
        key = f"{exp_type}_{col}"
        meta = rule_map.get(key, {"rule_id": "UNKNOWN", "severity": "Informational"})
        
        is_success = exp_res.get("success", False)
        rule_record = {
            "rule_id": meta["rule_id"],
            "severity": meta["severity"],
            "expectation_type": exp_type,
            "column": col,
            "success": is_success,
            "details": exp_res.get("result", {})
        }
        evaluated_rules.append(rule_record)
        
        if not is_success:
            if meta["severity"] == "Critical":
                overall_critical_passed = False
                critical_failures.append(rule_record)
            elif meta["severity"] == "Warning":
                warning_failures.append(rule_record)

    report = {
        "suite_name": suite_name,
        "evaluated_at": datetime.utcnow().isoformat() + "Z",
        "total_records_evaluated": len(df),
        "overall_success": result_dict.get("success", False),
        "critical_passed": overall_critical_passed,
        "total_evaluated": len(evaluated_rules),
        "critical_failure_count": len(critical_failures),
        "warning_failure_count": len(warning_failures),
        "critical_failures": critical_failures,
        "warning_failures": warning_failures,
        "rule_results": evaluated_rules
    }
    return report

def validate_spotify_raw(raw_file: Path, output_report: Path = None) -> dict:
    """
    Raw Validation Gate: Evaluates Spotify catalog batch before entering transformation.
    """
    logger.info(f"Executing Raw Validation Gate on Spotify dataset: {raw_file}")
    df = pd.read_csv(raw_file) if str(raw_file).endswith(".csv") else pd.read_parquet(raw_file)
    
    expectations_def = [
        ("RULE-RAW-SPOTIFY-01", "Critical", gx.expectations.ExpectColumnValuesToNotBeNull(column="track_id")),
        ("RULE-RAW-SPOTIFY-02", "Critical", gx.expectations.ExpectColumnValuesToBeBetween(column="danceability", min_value=0.0, max_value=1.0)),
        ("RULE-RAW-SPOTIFY-03", "Critical", gx.expectations.ExpectColumnValuesToBeBetween(column="energy", min_value=0.0, max_value=1.0)),
        ("RULE-RAW-SPOTIFY-04", "Critical", gx.expectations.ExpectColumnValuesToBeBetween(column="valence", min_value=0.0, max_value=1.0)),
        ("RULE-RAW-SPOTIFY-05", "Critical", gx.expectations.ExpectColumnValuesToBeBetween(column="acousticness", min_value=0.0, max_value=1.0)),
        ("RULE-RAW-SPOTIFY-06", "Warning",  gx.expectations.ExpectColumnValuesToBeBetween(column="popularity", min_value=0, max_value=100)),
        ("RULE-RAW-SPOTIFY-07", "Warning",  gx.expectations.ExpectColumnValuesToNotBeNull(column="artists", mostly=0.9999))
    ]
    
    report = run_gx_suite_on_df(df, "spotify_raw_suite", expectations_def)
    
    report_path = output_report or (EVIDENCE_DIR / "gx_reports" / "spotify_raw_validation.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Spotify raw validation report saved to: {report_path}")
    
    if not report["critical_passed"]:
        fail_rule = report["critical_failures"][0]["rule_id"]
        msg = f"CRITICAL QUALITY FAILURE in Spotify Raw Gate! Violating rule: {fail_rule}. Pipeline execution blocked."
        logger.error(msg)
        raise QualityGateFailureError(msg, fail_rule, report)
        
    if report["warning_failure_count"] > 0:
        logger.warning(f"Spotify Raw Gate encountered {report['warning_failure_count']} Warnings. Proceeding under documented exception policy.")
        
    logger.info("Spotify Raw Validation Gate PASSED successfully.")
    return report

def validate_grammy_raw(raw_file: Path, output_report: Path = None) -> dict:
    """
    Raw Validation Gate: Evaluates Grammy relational batch before entering transformation.
    """
    logger.info(f"Executing Raw Validation Gate on Grammy dataset: {raw_file}")
    df = pd.read_csv(raw_file) if str(raw_file).endswith(".csv") else pd.read_parquet(raw_file)
    
    expectations_def = [
        ("RULE-RAW-GRAMMY-01", "Critical", gx.expectations.ExpectColumnValuesToBeBetween(column="year", min_value=1958, max_value=2026)),
        ("RULE-RAW-GRAMMY-02", "Critical", gx.expectations.ExpectColumnValuesToNotBeNull(column="category")),
        ("RULE-RAW-GRAMMY-03", "Warning",  gx.expectations.ExpectColumnValuesToBeInSet(column="winner", value_set=[True, False, 1, 0, "True", "False"])),
        ("RULE-RAW-GRAMMY-04", "Warning",  gx.expectations.ExpectColumnValuesToNotBeNull(column="nominee", mostly=0.99))
    ]
    
    report = run_gx_suite_on_df(df, "grammy_raw_suite", expectations_def)
    
    report_path = output_report or (EVIDENCE_DIR / "gx_reports" / "grammy_raw_validation.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Grammy raw validation report saved to: {report_path}")
    
    if not report["critical_passed"]:
        fail_rule = report["critical_failures"][0]["rule_id"]
        msg = f"CRITICAL QUALITY FAILURE in Grammy Raw Gate! Violating rule: {fail_rule}. Pipeline execution blocked."
        logger.error(msg)
        raise QualityGateFailureError(msg, fail_rule, report)
        
    if report["warning_failure_count"] > 0:
        logger.warning(f"Grammy Raw Gate encountered {report['warning_failure_count']} Warnings. Proceeding under documented exception policy.")
        
    logger.info("Grammy Raw Validation Gate PASSED successfully.")
    return report

def validate_prepared(prepared_dir: Path, output_report: Path = None) -> dict:
    """
    Prepared Validation Gate: Evaluates prepared integrated tables prior to loading into DW.
    Section 6.9: Validates schema, domains, uniqueness, referential integrity.
    """
    logger.info(f"Executing Prepared Validation Gate on datasets in: {prepared_dir}")
    
    dim_track = pd.read_csv(prepared_dir / "dim_track.csv")
    dim_artist = pd.read_csv(prepared_dir / "dim_artist.csv")
    fact_perf = pd.read_csv(prepared_dir / "fact_track_performance.csv")
    fact_grammy = pd.read_csv(prepared_dir / "fact_grammy_awards.csv")
    
    # 1. Validate dim_track
    track_rules = [
        ("RULE-PREPARED-01", "Critical", gx.expectations.ExpectColumnValuesToNotBeNull(column="track_id")),
        ("RULE-PREPARED-02", "Critical", gx.expectations.ExpectColumnValuesToBeUnique(column="track_id")),
        ("RULE-PREPARED-03", "Critical", gx.expectations.ExpectColumnValuesToBeBetween(column="danceability", min_value=0.0, max_value=1.0)),
        ("RULE-PREPARED-04", "Critical", gx.expectations.ExpectColumnValuesToBeBetween(column="energy", min_value=0.0, max_value=1.0))
    ]
    track_rep = run_gx_suite_on_df(dim_track, "prepared_dim_track_suite", track_rules)
    
    # 2. Validate dim_artist
    artist_rules = [
        ("RULE-PREPARED-05", "Critical", gx.expectations.ExpectColumnValuesToNotBeNull(column="artist_id")),
        ("RULE-PREPARED-06", "Critical", gx.expectations.ExpectColumnValuesToBeUnique(column="artist_id")),
        ("RULE-PREPARED-07", "Critical", gx.expectations.ExpectColumnValuesToNotBeNull(column="artist_name"))
    ]
    artist_rep = run_gx_suite_on_df(dim_artist, "prepared_dim_artist_suite", artist_rules)
    
    # 3. Validate fact_track_performance
    fact_rules = [
        ("RULE-PREPARED-08", "Critical", gx.expectations.ExpectColumnValuesToNotBeNull(column="track_id")),
        ("RULE-PREPARED-09", "Critical", gx.expectations.ExpectColumnValuesToNotBeNull(column="artist_id")),
        ("RULE-PREPARED-10", "Critical", gx.expectations.ExpectColumnValuesToNotBeNull(column="genre_id")),
        ("RULE-PREPARED-11", "Critical", gx.expectations.ExpectColumnValuesToBeBetween(column="popularity", min_value=0, max_value=100))
    ]
    fact_rep = run_gx_suite_on_df(fact_perf, "prepared_fact_track_suite", fact_rules)
    
    # 4. Validate fact_grammy_awards
    grammy_rules = [
        ("RULE-PREPARED-12", "Critical", gx.expectations.ExpectColumnValuesToNotBeNull(column="award_year")),
        ("RULE-PREPARED-13", "Critical", gx.expectations.ExpectColumnValuesToNotBeNull(column="category_id")),
        ("RULE-PREPARED-14", "Warning",  gx.expectations.ExpectColumnValuesToBeInSet(column="is_winner", value_set=[True, False, 1, 0]))
    ]
    grammy_rep = run_gx_suite_on_df(fact_grammy, "prepared_fact_grammy_suite", grammy_rules)
    
    # Referential integrity check
    artist_ids_set = set(dim_artist["artist_id"])
    orphan_artists = fact_perf[~fact_perf["artist_id"].isin(artist_ids_set)]
    ref_integrity_passed = (len(orphan_artists) == 0)
    
    all_critical_passed = (
        track_rep["critical_passed"] and
        artist_rep["critical_passed"] and
        fact_rep["critical_passed"] and
        grammy_rep["critical_passed"] and
        ref_integrity_passed
    )
    
    combined_report = {
        "suite_name": "prepared_data_master_suite",
        "evaluated_at": datetime.utcnow().isoformat() + "Z",
        "overall_success": all_critical_passed,
        "critical_passed": all_critical_passed,
        "referential_integrity_passed": ref_integrity_passed,
        "sub_suites": {
            "dim_track": track_rep,
            "dim_artist": artist_rep,
            "fact_track_performance": fact_rep,
            "fact_grammy_awards": grammy_rep
        }
    }
    
    report_path = output_report or (EVIDENCE_DIR / "gx_reports" / "prepared_data_validation.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(combined_report, f, indent=2)
        
    logger.info(f"Prepared data validation report saved to: {report_path}")
    
    if not all_critical_passed:
        msg = "CRITICAL QUALITY FAILURE in Prepared Validation Gate! Loading into Data Warehouse is BLOCKED."
        logger.error(msg)
        raise QualityGateFailureError(msg, "RULE-PREPARED-CRITICAL", combined_report)
        
    logger.info("Prepared Validation Gate PASSED successfully. Data is approved for DW load.")
    return combined_report

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    from src.config import RAW_DATA_DIR
    validate_spotify_raw(RAW_DATA_DIR / "spotify_raw.csv")
    validate_grammy_raw(RAW_DATA_DIR / "grammy_raw.csv")
