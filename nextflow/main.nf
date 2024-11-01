// Import processes from module
include {build_msa; build_msa as build_msa_fragparent; process_msa; colabfold; create_summary_csv; predict_peaks} from './modules'

// Declare syntax version
nextflow.enable.dsl=2

// Define workflow
workflow {
    build_msa(file(params.protein_query_seq), true)

    if (params.heteromeric_mode) {
        build_msa_fragparent(file(params.fragment_query_seq), build_msa.out.done)
        process_msa(
            build_msa_fragparent.out.a3m,
            params.fragment_ntermres_start,
            params.fragment_ntermres_final,
            params.fragment_length,
            build_msa.out.a3m,
            params.protein_nterm_res,
            params.protein_cterm_res,
            params.protein_copies
        ) | flatten | colabfold

        fragment_parent_name = file(params.fragment_query_seq).baseName
    } else {
        process_msa(
            build_msa.out.a3m,
            params.fragment_ntermres_start,
            params.fragment_ntermres_final,
            params.fragment_length,
            build_msa.out.a3m,
            params.protein_nterm_res,
            params.protein_cterm_res,
            params.protein_copies
        ) | flatten | colabfold

        fragment_parent_name = file(params.protein_query_seq).baseName
    }

    protein_name = file(params.protein_query_seq).baseName

    create_summary_csv(
        colabfold.out.log | collect,
        colabfold.out.pdb | collect,
        protein_name,
        fragment_parent_name,
        params.job_name
    )

    predict_peaks(
        create_summary_csv.out.csv,
        params.job_name,
        params.n_contacts,
        params.n_weighted_contacts,
        params.iptm,
        params.contact_distance,
        params.cluster_peaks_frac_overlap
    )
}
