
// Define each process
process build_msa {
    label 'cpu_network'

    input:
        path query_seq
        val ready
    
    output:
        path 'mmseqs2_a3m/*.a3m', emit: a3m
        val true, emit: done

    shell:
    '''
    export PATH="!{colabfold_dir}/bin:$PATH"
    python !{repo_dir}/scripts/mmseqs2.py --query !{query_seq}
    '''
}

process process_msa {
    label 'cpu'

    input:
        path a3m
        val fragment_ntermres_start
        val fragment_ntermres_final
        val fragment_length
        val protein_a3m_input
        val protein_ntermres
        val protein_ctermres
        val protein_copies

    output:
        path '*/*.a3m'

    shell:
    '''
    python !{repo_dir}/fragfold/create_fragment_msa.py \
        --fragment_a3m_input !{a3m} \
        --fragment_ntermres_start !{fragment_ntermres_start} \
        --fragment_ntermres_final !{fragment_ntermres_final}  \
        --fragment_length !{fragment_length} \
        --protein_a3m_input !{protein_a3m_input} \
        --protein_ntermres !{protein_ntermres} \
        --protein_ctermres !{protein_ctermres} \
        --protein_copies !{protein_copies}
    '''
}

process colabfold {
    label 'cpu'

    input:
        path a3m_concat

    output:
        path 'data/log.txt', emit: log
        path 'data/*_unrelaxed_rank_00?_*.pdb', emit: pdb
        
    shell:
    '''
    export PATH="!{colabfold_dir}/bin:$PATH"
    colabfold_batch !{a3m_concat} data \
        --data !{alphafold_params_dir} \
        --model-type !{model_type} \
        --pair-mode !{pair_mode}
    '''
}

process create_summary_csv {
    label 'cpu'
    publishDir '.', saveAs: { csv -> "$csv" } 

    input:
        path 'log_file_*.txt'
        path pdb_file
        val protein_name
        val fragment_parent_name

    output:
        path '*.csv'

    shell:
    '''
    python !{repo_dir}/fragfold/colabfold_process_output.py 
        --predicted_pdbs !{pdb_file} 
        --confidence_logs log_file_*.txt 
        --full_protein !{protein_name}
        --fragment_protein !{fragment_parent_name}
    '''
}
