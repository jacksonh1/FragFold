
import os
from chimerax.core.commands import run
from chimerax.atomic import all_atomic_structures
from pathlib import Path

# Define the directory containing PDB files
pdb_dir = Path('./')
output_dir = Path('./aligned_pdbs')
output_dir.mkdir(exist_ok=True, parents=True)

# Get list of all PDB files in the directory
pdb_files = list(pdb_dir.glob('*.pdb'))

# Open the reference PDB file (assumed to be the first one)
run(session, f"open {pdb_files[0]}")
reference_model_id = 1  # The first model (assumed as #1)
model_num_map = {reference_model_id: pdb_files[0]}  # Map model ID to PDB file path

# Align each subsequent PDB file to the reference (first) model
for i, pdb_file in enumerate(pdb_files[1:], start=2):
    run(session, f"open {pdb_file}")
    # Align the newly opened model (model id will be `i`) to the reference model (model id #1)
    run(session, f"mm #{i} to #{reference_model_id}")
    model_num_map[i] = pdb_file  # Map model ID to PDB file path

# Save aligned models
for model in all_atomic_structures(session):
    model_id = model.id[0]  # Directly use the model ID
    print(f"Saving model with ID: {model_id}")  # Debugging output
    
    # Corrected save command syntax
    run(session, f"save ./aligned_pdbs/{model_num_map[model_id].stem}-aligned.pdb format pdb models #{model_id}")
