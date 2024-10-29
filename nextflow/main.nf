// Import processes from module
include {build_msa; build_msa as build_msa_fragparent; process_msa; colabfold; create_summary_csv; predict_peaks} from './modules'

// Declare syntax version
nextflow.enable.dsl=2

// Define workflow
workflow {
    if (params.heteromeric_mode) {
        // Serial execution of MSA building is necessary for our HPC environment
        build_msa(file(params.protein_query_seq),true)
        build_msa_fragparent(file(params.fragment_query_seq),build_msa.out.done)
        // output of process msa is some a3m files that are created (slices of the MSA); it gets piped to flatten and then to colabfold
        process_msa(build_msa_fragparent.out.a3m,
            params.fragment_ntermres_start,
            params.fragment_ntermres_final,
            params.fragment_length,
            build_msa.out.a3m,
            params.protein_nterm_res,
            params.protein_cterm_res,
            params.protein_copies)
            | flatten
            | colabfold
        protein_name = file(params.protein_query_seq).baseName
        fragment_parent_name = file(params.fragment_query_seq).baseName
        create_summary_csv(colabfold.out.log | collect , 
                        colabfold.out.pdb | collect ,
                        protein_name,
                        fragment_parent_name,
                        params.job_name)
        predict_peaks(create_summary_csv.out.csv,
                      params.job_name,
                      params.n_contacts,
                      params.n_weighted_contacts,
                      params.iptm,
                      params.contact_distance,
                      params.cluster_peaks_frac_overlap)
    } else {
        build_msa(file(params.protein_query_seq),true)
        process_msa(build_msa.out.a3m,
                params.fragment_ntermres_start,
                params.fragment_ntermres_final,
                params.fragment_length,
                build_msa.out.a3m,
                params.protein_nterm_res,
                params.protein_cterm_res,
                params.protein_copies)
            | flatten
            | colabfold
        protein_name = file(params.protein_query_seq).baseName
        create_summary_csv(colabfold.out.log | collect ,
                           colabfold.out.pdb | collect , 
                           protein_name,
                           protein_name,
                           /* params.experimental_data, */
                           params.job_name)
        predict_peaks(create_summary_csv.out.csv,
                      params.job_name,
                      params.n_contacts,
                      params.n_weighted_contacts,
                      params.iptm,
                      params.contact_distance,
                      params.cluster_peaks_frac_overlap)
    }
}
// params.experimental_data,
