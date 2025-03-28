import os
import subprocess
import re
import csv
import time
from pathlib import Path

def create_output_directories():
    os.makedirs("coverage_results", exist_ok=True)
    os.makedirs("mutation_results", exist_ok=True)

def run_command(command, timeout=300):
    try:
        process = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        return process.stdout, process.stderr, process.returncode
    except subprocess.TimeoutExpired:
        print(f"Command timed out after {timeout} seconds: {command}")
        return "", f"Timeout after {timeout} seconds", 1

def extract_number(pattern, text):
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None

def run_condition_coverage(class_name):
    """run condition coverage analysis for a single class"""
    print(f"running condition coverage...")
    
    try:
        # target file with just this class
        with open("target_class.txt", "w") as f:
            f.write(class_name)
        
        # run coverage for this specific class
        stdout, stderr, return_code = run_command("defects4j coverage -i target_class.txt")
        
        if return_code == 0 and os.path.exists("coverage.xml"):
            # read the coverage.xml file
            with open("coverage.xml", "r") as f:
                coverage_xml = f.read()
            
            # extract coverage data
            total_conditions = extract_number(r'branches-valid="([0-9]*)"', coverage_xml)
            covered_conditions = extract_number(r'branches-covered="([0-9]*)"', coverage_xml)
            
            if total_conditions and int(total_conditions) > 0:
                total_conditions = int(total_conditions)
                covered_conditions = int(covered_conditions)
                coverage_percentage = round(covered_conditions * 100 / total_conditions, 2)
                
                # save the coverage XML for reference
                class_filename = class_name.replace('/', '_')
                with open(f"coverage_results/{class_filename}_coverage.xml", "w") as f:
                    f.write(coverage_xml)
                
                # return coverage data
                print(f"class has {total_conditions} conditions, {covered_conditions} covered ({coverage_percentage}%)")
                
                # clean up
                os.remove("coverage.xml")
                return class_name, total_conditions, covered_conditions, coverage_percentage
            else:
                print(f"skipping coverage (no conditions found or zero conditions)")
        else:
            error_message = stderr if stderr else "Unknown error"
            print(f"coverage analysis failed: {error_message}")
    except Exception as e:
        print(f"error in coverage: {str(e)}")
    
    # clean up if file exists
    if os.path.exists("coverage.xml"):
        os.remove("coverage.xml")
    
    return None

def run_mutation_testing(class_name):
    """run mutation testing for a single class"""
    print(f"running mutation testing...")
    
    try:
        # target file with just this class
        with open("target_class.txt", "w") as f:
            f.write(class_name)
        
        # run mutation testing for this specific class
        stdout, stderr, return_code = run_command("defects4j mutation -i target_class.txt")
        output = stdout + stderr
        
        # check if mutation score is in the output
        if "Mutation score:" in output:
            total_mutants = extract_number(r"Mutants generated:\s*([0-9]+)", output)
            covered_mutants = extract_number(r"Mutants covered:\s*([0-9]+)", output)
            killed_mutants = extract_number(r"Mutants killed:\s*([0-9]+)", output)
            mutation_score = extract_number(r"Mutation score:\s*([0-9.]+)", output)
            
            if total_mutants and int(total_mutants) > 0:
                total_mutants = int(total_mutants)
                covered_mutants = int(covered_mutants) if covered_mutants else 0
                killed_mutants = int(killed_mutants) if killed_mutants else 0
                mutation_score = float(mutation_score) if mutation_score else 0.0
                
                # save detailed output to file
                class_filename = class_name.replace('/', '_').replace('$', '_inner_')
                with open(f"mutation_results/{class_filename}_mutation.txt", "w") as f:
                    f.write(output)
                
                print(f"class has {total_mutants} mutants, {killed_mutants} killed ({mutation_score}%)")
                return class_name, total_mutants, killed_mutants, mutation_score
            else:
                print(f"skipping mutation (no mutants found or zero mutants)")
        else:
            print(f"mutation testing failed or no results: {stderr}")
    except Exception as e:
        print(f"error in mutation: {str(e)}")
    
    return None

