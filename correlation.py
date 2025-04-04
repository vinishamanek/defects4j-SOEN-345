import os
import pandas as pd
from scipy.stats import pearsonr
import matplotlib.pyplot as plt

def analyze_project(project_folder):
    """Calculate correlation between mutation score and condition coverage for a project."""
    project_name = os.path.basename(project_folder)
    
    mutation_file = os.path.join(project_folder, "mutation.csv")
    condition_file = os.path.join(project_folder, "condition.csv")
    
    mutation_df = pd.read_csv(mutation_file)
    condition_df = pd.read_csv(condition_file)
    
    merged_df = pd.merge(mutation_df, condition_df, on="ClassName", how="inner")
    
    mutation_scores = merged_df["MutationScore"]
    condition_coverage = merged_df["ConditionCoverage"]
    
    correlation, p_value = pearsonr(mutation_scores, condition_coverage)
    
    print(f"Results for {project_name}:")
    print(f"  Number of classes: {len(merged_df)}")
    print(f"  Correlation: {correlation:.4f}")
    print(f"  P-value: {p_value:.4f}")
    
    plt.figure(figsize=(8, 6))
    plt.scatter(condition_coverage, mutation_scores)
    plt.xlabel("Condition Coverage (%)")
    plt.ylabel("Mutation Score (%)")
    plt.title(f"{project_name}: Correlation = {correlation:.4f}")
    plt.grid(True, alpha=0.3)
    plt.savefig(f"{project_name}_correlation.png")
    
    return correlation, p_value, len(merged_df)

def analyze_all_projects(root_folder):
    """Analyze all project folders."""
    results = []
    
    project_folders = [
        os.path.join(root_folder, folder) 
        for folder in os.listdir(root_folder) 
        if os.path.isdir(os.path.join(root_folder, folder))
    ]
    
    for folder in project_folders:
        try:
            correlation, p_value, num_classes = analyze_project(folder)
            results.append({
                "project": os.path.basename(folder),
                "correlation": correlation,
                "p_value": p_value,
                "num_classes": num_classes
            })
        except Exception as e:
            print(f"Error processing {folder}: {str(e)}")
    
    if results:
        summary_df = pd.DataFrame(results)
        print("\nSummary of all projects:")
        print(summary_df.to_string(index=False))
    
    return results

if __name__ == "__main__":
    root_folder = "."
    analyze_all_projects(root_folder)