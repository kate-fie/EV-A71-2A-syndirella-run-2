#!venv/bin/env python3
"""
find_scaffolds.py

This module runs to find placement success for each scaffold.
"""
import argparse
import os
import json
import pandas as pd
import csv
import glob2
import logging
from typing import *
from rdkit.Chem import SDWriter
from rdkit import Chem

logger = logging.getLogger()

# Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)
logger.setLevel(logging.DEBUG)

# Create a console handler (StreamHandler) and set its level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create a formatter and set it for the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(console_handler)

def get_delta_delta_G(data: dict) -> float:
    # Get the delta delta G value from the JSON file. Accounts for different formats.
    try:
        return data["Energy"]["xyz_∆∆G"]
    except KeyError:
        try:
            bound = data["Energy"]["bound"]['total_score']
            unbound = data["Energy"]["unbound"]['total_score']
            ddG = bound - unbound
            return ddG
        except KeyError:
            return float('inf')


def format_json_output(json_file_path: str) -> Tuple[str, float, float] | Tuple[str, None, None]:
    logger.info(json_file_path)
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    ddG = get_delta_delta_G(data)
    try:
        rmsd = data["mRMSD"]
    except KeyError:
        rmsd = float('inf')
    if rmsd > 2.0 or ddG > 0:
        outcome = 'place-fail'
    else:
        outcome = 'place-success'
    return outcome, ddG, rmsd

def format_success_sdf(mol_paths: Dict[str, List[str | float]], output_path: str) -> str | None:
    """
    mol_paths contains:
        key: inchi
        value: [path_to_mol, compound_set, ddG, rmsd]

    :param mol_paths:
    :return:
    """
    path = os.path.join(output_path, '23aug_success.sdf')
    with SDWriter(path) as writer:
        for key, value in mol_paths.items():
            if len(value) != 4:
                logger.error('Not enough values to unpack to build SDF')
                return None
            logger.info('writing successful mols')
            path_to_mol = value[0]
            compound_set = value[1]
            ddG = value[2]
            rmsd = value[3]
            mol = Chem.MolFromMolFile(path_to_mol)
            if mol is not None:
                mol.SetProp('inchi', key)
                mol.SetProp('compound_set', compound_set)
                mol.SetProp('ddG', ddG)
                mol.SetProp('rmsd', rmsd)
                writer.write(mol)
    logger.info(f'done writing (if successful) output_path is {path}')
    return path


def make_scaffold_outputs(csv_path: str, home_path: str, output_path: str):
    """
    Potential outcomes:
        not-found: base-check doesn't exist
        not-found: base-check is empty
        place-fail: base-check .json energy and/or RMSD values fail
        place-success: base-check .json energy and/or RMSD values pass

    :param output_path:
    :param home_path:
    :param csv_path: path to csv with columns 'smiles' and 'inchi'
    :return: path to new csv with placement information
    """
    df = pd.read_csv(csv_path)
    if 'smiles' not in df.columns or 'inchi' not in df.columns or 'compound_set' not in df.columns:
        logger.critical('CSV does not contain required columns of "smiles" and/or "inchi" and/or "compound_set"')
        return None
    new_rows = []
    mol_paths = {}
    failed_rows = []
    for i, row in df.iterrows():
        ddG = None
        rmsd = None
        path_to_mol = None
        inchi: str = row['inchi']
        compound_set: str = row['compound_set']
        base_check_dirs: List[str]= glob2.glob(os.path.join(home_path, f'*/{inchi}-base-check/'))
        if len(base_check_dirs) == 0:
            outcome = 'not-found'
        elif len(base_check_dirs) > 1:
            outcome = 'multiple-found'
        else:
            base_check_dir: str = base_check_dirs[0]
            logger.info(base_check_dir)
            json_path: List[str] = glob2.glob(os.path.join(base_check_dir, '**/*.minimised.json'))
            if len(json_path) == 1:
                json = json_path[0]
                outcome, ddG, rmsd = format_json_output(json_file_path=json)
                mol_path: List[str] = glob2.glob(os.path.join(base_check_dir, '**/*.minimised.mol'))
                if len(mol_path) == 1:
                    path_to_mol = mol_path[0]
                    mol_paths[inchi] = [path_to_mol, compound_set, ddG, rmsd]
            else:
                outcome = 'not-found'
        if outcome == 'not-found' or outcome == 'place-fail':
            failed_row = {
                'smiles': row['smiles'],
                'compound_set': row['compound_set'],
                'inchi': row['inchi'],
                'outcome': outcome
            }
            failed_rows.append(failed_row)
        new_row = {
            'smiles': row['smiles'],
            'compound_set': row['compound_set'],
            'inchi': row['inchi'],
            'outcome': outcome,
            'ddG': ddG,
            'rmsd': rmsd,
            'mol_path': path_to_mol
        }
        new_rows.append(new_row)
    # format SDF with success mols
    sdf_output_path = format_success_sdf(mol_paths=mol_paths, output_path=output_path)
    failed_df = pd.DataFrame(failed_rows)
    new_df = pd.DataFrame(new_rows)
    failed_df.to_csv(os.path.join(output_path, '23aug_failed.csv'))
    new_df.to_csv(os.path.join(output_path, '23aug_all_scaffolds_info.csv'))


def config_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', type=str, required=True,
                        help='Input .csv with "smiles" and "inchi" and "compound_set" columns')
    parser.add_argument('-d', type=str, required=True,
                        help='Path to home directory of where to look for bases')
    parser.add_argument('-o', type=str, required=True,
                        help='Output directory')
    return parser

def main():
    parser = config_parser()
    args = parser.parse_args()
    settings = vars(args)
    make_scaffold_outputs(csv_path=settings['i'], home_path=settings['d'], output_path=settings['o'])

if __name__ == '__main__':
    main()
