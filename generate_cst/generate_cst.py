#!/usr/local/miniconda/bin/python
import argparse
import extract_ligand_binding_sites
import rosetta_standard_match
import pyrosetta

import os
def main():
    pyrosetta.init()
    
    parser = argparse.ArgumentParser(description='Generate cst from PDB files')

    parser.add_argument('-i', '--input', required=True, help='Input PDB file path')
    parser.add_argument('-o', '--output', required=True, help='Output binding site directory')
    args = parser.parse_args()

    
    
    bindingsite_path = os.path.join(args.output, "binding_site")  
    extract_ligand_binding_sites.get_cst(args.input, bindingsite_path)
    for file in os.listdir(bindingsite_path):
        print(file)
        if file.endswith(".pdb.gz"):
            pdb_file_path = os.path.join(bindingsite_path, file)
            output_file=os.path.join(args.output,file.split(".")[0]+".cst")
            rosetta_standard_match.translate_binding_site(pdb_file_path, output_file)    
            print(f"file {pdb_file_path} is processing")
 
if __name__ == '__main__':
    main()
