from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix, precision_recall_curve, auc
import matplotlib.pyplot as plt # Optional for plotting

def evaluate_model(model_pipeline, X_test, y_test):
    """Evaluates the trained model pipeline."""
    print("Evaluating model...")

    # Predict probabilities and classes
    y_pred_proba = model_pipeline.predict_proba(X_test)[:, 1]
    y_pred = model_pipeline.predict(X_test)

    # Classification Report
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # AUC Score
    try:
        auc_score = roc_auc_score(y_test, y_pred_proba)
        print(f"\nROC AUC Score: {auc_score:.4f}")
    except ValueError:
        print("\nROC AUC score could not be calculated (possibly only one class present in test set).")


    # Confusion Matrix
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # Precision-Recall AUC (useful for imbalanced data)
    precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
    pr_auc = auc(recall, precision)
    print(f"\nPrecision-Recall AUC: {pr_auc:.4f}")

    # Optional: Plotting
    # try:
    #     from sklearn.metrics import RocCurveDisplay, PrecisionRecallDisplay
    #     RocCurveDisplay.from_estimator(model_pipeline, X_test, y_test)
    #     plt.title('ROC Curve')
    #     plt.show()
    #
    #     PrecisionRecallDisplay.from_estimator(model_pipeline, X_test, y_test)
    #     plt.title('Precision-Recall Curve')
    #     plt.show()
    # except ImportError:
    #     print("Matplotlib/Display not available for plotting.")
    # except Exception as e:
    #     print(f"Error during plotting: {e}")


    # Return metrics as a dictionary
    metrics = {
        'auc_roc': auc_score if 'auc_score' in locals() else None,
        'pr_auc': pr_auc,
        'classification_report': classification_report(y_test, y_pred, output_dict=True),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist() # Convert to list for JSON compatibility
    }
    print("Evaluation complete.")
    return metrics