# added to avoid reprocessing classes and pick up from previous runs
def get_completed_classes():
    """set of class names that have already been processed"""
    coverage_classes = set()
    mutation_classes = set()
    
    coverage_path = "coverage_results/condition_coverage.csv"
    if os.path.exists(coverage_path) and os.path.getsize(coverage_path) > 0:
        try:
            with open(coverage_path, "r", newline='') as f:
                reader = csv.reader(f)
                next(reader) 
                for row in reader:
                    if row and len(row) > 0:
                        coverage_classes.add(row[0])
        except Exception as e:
            print(f"Error reading coverage results: {str(e)}")
    
    mutation_path = "mutation_results/mutation_scores.csv"
    if os.path.exists(mutation_path) and os.path.getsize(mutation_path) > 0:
        try:
            with open(mutation_path, "r", newline='') as f:
                reader = csv.reader(f)
                next(reader)  
                for row in reader:
                    if row and len(row) > 0:
                        mutation_classes.add(row[0])
        except Exception as e:
            print(f"Error reading mutation results: {str(e)}")
    
    # return the intersection of both sets (classes that completed both tests)
    # this ensures we only skip classes that have completed both coverage and mutation tests
    completed = coverage_classes.intersection(mutation_classes)
    print(f"Found {len(completed)} classes already processed")
    return completed

def ensure_csv_headers():
    """ensure CSV files exist and have headers"""
    coverage_path = "coverage_results/condition_coverage.csv"
    mutation_path = "mutation_results/mutation_scores.csv"
    
    # create coverage CSV (if it doesn't exist)
    if not os.path.exists(coverage_path) or os.path.getsize(coverage_path) == 0:
        with open(coverage_path, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["ClassName", "TotalConditions", "CoveredConditions", "ConditionCoverage"])
    
    # create mutation CSV (if it doesn't exist)
    if not os.path.exists(mutation_path) or os.path.getsize(mutation_path) == 0:
        with open(mutation_path, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["ClassName", "TotalMutants", "KilledMutants", "MutationScore"])

def main():
    """main function to run coverage and mutation analysis with resume capability"""
    start_time = time.time()
    create_output_directories()
    
    ensure_csv_headers()
    completed_classes = get_completed_classes()
    
    # process each class
    try:
        with open("all_classes.txt", "r") as f:
            class_names = [line.strip() for line in f if line.strip()]
        
        # filtering out classes with results already 
        remaining_classes = [c for c in class_names if c not in completed_classes]
        
        total_classes = len(remaining_classes)
        total_original = len(class_names)
        
        if total_classes < total_original:
            print(f"resuming from previous run: {total_original - total_classes} classes already processed")
        
        print(f"found {total_classes} classes remaining to analyze\n")
        
        # run both coverage and mutation for each class before moving to the next
        coverage_results = []
        mutation_results = []
        
        for i, class_name in enumerate(remaining_classes, 1):
            current_position = i + (total_original - total_classes)
            print(f"[{current_position}/{total_original}] processing {class_name}")
            
            # run coverage first
            coverage_result = run_condition_coverage(class_name)
            if coverage_result:
                coverage_results.append(coverage_result)
                with open("coverage_results/condition_coverage.csv", "a", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(coverage_result)
            
            # run mutation for the same class
            mutation_result = run_mutation_testing(class_name)
            if mutation_result:
                mutation_results.append(mutation_result)
                with open("mutation_results/mutation_scores.csv", "a", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(mutation_result)
            
            print("")  
        
        total_coverage = len(completed_classes) + len(coverage_results)
        total_mutation = len(completed_classes) + len(mutation_results)
        
        print(f"\n done analyzing")
        print(f"total coverage results: {total_coverage} classes with valid results.")
        print(f"total mutation results: {total_mutation} classes with valid results.")
        print("all results saved in coverage_results/condition_coverage.csv and mutation_results/mutation_scores.csv")
        
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
    finally:
        if os.path.exists("target_class.txt"):
            os.remove("target_class.txt")
        
if __name__ == "__main__":
    main()