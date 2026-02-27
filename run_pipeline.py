#!/usr/bin/env python
"""
End-to-end pipeline runner for FB Marketplace Car Transaction Likelihood Predictor.

Usage:
    python run_pipeline.py [--all | --ingest | --train | --score | --writeback | --api]

With no arguments, --all is assumed.
"""
import argparse
import logging
import sys

logger = logging.getLogger(__name__)


def step_init_db():
    print("\n=== 1/5  Initialising database ===")
    from src.storage.database import init_db
    init_db()
    print("    ✓ Database ready.")


def step_ingest():
    print("\n=== 2/5  Running data ingestion ===")
    from src.ingestion.run_ingestion import run_connector_ingestion
    run_connector_ingestion()
    print("    ✓ Ingestion complete.")


def step_train():
    print("\n=== 3/5  Training model ===")
    from src.model.train import train_model
    meta = train_model()
    if meta is None:
        print("    ✗ Training failed — not enough data.")
        sys.exit(1)
    print(f"    ✓ Model trained (AUC={meta['cv_auc_mean']:.3f} ± {meta['cv_auc_std']:.3f})")


def step_score():
    print("\n=== 4/5  Scoring leads ===")
    from src.prediction.predictor import score_all_leads
    df = score_all_leads(save_to_db=True)
    if df.empty:
        print("    ✗ No leads to score.")
        return
    top = df.head(5)
    print(f"    ✓ Scored {len(df)} leads. Top 5 by likelihood:")
    for _, row in top.iterrows():
        print(f"      {row['lead_external_id']:12s}  {row['score']*100:5.1f}%")


def step_writeback():
    print("\n=== 5/5  CRM writeback ===")
    from src.integration.crm_writeback import write_scores_to_crm
    write_scores_to_crm()
    print("    ✓ Writeback complete (check logs — dry-run unless crm.writeback_enabled=true).")


def start_api():
    print("\n=== Starting Prediction API ===")
    print("    POST http://localhost:5000/leads/score")
    print("    GET  http://localhost:5000/leads/scores")
    print("    GET  http://localhost:5000/health")
    print("    Press CTRL+C to stop.\n")
    from src.prediction.api import run_api
    run_api()


def main():
    parser = argparse.ArgumentParser(description="FB Sales Predictor Pipeline")
    parser.add_argument("--all", action="store_true", help="Run full pipeline (default)")
    parser.add_argument("--ingest", action="store_true", help="Ingest data only")
    parser.add_argument("--train", action="store_true", help="Train model only")
    parser.add_argument("--score", action="store_true", help="Score leads only")
    parser.add_argument("--writeback", action="store_true", help="CRM writeback only")
    parser.add_argument("--api", action="store_true", help="Start prediction API server")
    args = parser.parse_args()

    run_all = args.all or not any([args.ingest, args.train, args.score, args.writeback, args.api])

    if run_all or args.ingest:
        step_init_db()
        step_ingest()
    if run_all or args.train:
        step_train()
    if run_all or args.score:
        step_score()
    if run_all or args.writeback:
        step_writeback()
    if args.api:
        start_api()

    if run_all:
        print("\n  Full pipeline complete!")
        print("    Run 'python run_pipeline.py --api' to start the prediction REST API.")


if __name__ == "__main__":
    main()
