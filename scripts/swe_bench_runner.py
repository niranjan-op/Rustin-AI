import os
import json
import subprocess
import shutil
import sys

# Force UTF-8 encoding for standard output to handle emojis on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

from datasets import load_dataset
from langchain_core.messages import HumanMessage

# Add the project root to sys.path so we can import from agent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.graph import app_graph
from agent.states import AgentState

def run_swe_bench_instance(instance):
    instance_id = instance['instance_id']
    repo = instance['repo']
    base_commit = instance['base_commit']
    problem_statement = instance['problem_statement']

    print(f"=====================================")
    print(f"Running SWE-bench instance: {instance_id}")
    print(f"Repo: {repo}, Commit: {base_commit}")
    
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sandbox', 'swe_bench_workspaces', instance_id))
    
    # Clean up old workspace if exists
    if os.path.exists(workspace_dir):
        def remove_readonly(func, path, excinfo):
            import stat
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(workspace_dir, onerror=remove_readonly)
        
    os.makedirs(os.path.dirname(workspace_dir), exist_ok=True)

    # 1. Clone repo
    repo_url = f"https://github.com/{repo}.git"
    print(f"Cloning {repo_url} into {workspace_dir}...")
    subprocess.run(["git", "clone", repo_url, workspace_dir], check=True)
    
    # 2. Checkout base_commit
    print(f"Checking out base commit {base_commit}...")
    subprocess.run(["git", "checkout", base_commit], cwd=workspace_dir, check=True)
    
    # Setup Node sandbox path correctly for headless execution
    from sandbox import node_sandbox
    node_sandbox.node_instance.project_path = workspace_dir

    # 3. Setup Agent State
    # Note: Using 'projet_path' as it is misspelled in states.py
    initial_state = {
        "messages": [HumanMessage(content=f"Fix this issue:\n\n{problem_statement}")],
        "is_project": True,
        "projet_path": workspace_dir,
        "project_id": instance_id,
        "plan_approved": True, # assume approved so it doesn't wait
    }
    
    print("Starting Rustin AI Agent...")
    try:
        import asyncio
        final_state = asyncio.run(app_graph.ainvoke(initial_state))
    except Exception as e:
        print(f"Agent execution failed: {e}")
        return None
        
    # 4. Capture diff
    print("Agent finished. Capturing diff...")
    diff_process = subprocess.run(["git", "diff", base_commit], cwd=workspace_dir, capture_output=True, text=True)
    model_patch = diff_process.stdout
    
    prediction = {
        "instance_id": instance_id,
        "model_name_or_path": "rustin-ai-gemini-3.1-flash",
        "model_patch": model_patch
    }
    
    return prediction

def main():
    print("Loading SWE-bench Lite dataset (test split)...")
    dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    
    predictions_file = os.path.join(os.path.dirname(__file__), "..", "predictions.jsonl")
    
    # Let's run just 1 instance for testing
    instances_to_run = 1
    
    with open(predictions_file, "w", encoding="utf-8") as f:
        for i, instance in enumerate(dataset):
            if i >= instances_to_run:
                break
            prediction = run_swe_bench_instance(instance)
            if prediction:
                f.write(json.dumps(prediction) + "\n")
                print(f"Saved prediction for {instance['instance_id']}")
                
    print(f"Done! Predictions saved to {predictions_file}")

if __name__ == "__main__":
    main()
